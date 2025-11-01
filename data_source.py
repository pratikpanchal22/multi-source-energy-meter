import random
import threading
import time
import socket
from datetime import datetime
import logging
import traceback


class DataSource:
    """
    Simulates a mock energy meter that generates voltage, current, and power readings.
    """

    def __init__(self, name="Generic DS", interval_lower_bound=2, interval_upper_bound=2, callback=None):
        """
        :param interval_lower_bound: Minimum sleep interval between readings (seconds)
        :param interval_upper_bound: Maximum sleep interval between readings (seconds)
        :param callback: Function called with each new reading
        """
        self.name = name
        self.timestamp = None
        self.voltage = 0.0
        self.current = 0.0
        self.power = 0.0
        self.ipAddr = self._get_ip_address()
        self.interval_lower_bound = interval_lower_bound
        self.interval_upper_bound = interval_upper_bound
        self.running = True
        self.callback = callback
        self._logger = logging.getLogger()
        self._thread_started = False

    def _get_ip_address(self):
        """Retrieve the local IP address of the device."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            self._logger.warning("⚠️ Failed to get local IP, defaulting to 127.0.0.1")
            return "127.0.0.1"

    def generate_readings(self):
        """Simulate realistic voltage, current, and power readings."""
        self.voltage = round(random.uniform(210, 240), 2)
        self.current = round(random.uniform(0.1, 10.0), 2)
        self.power = round(self.voltage * self.current, 2)
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._logger.info(
            f"[{self.name}] Reading: "
            f"V={self.voltage}V, I={self.current}A, P={self.power}W at {self.timestamp}"
        )

    def start(self):
        """Start the thread only once."""
        if not self._thread_started:
            thread = threading.Thread(target=self._run, daemon=True, name=f"{self.name}-Thread")
            thread.start()
            self._thread_started = True
            self._logger.info("✅ [%s] DataSource thread started.", self.name)
        else:
            self._logger.warning("⚠️ [%s] DataSource thread already started.", self.name)


    def pause(self):
        """Pause readings without stopping the thread."""
        self.running = False
        self._logger.info("⏸️ [%s] DataSource paused.", self.name)


    def resume(self):
        """Resume readings."""
        self.running = True
        self._logger.info("▶️ [%s] DataSource resumed.", self.name)


    def stop(self):
        """Stop the data generation loop."""
        self.running = False
        self._logger.info("🛑 [%s] DataSource stopped.", self.name)


    def _run(self):
        """Main loop for generating readings at random intervals."""
        while True:
            try:
                if self.running:
                    self.generate_readings()
                    if self.callback:
                        try:
                            self.callback({
                                "voltage": self.voltage,
                                "current": self.current,
                                "power": self.power,
                                "ipAddr": self.ipAddr,
                                "timestamp": self.timestamp
                            })
                        except Exception:
                            self._logger.exception("⚠️ [%s] Callback error", self.name)

                sleep_time = random.uniform(self.interval_lower_bound, self.interval_upper_bound)
                current_thread = threading.current_thread()
                self._logger.debug(
                    "[%s] Thread ID: %s, Name: %s, sleeping for %.2fs",
                    self.name, current_thread.ident, current_thread.name, sleep_time
                )
                time.sleep(sleep_time)
            except Exception:
                self._logger.exception("❌ [%s] DataSource error", self.name)