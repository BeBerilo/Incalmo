#!/bin/bash

# This script packages the Python backend using PyInstaller for inclusion in the macOS app

# Exit on error
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$ROOT_DIR/../src/backend"
VENV_DIR="$ROOT_DIR/backend_venv"
DIST_DIR="$ROOT_DIR/backend_dist"

# Ensure virtual environment is activated
source "$VENV_DIR/bin/activate"

# Install PyInstaller if not already installed
pip install pyinstaller

echo "Packaging Python backend with PyInstaller..."
cd "$BACKEND_DIR"

# Create spec file for PyInstaller
cat > incalmo_backend.spec << EOF
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['$BACKEND_DIR'],
    binaries=[],
    datas=[],
    hiddenimports=['uvicorn.logging', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='incalmo_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='incalmo_backend',
)
EOF

# Run PyInstaller
pyinstaller incalmo_backend.spec

# Copy the dist directory to the app directory
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"
cp -r dist/incalmo_backend/* "$DIST_DIR"

echo "Python backend packaged successfully at $DIST_DIR"
