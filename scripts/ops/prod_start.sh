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

#################################
# Ensure .env exists (first run) #
#################################
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    echo -e "${YELLOW}Created .env from .env.example. Please set OPENAI_API_KEY in .env before using AI features.${NC}"
  else
    echo -e "${RED}Missing .env and .env.example. Create .env with database and OpenAI settings.${NC}"
    exit 1
  fi
fi

# Export variables from .env for this shell (optional; compose also reads .env automatically)
set -a
source .env
set +a

if [ -z "$OPENAI_API_KEY" ] || [[ "$OPENAI_API_KEY" == "your_openai_api_key_here" ]]; then
  echo -e "${YELLOW}Warning: OPENAI_API_KEY is not set or is a placeholder. Backend will start, but AI features won't work until you set it in .env.${NC}"
fi

#############################################
# Pull/build and start all services (prod)  #
#############################################
echo -e "${YELLOW}Pulling base images and building services...${NC}"
$DOCKER_COMPOSE -f docker-compose.yml pull db pgadmin || true
echo -e "${YELLOW}Starting all services in production mode...${NC}"
$DOCKER_COMPOSE -f docker-compose.yml up -d --build

################################
# Wait for API health endpoint #
################################
echo -n "${YELLOW}Waiting for API health at http://localhost:8000/health${NC}"
HEALTH_OK=0
for i in {1..120}; do
  if curl -sf "http://127.0.0.1:8000/health" >/dev/null 2>&1; then
    HEALTH_OK=1
    break
  fi
  echo -n "."
  sleep 1
done
echo

if [ "$HEALTH_OK" -ne 1 ]; then
  echo -e "${RED}API did not become healthy within 120s. Use: $DOCKER_COMPOSE -f docker-compose.yml logs backend${NC}"
  exit 1
fi

echo -e "${GREEN}All services are up and healthy.${NC}"
echo -e "${GREEN}=== Talktor is now available ===${NC}"
echo -e "API:       http://localhost:8000"
echo -e "Docs:      http://localhost:8000/docs"
echo -e "Frontend:  http://localhost:3000"
echo -e "pgAdmin:   http://localhost:5050"

# Open frontend in default browser (macOS)
if command -v open >/dev/null 2>&1; then
  open "http://localhost:3000" || true
fi
