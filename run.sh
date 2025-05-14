#!/bin/bash

# Incalmo Run Script for macOS
# This script automates the setup and running of the Incalmo application from source code
# With special handling for macOS compatibility

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print warning messages
print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_header "Checking Prerequisites"

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION is installed"
else
    print_error "Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

# Check Node.js
if command_exists node; then
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION is installed"
else
    print_error "Node.js is not installed. Please install Node.js 16 or later."
    exit 1
fi

# Check npm
if command_exists npm; then
    NPM_VERSION=$(npm --version)
    print_success "npm $NPM_VERSION is installed"
else
    print_error "npm is not installed. Please install npm."
    exit 1
fi

# Check if running on macOS
IS_MACOS=false
if [[ "$(uname)" == "Darwin" ]]; then
    IS_MACOS=true
    print_warning "Detected macOS: Using macOS-compatible dependencies"
    
    # Check for Rust (needed for some Python packages on macOS)
    if command_exists rustc; then
        RUST_VERSION=$(rustc --version | cut -d' ' -f2)
        print_success "Rust $RUST_VERSION is installed"
    else
        print_warning "Rust is not installed. Some packages might fail to build."
        print_warning "Consider installing Rust with: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    fi
    
    # Check for Xcode command line tools
    if xcode-select -p &>/dev/null; then
        print_success "Xcode command line tools are installed"
    else
        print_warning "Xcode command line tools are not installed."
        print_warning "Consider installing them with: xcode-select --install"
    fi
fi

# Create a .env file for the backend
print_header "Setting up Environment"

BACKEND_DIR="$PROJECT_DIR/src/backend"
MACOS_APP_DIR="$PROJECT_DIR/macos-app"

# Create backend .env file if it doesn't exist
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "Creating .env file for backend..."
    echo "ANTHROPIC_API_KEY=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" > "$BACKEND_DIR/.env"
    print_success "Created .env file with API key"
else
    print_success "Backend .env file already exists"
fi

# Set up backend
print_header "Setting up Backend"

# Create virtual environment if it doesn't exist
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "Creating Python virtual environment..."
    cd "$BACKEND_DIR"
    python3 -m venv venv
    print_success "Created Python virtual environment"
else
    print_success "Python virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
cd "$BACKEND_DIR"
source venv/bin/activate

# Use macOS-specific requirements if on macOS
if [ "$IS_MACOS" = true ]; then
    if [ -f "$PROJECT_DIR/requirements_macos.txt" ]; then
        print_warning "Using project-level macOS requirements file..."
        cp "$PROJECT_DIR/requirements_macos.txt" "$BACKEND_DIR/"
    elif [ ! -f "$BACKEND_DIR/requirements_macos.txt" ]; then
        print_warning "macOS requirements file not found, creating it..."
        cat > "$BACKEND_DIR/requirements_macos.txt" << EOF
fastapi>=0.104.1
uvicorn>=0.24.0
pydantic>=2.5.0
anthropic>=0.18.0
sqlalchemy>=2.0.28
networkx>=3.3
pytest>=7.4.3
python-dotenv>=1.0.0
websockets>=11.0.3
httpx>=0.25.0
python-multipart>=0.0.7
typing-extensions>=4.9.0
anyio>=4.2.0
click>=8.1.7
h11>=0.14.0
idna>=3.6
sniffio>=1.3.0
pluggy>=1.3.0
packaging>=23.2
exceptiongroup>=1.2.0
iniconfig>=2.0.0
certifi>=2023.11.17
distro>=1.9.0
requests>=2.31.0
urllib3>=2.1.0
charset-normalizer>=3.3.2
EOF
    fi
    
    print_warning "Installing macOS-compatible dependencies..."
    pip install --upgrade pip
    pip install -r requirements_macos.txt
    export PYTHONPATH=$BACKEND_DIR:$PYTHONPATH
else
    pip install -r requirements.txt
fi

print_success "Installed backend dependencies"

# Set up frontend
print_header "Setting up Frontend"

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd "$MACOS_APP_DIR"
npm install
print_success "Installed frontend dependencies"

# Create app icon
echo "Creating app icon..."
node scripts/create_icon.js
print_success "Created app icon"

# Start the backend server
print_header "Starting Backend Server"

