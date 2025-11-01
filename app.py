import os
import sys
import threading
import logging
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

from data_source import DataSource
from mqtt_manager import MqttManager
from config_manager import ConfigManager

# --- Logging Setup ---
"See mock-energy-meter.service for logging targets"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(module)s:%(funcName)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout  # log to console, systemd captures it
)
logger = logging.getLogger("EnergyMeter")

# --- Flask + SocketIO Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.logger.handlers = logger.handlers
app.logger.setLevel(logger.level)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    logger=False,
    engineio_logger=False
)

# --- Constants ---
DEFAULT_CERT_DIR = "certs"

# --- Utilities ---
publish_and_emit_lock = threading.Lock()


def safe_emit(event, data):
    """Emit safely to SocketIO clients; ignore minor failures."""
    try:
        socketio.emit(event, data)
    except Exception:
        logger.exception("❌ Failed to emit message to clients")


def get_config_template_vars(cfg):
    """Prepare config values for template rendering."""
    return {
        "consumed_lower": cfg.get("interval_consumed_lower", 2.0),
        "consumed_upper": cfg.get("interval_consumed_upper", 5.0),
        "generated_lower": cfg.get("interval_generated_lower", 2.0),
        "generated_upper": cfg.get("interval_generated_upper", 5.0),
        "mqtt_publish_enabled": cfg.get("mqtt_publish_enabled", True),
        "mqtt_host": cfg.get("mqtt_host", ""),
        "mqtt_port": cfg.get("mqtt_port", 8883),
        "mqtt_username": cfg.get("mqtt_username", ""),
        "mqtt_password": cfg.get("mqtt_password", ""),
        "mqtt_cert_filename": cfg.get("mqtt_cert_filename", "")
    }


# --- Initialization ---
def init_config():
    """Initialize ConfigManager and return current config."""
    cfg_mgr = ConfigManager()
    return cfg_mgr, cfg_mgr.all()


def init_mqtt(cfg):
    """Initialize MQTT manager with current config."""
    return MqttManager(config=cfg)


def init_data_sources(cfg, callback):
    """Create consumer and generator DataSource instances."""
    consumer = DataSource(
        name="Load",
        interval_lower_bound=cfg["interval_consumed_lower"],
        interval_upper_bound=cfg["interval_consumed_upper"],
        callback=lambda data: callback({'consumed': data})
    )
    generator = DataSource(
        name="Generator",
        interval_lower_bound=cfg["interval_generated_lower"],
        interval_upper_bound=cfg["interval_generated_upper"],
        callback=lambda data: callback({'generated': data})
    )
    return consumer, generator


def apply_config(new_cfg, consumer, generator, mqtt_mgr):
    """Update intervals and restart MQTT client with new config."""
    try:
        logger.info("🔄 Applying new configuration...")
        consumer.interval_lower_bound = new_cfg["interval_consumed_lower"]
        consumer.interval_upper_bound = new_cfg["interval_consumed_upper"]
        generator.interval_lower_bound = new_cfg["interval_generated_lower"]
        generator.interval_upper_bound = new_cfg["interval_generated_upper"]

        mqtt_mgr.stopClient()
        mqtt_mgr.config = new_cfg
        mqtt_mgr.startClient()
    except Exception:
        logger.exception("❌ Error applying configuration")


def apply_action(action: str, consumer, generator, source: str = "UI/MQTT"):
    """Pause/resume sources and notify UI."""
    action_upper = action.upper()
    if action_upper == "RESUME":
        consumer.resume()
        generator.resume()
        logger.info(f"ℹ️ Action '{action_upper}' executed from {source}")
    elif action_upper == "PAUSE":
        consumer.pause()
        generator.pause()
        logger.info(f"ℹ️ Action '{action_upper}' executed from {source}")
    else:
        logger.warning(f"⚠️ Unknown action '{action}' from {source}")
        return

    safe_emit("mqtt_message", {"message": f"Action: {action_upper} ({source})"})


# --- Main Application ---
def main():
    # Initialize config
    config_manager, config = init_config()
    mqtt_manager = init_mqtt(config)

    # Callback for publishing data
    def publish_callback(payload):
        with publish_and_emit_lock:
            mqtt_manager.safePublish(payload)
            safe_emit("meter_reading", payload)

    # Start data sources
    energy_consumer, energy_generator = init_data_sources(config, publish_callback)
    energy_consumer.start()
    energy_generator.start()

    # MQTT message handling
    mqtt_manager.message_callback = lambda payload: apply_action(
        payload, consumer=energy_consumer, generator=energy_generator, source="MQTT"
    )
    mqtt_manager.startClient()

    # Config change hook
    config_manager.on_change(lambda new_cfg: apply_config(
        new_cfg, energy_consumer, energy_generator, mqtt_manager
    ))

    # --- Flask routes ---
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/configuration", methods=["GET", "POST"])
    def configuration():
        if request.method == "GET":
            return render_template("configuration.html", **get_config_template_vars(config_manager.all()))

        uploaded_cert = request.files.get("mqtt_cert")
        cert_filename = None
        if uploaded_cert:
            try:
                cert_filename = config_manager.save_cert_file(uploaded_cert, cert_dir=DEFAULT_CERT_DIR)
            except Exception:
                logger.warning("⚠️ Could not save uploaded certificate; keeping previous one.")

        new_config = {
            "interval_consumed_lower": request.form.get("consumed_lower", type=float),
            "interval_consumed_upper": request.form.get("consumed_upper", type=float),
            "interval_generated_lower": request.form.get("generated_lower", type=float),
            "interval_generated_upper": request.form.get("generated_upper", type=float),
            "mqtt_publish_enabled": request.form.get("mqtt_publish_enabled", "false").lower() == "true",
            "mqtt_host": request.form.get("mqtt_host"),
            "mqtt_port": request.form.get("mqtt_port", type=int),
            "mqtt_username": request.form.get("mqtt_username"),
            "mqtt_password": request.form.get("mqtt_password"),
            "mqtt_cert_filename": cert_filename or config_manager.get("mqtt_cert_filename", "")
        }

        config_manager.update(new_config)
        logger.info("✅ Configuration updated successfully")
        return jsonify({"message": "✅ Configuration updated successfully!"})

    @app.route("/mqtt_status")
    def mqtt_status():
        connected = mqtt_manager.isConnected()
        logger.info(f"MQTT connection status: {connected}")
        return jsonify({"connected": connected})

    # --- SocketIO events ---
    @socketio.on("control_action")
    def handle_control_action(data):
        action = data.get("action")
        apply_action(action, consumer=energy_consumer, generator=energy_generator, source="UI")

    # Start server
    logger.info("🚀 Starting Flask + SocketIO server...")
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()