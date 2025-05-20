#!/bin/bash

# Setup script for Incalmo
# Creates Python virtual environment and installs all requirements
# Also installs Node dependencies for the Electron frontend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/src/backend"
FRONTEND_DIR="$SCRIPT_DIR/macos-app"

# Detect platform to select requirements file
REQ_FILE="$BACKEND_DIR/requirements.txt"
if [[ "$(uname)" == "Darwin" ]]; then
    if [[ -f "$SCRIPT_DIR/requirements_macos.txt" ]]; then
        REQ_FILE="$SCRIPT_DIR/requirements_macos.txt"
    elif [[ -f "$BACKEND_DIR/requirements_macos.txt" ]]; then
        REQ_FILE="$BACKEND_DIR/requirements_macos.txt"
    fi
fi

echo "Using Python requirements from $REQ_FILE"

# Check python and pip
if ! command -v python3 >/dev/null; then
  echo "Python3 is required but not installed" >&2
  exit 1
fi

# Create virtual environment
VENV_DIR="$BACKEND_DIR/venv"
if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -r "$REQ_FILE"

deactivate

echo "Python environment set up at $VENV_DIR"

# Install Node dependencies
if command -v npm >/dev/null; then
  echo "Installing Node dependencies in $FRONTEND_DIR"
  (cd "$FRONTEND_DIR" && npm install)
else
  echo "npm not found - skipping Node dependency installation" >&2
fi

echo "Setup complete"
