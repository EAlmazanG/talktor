#!/bin/bash

# Script to start the Talktor local development environment
# This script starts the databases in Docker and the backend locally

# Colors for messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting Talktor development environment ===${NC}"

# Determine repo root (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "$REPO_ROOT"

# Activate virtual environment (.venv preferred, fallback to talktor-env)
echo -e "${YELLOW}Activating virtual environment...${NC}"
if [ -d ".venv" ]; then
  source .venv/bin/activate
elif [ -d "talktor-env" ]; then
  source talktor-env/bin/activate
else
  echo -e "${RED}No virtual environment found (.venv/ or talktor-env/).${NC}"
  echo -e "${YELLOW}Create one with: python3 -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt${NC}"
  exit 1
fi

# Start database services with Docker Compose
echo -e "${YELLOW}Starting database services in Docker...${NC}"
docker-compose -f docker-compose.dev.yml up -d

# Wait for the database to be ready
echo -e "${YELLOW}Waiting for database to be ready...${NC}"
sleep 5

# Configure environment variables for local development
export POSTGRES_HOST=localhost

# Change to backend directory
cd backend

# Database is ready to use
echo -e "${GREEN}Database ready for development${NC}"

# Check if port 8000 is in use and kill the process if needed
echo -e "${YELLOW}Checking if port 8000 is already in use...${NC}"
PORT_PID=$(lsof -i :8000 -sTCP:LISTEN -t 2>/dev/null)
if [ ! -z "$PORT_PID" ]; then
    echo -e "${YELLOW}Port 8000 is in use by PID $PORT_PID. Attempting to kill...${NC}"
    kill $PORT_PID 2>/dev/null || echo -e "${YELLOW}Could not kill process. You may need to manually free port 8000.${NC}"
    sleep 2
fi

# Start the backend with uvicorn
echo -e "${GREEN}Starting backend in development mode...${NC}"
echo -e "${GREEN}API will be available at http://localhost:8000${NC}"
echo -e "${GREEN}API documentation will be available at http://localhost:8000/docs${NC}"
echo -e "${GREEN}pgAdmin will be available at http://localhost:5050${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
