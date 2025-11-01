import os
import json
import threading
import traceback
import logging

# --- Constants ---
DEFAULT_CERT_DIR = "certs"

class ConfigManager:
    DEFAULT_CONFIG = {
        "interval_consumed_lower": 2.0,
        "interval_consumed_upper": 5.0,
        "interval_generated_lower": 2.0,
        "interval_generated_upper": 5.0,
        "mqtt_publish_enabled": False,
        "mqtt_host": None,
        "mqtt_port": 1883,
        "mqtt_username": None,
        "mqtt_password": None,
        "mqtt_cert_filename": None,
    }

    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self._lock = threading.RLock()
        self._config = None
        self._listeners = []
        self._logger = logging.getLogger()
        self.load()

    def load(self):
        """Load config from file or create default if missing."""
        with self._lock:
            if not os.path.exists(self.config_file):
                self._config = self.DEFAULT_CONFIG.copy()
                self.save()
            else:
                try:
                    with open(self.config_file, "r") as f:
                        self._config = json.load(f)
                except Exception:
                    self._logger.warning(
                        "⚠️ Failed to read config, using defaults:\n%s", traceback.format_exc()
                    )
                    self._config = self.DEFAULT_CONFIG.copy()
                    self.save()
        return self._config

    def save(self):
        """Save current config to file."""
        with self._lock:
            try:
                self._logger.info("💾 Attempting to save config...")
                with open(self.config_file, "w") as f:
                    json.dump(self._config, f, indent=4)
                self._logger.info("✅ Config saved successfully.")
            except Exception:
                self._logger.exception("❌ Failed to save config")

    def save_cert_file(self, cert_file, cert_dir=DEFAULT_CERT_DIR):
        """
        Save an uploaded certificate file and update config with its filename.
        :param cert_file: werkzeug FileStorage object
        :param cert_dir: directory to save the cert
        :return: filename of saved cert or None
        """
        if not cert_file or not cert_file.filename.endswith(".crt"):
            return self.get("mqtt_cert_filename", None)

        os.makedirs(cert_dir, exist_ok=True)
        cert_path = os.path.join(cert_dir, cert_file.filename)
        try:
            cert_file.save(cert_path)
            self.update({"mqtt_cert_filename": cert_file.filename})
            self._logger.info("✅ Certificate saved: %s", cert_path)
            return cert_file.filename
        except Exception:
            self._logger.exception("❌ Failed to save certificate")
            return self.get("mqtt_cert_filename", None)

    def get(self, key, default=None):
        with self._lock:
            return self._config.get(key, default)

    def all(self):
        with self._lock:
            return self._config.copy()

    def update(self, updates: dict):
        with self._lock:
            self._config.update(updates)
            self.save()

        # Notify listeners outside the lock
        for listener in self._listeners:
            try:
                listener(self._config)
            except Exception as e:
                self._logger.warning("⚠️ Config listener error: %s", e)

    def on_change(self, callback):
        if callable(callback):
            self._listeners.append(callback)