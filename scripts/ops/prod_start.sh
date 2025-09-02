#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting Talktor production environment ===${NC}"

# Determine repo root (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "$REPO_ROOT"

# Load environment variables
source .env

# Start Docker services with production configuration
echo -e "${YELLOW}Starting all services in production mode...${NC}"
docker-compose -f docker-compose.yml up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}All services are up and running.${NC}"
    
    # Display access information
    echo -e "${GREEN}=== Talktor is now available ===${NC}"
    echo -e "API: http://localhost:8000"
    echo -e "API Documentation: http://localhost:8000/docs"
    echo -e "Frontend: http://localhost:3000"
    echo -e "pgAdmin: http://localhost:5050"
else
    echo -e "${RED}Error: Some services failed to start. Check logs with 'docker-compose logs'.${NC}"
    exit 1
fi
