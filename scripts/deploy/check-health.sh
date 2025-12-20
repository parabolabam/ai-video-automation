#!/bin/bash

# Health check script for deployed services
# Usage: ./check-health.sh

set -e

echo "=== AI Video Automation - Health Check ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local service_name=$1
    local url=$2
    local container_name=$3

    echo -n "Checking $service_name... "

    # Check if container is running
    if ! docker ps | grep -q $container_name; then
        echo -e "${RED}FAILED${NC} - Container not running"
        return 1
    fi

    # Check HTTP endpoint
    if curl -f -s -o /dev/null -w "%{http_code}" $url > /dev/null 2>&1; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $url)
        if [ $HTTP_CODE -eq 200 ] || [ $HTTP_CODE -eq 404 ]; then
            echo -e "${GREEN}OK${NC} (HTTP $HTTP_CODE)"
            return 0
        else
            echo -e "${YELLOW}WARNING${NC} (HTTP $HTTP_CODE)"
            return 1
        fi
    else
        echo -e "${RED}FAILED${NC} - Not responding"
        return 1
    fi
}

# Check backend
check_service "Backend API" "http://localhost:8000/health" "ai-video-backend"
BACKEND_STATUS=$?

# Check frontend
check_service "Frontend" "http://localhost:3000" "ai-video-frontend"
FRONTEND_STATUS=$?

echo ""
echo "=== Container Status ==="
docker ps --filter "name=ai-video" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== Resource Usage ==="
docker stats --no-stream --filter "name=ai-video" --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

echo ""
echo "=== Disk Usage ==="
docker system df

echo ""
if [ $BACKEND_STATUS -eq 0 ] && [ $FRONTEND_STATUS -eq 0 ]; then
    echo -e "${GREEN}All services healthy!${NC}"
    exit 0
else
    echo -e "${RED}Some services are unhealthy!${NC}"
    echo ""
    echo "Check logs with:"
    echo "  docker logs ai-video-backend"
    echo "  docker logs ai-video-frontend"
    exit 1
fi
