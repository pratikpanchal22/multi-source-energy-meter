import os
import ssl
import json
import threading
import logging
import traceback
import paho.mqtt.client as mqtt

DEFAULT_CERT_DIR = "certs"
PUB_TOPIC = "mock/energy_meter/id001/data"
SUB_TOPIC = "mock/energy_meter/id001/control"

class MqttManager:
    """
    MQTT client wrapper with TLS support, credentials, safe publish, and logging.
    """

    def __init__(self, config=None, message_callback=None):
        """
        :param config: configuration dictionary
        :param message_callback: function called with incoming messages
        """
        self.config = config or {}
        self.message_callback = message_callback
        self._logger = logging.getLogger()
        self._lock = threading.RLock()
        self.mqtt_client = None

    def startClient(self):
        """Start MQTT client with TLS, credentials, and subscriptions."""
        with self._lock:
            self.stopClient()  # Clean up any previous client

            host = self.config.get("mqtt_host")
            port = self.config.get("mqtt_port", 8883)
            if not host:
                self._logger.warning("⚠️ MQTT host not configured. Skipping MQTT startup.")
                return None

            client_id = f"mock-meter-{os.urandom(4).hex()}"
            client = mqtt.Client(client_id=client_id, clean_session=True)
            client.enable_logger()
            client.reconnect_delay_set(min_delay=1, max_delay=2)
            client.max_inflight_messages_set(20)

            # Set username/password if provided
            username = self.config.get("mqtt_username")
            password = self.config.get("mqtt_password")
            if username or password:
                client.username_pw_set(username or "", password or "")

            # TLS setup
            cert_filename = self.config.get("mqtt_cert_filename") or ""
            cert_path = os.path.join(DEFAULT_CERT_DIR, cert_filename)
            if cert_filename and os.path.exists(cert_path):
                try:
                    client.tls_set(
                        ca_certs=cert_path,
                        certfile=None,
                        keyfile=None,
                        cert_reqs=ssl.CERT_REQUIRED,
                        tls_version=ssl.PROTOCOL_TLS,
                    )
                    client.tls_insecure_set(True)
                    self._logger.info("🔐 TLS enabled using cert: %s", cert_path)
                except Exception:
                    self._logger.exception("❌ Failed to set TLS")
            else:
                self._logger.info("ℹ️ No MQTT certificate found. Connecting without TLS.")

            # Assign MQTT event handlers
            client.on_connect = self._on_connect
            client.on_disconnect = self._on_disconnect
            client.on_message = self._on_message
            client.on_log = lambda c, u, l, b: self._logger.debug("📝 MQTT LOG: %s", b)

            # Connect
            try:
                client.connect(host, int(port), 60)
                client.loop_start()
                self.mqtt_client = client
                self._logger.info("✅ Connected to MQTT broker %s:%s (Client ID: %s)", host, port, client_id)
            except Exception:
                self._logger.exception("❌ MQTT connection failed")
                self.mqtt_client = None

            return self.mqtt_client

    def stopClient(self):
        """Stop and clean up any existing client."""
        with self._lock:
            try:
                if self.mqtt_client:
                    self.mqtt_client.loop_stop()
                    self.mqtt_client.disconnect()
                    self._logger.info("🛑 MQTT client stopped.")
            except Exception:
                self._logger.exception("⚠️ MQTT stop failed")
            finally:
                self.mqtt_client = None

    def safePublish(self, payload):
        """Safely publish JSON or text payload if connected."""
        if not self.config.get("mqtt_publish_enabled", False):
            return
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            self._logger.warning("⚠️ MQTT client is null or not connected")
            return
        try:
            mqtt_payload = (
                json.dumps(payload).encode("utf-8")
                if isinstance(payload, dict)
                else str(payload).encode("utf-8")
            )
            self._logger.info(f"🚀 MQTT Outbound: {mqtt_payload}")
            self.mqtt_client.publish(PUB_TOPIC, mqtt_payload)
        except Exception:
            self._logger.exception("💣 MQTT publish error")

    def isConnected(self):
        """Check connection state."""
        return self.mqtt_client and self.mqtt_client.is_connected()

    # --- MQTT Event Handlers ---
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._logger.info("✅ Connected to MQTT broker.")
            client.subscribe(SUB_TOPIC)
        else:
            self._logger.warning("❌ MQTT connect failed: rc=%s", rc)

    def _on_disconnect(self, client, userdata, rc):
        self._logger.warning("⚠️ MQTT disconnected (rc=%s)", rc)

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        self._logger.info("📩 MQTT Received: %s", payload)
        if self.message_callback:
            try:
                self.message_callback(payload)
            except Exception:
                self._logger.exception("💥 Message callback error")