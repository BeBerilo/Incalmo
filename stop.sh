#!/bin/bash

# Stop script for Incalmo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Stop the backend server
if [ -f "$SCRIPT_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$SCRIPT_DIR/backend.pid")
    echo -e "${GREEN}Stopping backend server (PID: $BACKEND_PID)...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    rm "$SCRIPT_DIR/backend.pid"
    echo -e "${GREEN}Backend server stopped${NC}"
else
    echo -e "${RED}No backend PID file found${NC}"
fi

# Stop the Electron app
if [ -f "$SCRIPT_DIR/electron.pid" ]; then
    ELECTRON_PID=$(cat "$SCRIPT_DIR/electron.pid")
    echo -e "${GREEN}Stopping Electron app (PID: $ELECTRON_PID)...${NC}"
    kill $ELECTRON_PID 2>/dev/null || true
    rm "$SCRIPT_DIR/electron.pid"
    echo -e "${GREEN}Electron app stopped${NC}"
else
    echo -e "${RED}No Electron PID file found${NC}"
fi

echo -e "${GREEN}Incalmo application has been stopped${NC}"
