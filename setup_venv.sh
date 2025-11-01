#!/usr/bin/env bash
set -e

# Minimum required Python version
REQUIRED_MAJOR=3
REQUIRED_MINOR=9

VENV_DIR="./venv"
FREEZE_FILE="requirements‑freeze.txt"

echo "🛠️  Setting up virtual environment..."

# Check if python3 is available and version is correct
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 is not installed. Please install Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR}+"
  exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; v=sys.version_info; print(f"{v.major}.{v.minor}")')
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt "$REQUIRED_MAJOR" ] || { [ "$PY_MAJOR" -eq "$REQUIRED_MAJOR" ] && [ "$PY_MINOR" -lt "$REQUIRED_MINOR" ]; }; then
  echo "❌ Python version ${PYTHON_VERSION} detected. Require Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR} or higher."
  exit 1
fi

echo "✅ Python version ${PYTHON_VERSION} is acceptable."

# Create the virtualenv if not exists
if [ ! -d "$VENV_DIR" ]; then
  echo "🔧 Creating virtual environment at ${VENV_DIR} …"
  python3 -m venv "$VENV_DIR"
  echo "✅ Virtual environment created."
fi

# Activate it
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
echo "🔄 Activated virtual environment: ${VENV_DIR}"

# Upgrade pip & install dependencies
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed."

# Freeze installed packages
pip freeze > "$FREEZE_FILE"
echo "📦 Installed package versions have been saved to ${FREEZE_FILE}"

echo "🎉 Virtual environment setup complete. You’re good to go!"
