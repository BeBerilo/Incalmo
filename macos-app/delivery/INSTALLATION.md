# Incalmo macOS Application - Installation Guide

## Overview

Incalmo is a macOS application that implements the LLM-powered multistage network attack tool described in the arXiv paper "On the Feasibility of Using LLMs to Execute Multistage Network Attacks". The application integrates Claude Sonnet 3.7 to execute multistage network attacks through a high-level attack abstraction layer.

## System Requirements

- macOS 10.15 (Catalina) or later
- 4GB RAM minimum, 8GB recommended
- 500MB free disk space
- Internet connection for Claude Sonnet 3.7 API access

## Installation Instructions

### Method 1: Using the DMG Installer (Recommended)

1. Download the `Incalmo.dmg` file from the provided link
2. Double-click the DMG file to mount it
3. Drag the Incalmo application to your Applications folder
4. Eject the DMG by right-clicking on it in Finder and selecting "Eject"
5. Open the Applications folder and double-click Incalmo to launch it

### Method 2: Manual Installation

If you received the `.app` file directly:

1. Download the `Incalmo.app` file
2. Move it to your Applications folder
3. Double-click Incalmo in the Applications folder to launch it

### First Launch Security Notice

When launching Incalmo for the first time, macOS may display a security warning because the application is from an unidentified developer. To open the application:

1. Right-click (or Control-click) on the Incalmo app icon
2. Select "Open" from the context menu
3. Click "Open" in the dialog that appears
4. You only need to do this once; subsequent launches will open normally

## API Key Configuration

Incalmo requires an Anthropic API key to use Claude Sonnet 3.7:

1. Launch Incalmo
2. Click on the "Settings" icon in the sidebar
3. Enter your Anthropic API key in the designated field
4. Click "Save"

If you don't have an API key, you can obtain one from the [Anthropic website](https://www.anthropic.com/).

## Uninstallation

To uninstall Incalmo:

1. Open the Applications folder in Finder
2. Drag the Incalmo application to the Trash
3. Empty the Trash

## Troubleshooting

### Application Won't Start

- Ensure you have sufficient disk space
- Check that you're running a compatible version of macOS
- Try restarting your computer

### Backend Connection Issues

- Verify your internet connection
- Check that your API key is entered correctly
- Ensure no firewall is blocking the application

### Performance Issues

- Close other resource-intensive applications
- Restart the application
- Ensure your system meets the minimum requirements

## Support

For additional support or to report issues, please contact:
- Email: support@incalmo.example.com
- GitHub Issues: https://github.com/incalmo/incalmo-app/issues

## License

Incalmo is distributed under the MIT License. See the LICENSE file for more information.
