#!/bin/bash

# Script to stop Docker services for the development environment

# Colors for messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Stopping Talktor Docker services ===${NC}"

# Stop Docker services
echo -e "${YELLOW}Stopping services...${NC}"
docker-compose -f docker-compose.dev.yml down

echo -e "${GREEN}Services stopped successfully${NC}"
