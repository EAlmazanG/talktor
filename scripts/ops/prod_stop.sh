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

# Stop all services
echo -e "${YELLOW}Stopping all services...${NC}"
docker-compose -f docker-compose.yml down

# Check if all containers are stopped
if [ "$(docker ps -q -f name=talktor)" ]; then
    echo -e "${RED}Warning: Some containers are still running. Forcing stop...${NC}"
    docker-compose -f docker-compose.yml down --remove-orphans
else
    echo -e "${GREEN}All services stopped successfully${NC}"
fi
