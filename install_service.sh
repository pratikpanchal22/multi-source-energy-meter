#!/usr/bin/env bash
set -e

SERVICE_NAME="multi-source-energy-meter"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo
echo "=== 🛠 Installing ${SERVICE_NAME} systemd service ==="
echo

# Prompt for project directory and run-user
read -rp "Enter the full path to your project directory (e.g. /home/you/multi-source-energy-meter): " PROJECT_DIR
if [ ! -d "$PROJECT_DIR" ]; then
  echo "❌ Directory does not exist: $PROJECT_DIR"
  exit 1
fi

read -rp "Enter the user to run the service as (e.g. youruser): " RUN_USER
if ! id "$RUN_USER" >/dev/null 2>&1; then
  echo "⚠️ User '$RUN_USER' does not exist; service may not start correctly."
fi

echo
echo "Creating systemd unit file at ${SERVICE_FILE}"
sudo tee "${SERVICE_FILE}" > /dev/null <<EOF
[Unit]
Description=Mock Energy Meter Flask App
After=network.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/python3 ${PROJECT_DIR}/app.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo chmod 644 "${SERVICE_FILE}"

echo
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling service ${SERVICE_NAME}.service"
sudo systemctl enable ${SERVICE_NAME}.service

echo "Starting service ${SERVICE_NAME}.service"
sudo systemctl start  ${SERVICE_NAME}.service

echo
echo "✅ Service installed and started."
echo "Use the following to check status and logs:"
echo "  sudo systemctl status ${SERVICE_NAME}.service"
echo "  sudo journalctl --unit=${SERVICE_NAME}.service -f"
echo