# Check if port 8713 is already in use
if nc -z localhost 8713 2>/dev/null; then
    print_warning "Port 8713 is already in use. Checking if it's our backend..."
    
    # Check if it's responding to our health endpoint
    if curl -s http://localhost:8713/health > /dev/null; then
        print_warning "An Incalmo backend server is already running on port 8713."
        print_warning "Using the existing backend server."
        
        # Save a placeholder PID since we don't know the actual PID
        echo "999999" > "$PROJECT_DIR/backend.pid"
    else
        print_error "Port 8713 is in use by another application. Please stop it before continuing."
        exit 1
    fi
else
    echo "Starting backend server on port 8713..."
    cd "$BACKEND_DIR"
    source venv/bin/activate
    # Start the backend server in the background
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8713 > backend.log 2>&1 &
    BACKEND_PID=$!
    echo "Backend server started with PID: $BACKEND_PID"

    # Save the PID to a file for later cleanup
    echo $BACKEND_PID > "$PROJECT_DIR/backend.pid"
fi

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Check if a port.txt file was created, which indicates a port change
PORT_FILE="$BACKEND_DIR/port.txt"
BACKEND_PORT=8713
if [ -f "$PORT_FILE" ]; then
    NEW_PORT=$(cat "$PORT_FILE")
    if [ "$NEW_PORT" != "8713" ]; then
        print_warning "Backend is running on port $NEW_PORT instead of default 8713"
        BACKEND_PORT=$NEW_PORT
    fi
fi

# Check if backend is running
echo "Checking if backend is running..."
for attempt in {1..15}; do
    if curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null; then
        print_success "Backend server is running on port $BACKEND_PORT"
        break
    else
        # Also try with 127.0.0.1 in case localhost resolution is an issue
        if curl -s "http://127.0.0.1:$BACKEND_PORT/health" > /dev/null; then
            print_success "Backend server is running on 127.0.0.1:$BACKEND_PORT"
            break
        fi
        
        if [ $attempt -eq 15 ]; then
            print_error "Backend server failed to start. Check backend.log for details."
            cat "$BACKEND_DIR/backend.log"
            exit 1
        fi
        echo "Waiting for backend to start (attempt $attempt/15)..."
        sleep 2
    fi
done

# Start the Electron app
print_header "Starting Incalmo Application"

echo "Starting Electron app in development mode..."
cd "$MACOS_APP_DIR"
NODE_ENV=development npm start &
ELECTRON_PID=$!
echo "Electron app started with PID: $ELECTRON_PID"

# Save the PID to a file for later cleanup
echo $ELECTRON_PID > "$PROJECT_DIR/electron.pid"

print_success "Incalmo application is now running!"
print_warning "To stop the application, run: ./stop.sh"

# Create a stop script
cat > "$PROJECT_DIR/stop.sh" << EOF
#!/bin/bash

# Stop script for Incalmo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"

# Stop the backend server
if [ -f "\$SCRIPT_DIR/backend.pid" ]; then
    BACKEND_PID=\$(cat "\$SCRIPT_DIR/backend.pid")
    echo -e "\${GREEN}Stopping backend server (PID: \$BACKEND_PID)...\${NC}"
    kill \$BACKEND_PID 2>/dev/null || true
    rm "\$SCRIPT_DIR/backend.pid"
    echo -e "\${GREEN}Backend server stopped\${NC}"
else
    echo -e "\${RED}No backend PID file found\${NC}"
fi

# Stop the Electron app
if [ -f "\$SCRIPT_DIR/electron.pid" ]; then
    ELECTRON_PID=\$(cat "\$SCRIPT_DIR/electron.pid")
    echo -e "\${GREEN}Stopping Electron app (PID: \$ELECTRON_PID)...\${NC}"
    kill \$ELECTRON_PID 2>/dev/null || true
    rm "\$SCRIPT_DIR/electron.pid"
    echo -e "\${GREEN}Electron app stopped\${NC}"
else
    echo -e "\${RED}No Electron PID file found\${NC}"
fi

echo -e "\${GREEN}Incalmo application has been stopped\${NC}"
EOF

chmod +x "$PROJECT_DIR/stop.sh"
print_success "Created stop.sh script"

echo ""
echo -e "${GREEN}Incalmo is now running!${NC}"
echo "Backend API: http://localhost:8713"
echo "API Documentation: http://localhost:8713/docs"
echo ""
echo "The Electron app should have launched automatically."
echo "If you need to stop the application, run: ./stop.sh"
