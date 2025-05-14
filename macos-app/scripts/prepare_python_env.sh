#!/bin/bash

# This script prepares the Python environment for packaging with the Electron app

# Exit on error
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$ROOT_DIR/../src/backend"
VENV_DIR="$ROOT_DIR/backend_venv"

echo "Creating Python virtual environment for packaging..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "Installing backend dependencies..."
pip install -r "$BACKEND_DIR/requirements.txt"

echo "Creating requirements file for PyInstaller..."
pip freeze > "$ROOT_DIR/backend_requirements.txt"

echo "Python environment prepared successfully!"
