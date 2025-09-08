#!/bin/bash

# Script to stop Docker services for the development environment

# Colors for messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Stopping Talktor Docker services ===${NC}"

# Determine repo root (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "$REPO_ROOT"

# Show active virtualenv (if any)
if [ -n "$VIRTUAL_ENV" ]; then
  echo -e "${YELLOW}Active virtualenv: $VIRTUAL_ENV${NC}"
  echo -e "${YELLOW}You can deactivate it with: 'deactivate'${NC}"
fi

# Stop local API (uvicorn) if running
echo -e "${YELLOW}Stopping local API (uvicorn)...${NC}"
UVICORN_PIDS=$(pgrep -f "uvicorn main:app --reload" || true)
if [ -n "$UVICORN_PIDS" ]; then
  echo -e "${YELLOW}Found uvicorn PIDs: $UVICORN_PIDS. Sending SIGTERM...${NC}"
  kill $UVICORN_PIDS 2>/dev/null || true
  sleep 1
  if pgrep -f "uvicorn main:app --reload" >/dev/null 2>&1; then
    echo -e "${YELLOW}uvicorn still running. Sending SIGKILL...${NC}"
    pkill -9 -f "uvicorn main:app --reload" || true
  fi
else
  echo -e "${GREEN}No uvicorn dev server found.${NC}"
fi

# Free port 8000 if still occupied
PORT_PID=$(lsof -i :8000 -sTCP:LISTEN -t 2>/dev/null)
if [ ! -z "$PORT_PID" ]; then
  echo -e "${YELLOW}Freeing port 8000 (PID $PORT_PID)...${NC}"
  kill $PORT_PID 2>/dev/null || true
  sleep 1
  if lsof -i :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    kill -9 $PORT_PID 2>/dev/null || true
  fi
fi

# Stop Docker services
echo -e "${YELLOW}Stopping Docker services...${NC}"
if docker compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker-compose"
else
  echo -e "${RED}Neither 'docker compose' nor 'docker-compose' is available.${NC}"
  exit 1
fi
$DOCKER_COMPOSE -f docker-compose.dev.yml down

echo -e "${GREEN}Services stopped successfully${NC}"
