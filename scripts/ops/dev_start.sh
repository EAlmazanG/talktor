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

############################
# Ensure Docker is running #
############################
echo -e "${YELLOW}Ensuring Docker Desktop is running...${NC}"
if ! command -v docker >/dev/null 2>&1; then
  echo -e "${RED}Docker CLI not found. Please install Docker Desktop for Mac.${NC}"
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo -e "${YELLOW}Starting Docker Desktop...${NC}"
  open -a Docker || true
  echo -n "${YELLOW}Waiting for Docker to be ready${NC}"
  DOCKER_WAIT_START=$(date +%s)
  while ! docker info >/dev/null 2>&1; do
    echo -n "."
    sleep 2
    if [ $(( $(date +%s) - DOCKER_WAIT_START )) -gt 120 ]; then
      echo -e "\n${RED}Docker did not become ready within 120 seconds.${NC}"
      exit 1
    fi
  done
  echo -e "\n${GREEN}Docker is ready.${NC}"
else
  echo -e "${GREEN}Docker is already running.${NC}"
fi

#########################################
# Start database services (Docker Compose)
#########################################
echo -e "${YELLOW}Starting database services in Docker...${NC}"
if docker compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker-compose"
else
  echo -e "${RED}Neither 'docker compose' nor 'docker-compose' is available.${NC}"
  exit 1
fi
$DOCKER_COMPOSE -f docker-compose.dev.yml up -d

# Wait for the database to be ready (basic wait)
echo -e "${YELLOW}Waiting for database to be ready...${NC}"
sleep 5

# Configure environment variables for local development
export POSTGRES_HOST=localhost

#########################################
# Activate Python virtual environment   #
#########################################
echo -e "${YELLOW}Activating virtual environment...${NC}"
if [ -d ".venv" ]; then
  source .venv/bin/activate
else
  echo -e "${RED}No virtual environment found at .venv/.${NC}"
  echo -e "${YELLOW}Create one with: python3 -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt${NC}"
  exit 1
fi
echo -e "${GREEN}Using python: $(which python) ($(python --version 2>/dev/null || python3 --version 2>/dev/null))${NC}"

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

# Start the backend with uvicorn (background) and check health
echo -e "${GREEN}Starting backend in development mode...${NC}"
echo -e "${GREEN}API will be available at http://localhost:8000${NC}"
echo -e "${GREEN}API documentation will be available at http://localhost:8000/docs${NC}"
echo -e "${GREEN}pgAdmin will be available at http://localhost:5050${NC}"

LOG_FILE=".dev_uvicorn.log"
echo -e "${YELLOW}Launching uvicorn in background... (logs -> ${LOG_FILE})${NC}"
nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 > "${LOG_FILE}" 2>&1 &
UVICORN_PID=$!
echo -e "${BLUE}uvicorn PID: ${UVICORN_PID}${NC}"

echo -n "${YELLOW}Waiting for API health at /health${NC}"
HEALTH_OK=0
for i in {1..60}; do
  if curl -sf "http://127.0.0.1:8000/health" >/dev/null 2>&1; then
    HEALTH_OK=1
    break
  fi
  echo -n "."
  sleep 1
done
echo

if [ "$HEALTH_OK" -eq 1 ]; then
  echo -e "${GREEN}API is healthy. You're ready to run tests and develop.${NC}"
else
  echo -e "${RED}API did not become healthy within 60s. See logs below:${NC}"
  echo "------ Last 80 lines of ${LOG_FILE} ------"
  tail -n 80 "${LOG_FILE}" || true
  exit 1
fi

echo -e "${YELLOW}To stop the API later: kill ${UVICORN_PID} (or pkill -f \"uvicorn main:app --reload\")${NC}"
