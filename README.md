# Clone repo
git clone https://github.com/yourusername/multi-source-energy-meter.git
cd multi-source-energy-meter

# Setup virtual environment
./setup_venv.sh

# Start the service (assuming service file is placed)
sudo systemctl daemon-reload
sudo systemctl enable mock-energy-meter.service
sudo systemctl start mock-energy-meter.service
