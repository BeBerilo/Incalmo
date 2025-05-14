#!/bin/bash

# This script builds the macOS application package

# Exit on error
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Create app icon
echo "Creating app icon..."
node "$SCRIPT_DIR/create_icon.js"

# Copy backend files from the original project
echo "Copying backend files..."
mkdir -p "$ROOT_DIR/../src/backend"
cp -r "$ROOT_DIR/../src/backend" "$ROOT_DIR/../src/"

# Prepare Python environment
echo "Preparing Python environment..."
"$SCRIPT_DIR/prepare_python_env.sh"

# Package backend
echo "Packaging backend..."
"$SCRIPT_DIR/package_backend.sh"

# Build macOS app
echo "Building macOS app..."
cd "$ROOT_DIR"
npm run build

echo "Build completed successfully!"
echo "The macOS application package can be found in the dist directory."
