# Multi‑Source Energy Meter (Mock)

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg?logo=python)](https://www.python.org/) [![Flask](https://img.shields.io/badge/Flask-Web%20Framework-orange.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/) [![MQTT](https://img.shields.io/badge/MQTT-Pub/Sub-green.svg?logo=mqtt&logoColor=white)](https://mqtt.org/) [![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript) [![WebSocket (Socket.IO)](https://img.shields.io/badge/WebSocket-Socket.IO-010101?logo=socket.io&logoColor=white)](https://socket.io/) [![License: GPL v3](https://img.shields.io/badge/License‑GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) 

_A Python‑Flask prototype demo app with asynchronous, callback‑based multiple data‑source threads (hardware emulation). Emits data via WebSocket and MQTT._

 
## 🚀 Quick Start
```bash

git clone https://github.com/pratikpanchal22/multi-source-energy-meter.git
cd multi-source-energy-meter
source setup_venv.sh
python3 app.py
```

Then open **http://localhost:5000** in your browser.

## Getting Started – Development Environment Setup

Prerequisites

- **Python 3.9+**
- `python3-venv` for virtual environment management
- `systemd` (Linux only) if you plan to run it as a background service
- `sudo` access (required for installing system services)

### Installation

```bash

# Clone the repo
git  clone  https://github.com/pratikpanchal22/multi-source-energy-meter.git
cd  multi-source-energy-meter

# Setup virtual environment and install dependencies
chmod  +x  setup_venv.sh
./setup_venv.sh
```

### **Running as a Linux Service (Recommended)**

A helper script is provided to simplify service installation.

```bash
chmod +x install_service.sh
./install_service.sh
```

You’ll be prompted for:

-   The full project path (e.g. `/home/you/multi-source-energy-meter`)
-   The user account under which the service should run (e.g. `you`)
      

The script:
-   Creates a `/etc/systemd/system/multi-source-energy-meter.service` file dynamically
-   Reloads the daemon
-   Enables and starts the service automatically

### Managing the Service

```bash
# Check service status
sudo systemctl status multi-source-energy-meter.service

# Start or stop manually
sudo systemctl start multi-source-energy-meter.service
sudo systemctl stop multi-source-energy-meter.service

# View live logs
sudo journalctl -u multi-source-energy-meter.service -f
```

Access the app at: **`http://<ip-address>:5000`**


### Logs

Access logs:
```bash
sudo journalctl -u multi-source-energy-meter.service -f
```

#### **Configuring `journald` Log Size, Rotation, and Retention**

Systemd automatically manages logs via the **journal** service. To control log size and rotation behavior, edit:

```bash
sudo vi /etc/systemd/journald.conf
```

Modify or add these key options under [Journal]. Adjust the sizes to your system:
```ini
[Journal]
# Maximum disk space journald may use
SystemMaxUse=1024M

# Maximum size per individual journal file
SystemMaxFileSize=20M

# Whether to compress rotated logs (recommended)
Compress=yes
```

Then apply changes:
```bash
sudo systemctl restart systemd-journald
```

You can inspect current journal usage with:
```bash
sudo journalctl --disk-usage
```

To vacuum old logs manually:
```bash
# Keep only 50MB total
sudo journalctl --vacuum-size=50M

# Or keep only 14 days of logs
sudo journalctl --vacuum-time=14d
```

---
### **Architecture Notes**
-   The app runs Flask with asynchronous WebSocket broadcasting (via Socket.IO).
-   MQTT publishing is implemented for integration testing with brokers. You can configure your broker at `http://<ip-address>:5000/configuration`
-   Each data source runs in its own background thread, simulating multiple energy sensors.

### **Contributions and Usage**

Feel free to fork, improve, or adapt for your own IoT data-emulation projects.
Pull requests and suggestions are welcome!
