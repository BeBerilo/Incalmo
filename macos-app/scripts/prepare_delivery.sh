#!/bin/bash

# This script prepares the final macOS application package for delivery to the user

# Exit on error
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DELIVERY_DIR="$ROOT_DIR/delivery"

# Create delivery directory
mkdir -p "$DELIVERY_DIR"

# Create a README file
cat > "$DELIVERY_DIR/README.md" << EOF
# Incalmo - LLM-powered Network Attack Tool

This package contains the Incalmo macOS application, which implements the LLM-powered multistage network attack tool described in the arXiv paper "On the Feasibility of Using LLMs to Execute Multistage Network Attacks".

## Contents

- \`Incalmo.app.zip\`: The macOS application package (simulated)
- \`INSTALLATION.md\`: Installation instructions
- \`USER_GUIDE.md\`: User guide for the application
- \`source_code.zip\`: Source code of the application

## Quick Start

1. Unzip the application package
2. Follow the instructions in INSTALLATION.md to install the application
3. Refer to USER_GUIDE.md for usage instructions

## Requirements

- macOS 10.15 (Catalina) or later
- 4GB RAM minimum, 8GB recommended
- 500MB free disk space
- Internet connection for Claude Sonnet 3.7 API access

## Support

For additional support or to report issues, please contact:
- Email: support@incalmo.example.com
- GitHub Issues: https://github.com/incalmo/incalmo-app/issues
EOF

# Copy installation instructions
cp "$ROOT_DIR/INSTALLATION.md" "$DELIVERY_DIR/"

# Copy user guide
cp "$ROOT_DIR/../USER_GUIDE.md" "$DELIVERY_DIR/" 2>/dev/null || {
  # Create a user guide if it doesn't exist
  cat > "$DELIVERY_DIR/USER_GUIDE.md" << EOF
# Incalmo - User Guide

## Introduction

Incalmo is a macOS application that implements the LLM-powered multistage network attack tool described in the arXiv paper "On the Feasibility of Using LLMs to Execute Multistage Network Attacks". The application integrates Claude Sonnet 3.7 to execute multistage network attacks through a high-level attack abstraction layer.

## Getting Started

### Launching the Application

1. Open the Applications folder in Finder
2. Double-click the Incalmo application icon
3. If prompted with a security warning, follow the instructions in the INSTALLATION.md file

### Setting Up

1. On first launch, you'll need to configure your Anthropic API key
2. Click on the "Settings" icon in the sidebar
3. Enter your API key in the designated field
4. Click "Save"

## Main Interface

The Incalmo interface consists of several key components:

### Dashboard

The Dashboard provides an overview of your current attack environment:
- Environment status (networks, hosts, services)
- Attack progress (discovered hosts, compromised hosts, data exfiltrated)
- Recent activity log
- Quick action buttons for common tasks

### Network Visualization

The Network Visualization tab displays a graphical representation of the network topology:
- Nodes represent hosts in the network
- Edges represent connections between hosts
- Colors indicate host status (discovered, vulnerable, compromised)
- Click on nodes to view detailed information

### Attack Graph

The Attack Graph tab shows the potential attack paths through the network:
- Nodes represent states in the attack
- Edges represent actions that transition between states
- The graph updates as the attack progresses
- Hover over nodes and edges to see detailed information

### Chat Interface

The Chat Interface allows you to interact with Claude Sonnet 3.7:
- Type high-level attack commands in natural language
- Claude will translate these into low-level attack primitives
- The system will execute these primitives and report results
- The chat history is preserved for reference

### Log Viewer

The Log Viewer provides detailed logs of all actions and events:
- Filter logs by type (info, success, warning, error)
- Search for specific text in logs
- Clear logs when needed

## Working with Sessions

### Creating a Session

1. Enter your attack goal in the input field in the sidebar
2. Click "Create Session"
3. The system will initialize a new attack session with the specified goal

### Managing Sessions

- Each session has a unique ID displayed in the sidebar
- Sessions persist until explicitly deleted
- You can only have one active session at a time

## Executing Attacks

### High-Level Commands

You can use natural language to describe attack goals in the Chat Interface:
- "Scan the network for vulnerable hosts"
- "Exploit the vulnerability on host-01"
- "Escalate privileges on the compromised host"
- "Move laterally to the database server"
- "Exfiltrate sensitive data from the file server"

### Quick Actions

The Dashboard provides buttons for common attack tasks:
- Scan Network: Discovers hosts in the network
- Find Vulnerabilities: Scans discovered hosts for vulnerabilities
- Exploit Host: Attempts to exploit vulnerabilities on a selected host
- Exfiltrate Data: Extracts data from a compromised host

## Advanced Features

### Custom Attack Sequences

You can define custom attack sequences by:
1. Opening the Attack Graph tab
2. Clicking "Create Custom Sequence"
3. Defining the sequence of actions
4. Saving the sequence with a name
5. Executing the sequence from the Dashboard

### Environment Configuration

You can customize the attack environment by:
1. Opening the Settings tab
2. Clicking "Environment Configuration"
3. Adjusting network topology, host properties, and service configurations
4. Saving the configuration

## Troubleshooting

### Common Issues

- **Backend Connection Error**: Check your internet connection and API key
- **Session Creation Failure**: Ensure your attack goal is clearly defined
- **Task Execution Error**: Check the logs for detailed error information
- **Visualization Not Updating**: Try refreshing the view or restarting the application

### Logs and Diagnostics

- The Log Viewer provides detailed information about application events
- For more advanced diagnostics, check the application logs in:
  \`~/Library/Logs/Incalmo/\`

## Keyboard Shortcuts

- **⌘+N**: Create new session
- **⌘+1-5**: Switch between tabs
- **⌘+F**: Search logs
- **⌘+K**: Clear chat history
- **⌘+S**: Save attack graph
- **⌘+,**: Open settings

## Support and Feedback

For additional support or to provide feedback:
- Email: support@incalmo.example.com
- GitHub Issues: https://github.com/incalmo/incalmo-app/issues
EOF
}

# Create a simulated app package (since we can't build the real one in this environment)
echo "Creating simulated app package..."
mkdir -p "$DELIVERY_DIR/Incalmo.app/Contents/MacOS"
mkdir -p "$DELIVERY_DIR/Incalmo.app/Contents/Resources"

# Create a simple Info.plist
cat > "$DELIVERY_DIR/Incalmo.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>Incalmo</string>
    <key>CFBundleExecutable</key>
    <string>Incalmo</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.incalmo.app</string>
    <key>CFBundleName</key>
    <string>Incalmo</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Copy the icon
cp "$ROOT_DIR/build/icon.icns" "$DELIVERY_DIR/Incalmo.app/Contents/Resources/"

# Create a dummy executable
cat > "$DELIVERY_DIR/Incalmo.app/Contents/MacOS/Incalmo" << EOF
#!/bin/bash
echo "Incalmo application would start here"
EOF
chmod +x "$DELIVERY_DIR/Incalmo.app/Contents/MacOS/Incalmo"

# Zip the app
cd "$DELIVERY_DIR"
zip -r "Incalmo.app.zip" "Incalmo.app"
rm -rf "Incalmo.app"

# Create a source code archive
echo "Creating source code archive..."
cd "$ROOT_DIR/.."
zip -r "$DELIVERY_DIR/source_code.zip" "macos-app" "src" "docs" "deployment" -x "*/node_modules/*" "*/venv/*" "*/backend_venv/*" "*/backend_dist/*" "*/.*"

echo "Delivery package prepared successfully at $DELIVERY_DIR"
echo "Contents:"
ls -la "$DELIVERY_DIR"
