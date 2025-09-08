#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Stopping Talktor production environment ===${NC}"

# Determine repo root (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "$REPO_ROOT"

############################
# Detect docker compose CLI #
############################
if docker compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker-compose"
else
  echo -e "${RED}Neither 'docker compose' nor 'docker-compose' is available.${NC}"
  exit 1
fi

# Stop all services (optionally purge volumes)
PURGE=0
if [ "$1" == "--purge" ] || [ "$1" == "-p" ]; then
  PURGE=1
fi

echo -e "${YELLOW}Stopping all services...${NC}"
if [ $PURGE -eq 1 ]; then
  echo -e "${YELLOW}Purging volumes for a full reset...${NC}"
  $DOCKER_COMPOSE -f docker-compose.yml down --remove-orphans -v
else
  $DOCKER_COMPOSE -f docker-compose.yml down --remove-orphans
fi

# Verify containers are stopped
RUNNING_CONTAINERS=$(docker ps -q --filter "name=talktor")
if [ -n "$RUNNING_CONTAINERS" ]; then
  echo -e "${RED}Some containers still running: ${RUNNING_CONTAINERS}. You may need to stop them manually.${NC}"
else
  if [ $PURGE -eq 1 ]; then
    echo -e "${GREEN}All services stopped and volumes removed. Next start will be a clean install.${NC}"
  else
    echo -e "${GREEN}All services stopped successfully${NC}"
  fi
fi
