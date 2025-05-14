#!/bin/bash
# Script to generate requirements.txt for backend

# Exit on error
set -e

echo "Generating requirements.txt for backend..."

# Navigate to backend directory
cd ../src/backend

# Create requirements.txt
cat > requirements.txt << EOF
# Core dependencies
fastapi==0.104.1
uvicorn==0.23.2
pydantic==2.4.2
anthropic==0.5.0
python-dotenv==1.0.0

# Database and state management
sqlalchemy==2.0.22

# Network and graph analysis
networkx==3.1

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.0

# Utilities
python-multipart==0.0.6
websockets==11.0.3
EOF

echo "requirements.txt generated successfully!"
