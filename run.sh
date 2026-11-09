#!/bin/bash
set -e

cd "$(dirname "$0")"

# Create or recreate .venv if it doesn't exist or is broken
if [ ! -d ".venv" ] || ! .venv/bin/pip --version >/dev/null 2>&1; then
    echo "Creating .venv..."
    rm -rf .venv
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    python -m pip install -r requirements.txt
fi

# Run the server
echo "Starting app.py..."
python app.py
