#!/bin/bash
# Deployment script for Incalmo

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
  echo "Loading environment variables from .env"
  export $(grep -v '^#' .env | xargs)
else
  echo "Error: .env file not found"
  echo "Please copy .env.example to .env and fill in the values"
  exit 1
fi

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
  echo "Error: Docker is not installed"
  echo "Please install Docker: https://docs.docker.com/get-docker/"
  exit 1
fi

if ! command -v docker-compose &> /dev/null; then
  echo "Error: Docker Compose is not installed"
  echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
  exit 1
fi

# Check if Anthropic API key is set
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_anthropic_api_key_here" ]; then
  echo "Error: Anthropic API key is not set"
  echo "Please set ANTHROPIC_API_KEY in .env file"
  exit 1
fi

# Build and start the containers
echo "Building and starting Incalmo containers..."
docker-compose up -d --build

# Check if containers are running
if [ "$(docker-compose ps -q | wc -l)" -ne 2 ]; then
  echo "Error: Not all containers are running"
  docker-compose logs
  exit 1
fi

echo "Incalmo has been successfully deployed!"
echo "Frontend: $FRONTEND_URL"
echo "Backend API: $API_BASE_URL"
echo "WebSocket: $WS_BASE_URL"
echo ""
echo "To stop the application, run: docker-compose down"
echo "To view logs, run: docker-compose logs -f"
