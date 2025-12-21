#!/bin/bash

set -e

echo "========================================"
echo "   Docker Compose Local Development"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if .env files exist
if [ ! -f .env ]; then
  echo -e "${RED}❌ Backend .env not found${NC}"
  echo "   Run: cp .env.example .env"
  echo "   Then edit with your credentials"
  exit 1
fi

if [ ! -f web/.env.local ]; then
  echo -e "${RED}❌ Frontend web/.env.local not found${NC}"
  echo "   Run: cp web/.env.example web/.env.local"
  echo "   Then edit with your credentials"
  exit 1
fi

echo -e "${GREEN}✅ Environment files found${NC}"
echo ""

# Parse command
COMMAND=${1:-up}

case $COMMAND in
  up|start)
    echo "Starting services with Docker Compose..."
    echo ""
    docker-compose up --build -d
    echo ""
    echo -e "${GREEN}✅ Services started!${NC}"
    echo ""
    echo "Services running:"
    echo "  - Backend:  http://localhost:8000"
    echo "  - Frontend: http://localhost:3000"
    echo ""
    echo "View logs:"
    echo "  docker-compose logs -f"
    echo ""
    echo "Check status:"
    echo "  docker-compose ps"
    echo ""
    echo "Stop services:"
    echo "  ./docker-local.sh stop"
    ;;

  down|stop)
    echo "Stopping services..."
    docker-compose down
    echo -e "${GREEN}✅ Services stopped${NC}"
    ;;

  restart)
    echo "Restarting services..."
    docker-compose restart
    echo -e "${GREEN}✅ Services restarted${NC}"
    ;;

  logs)
    echo "Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f ${2}
    ;;

  build)
    echo "Rebuilding containers..."
    docker-compose build --no-cache
    echo -e "${GREEN}✅ Build complete${NC}"
    ;;

  status|ps)
    docker-compose ps
    ;;

  clean)
    echo "Cleaning up containers and volumes..."
    docker-compose down -v
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    ;;

  shell)
    SERVICE=${2:-backend}
    echo "Opening shell in $SERVICE container..."
    docker-compose exec $SERVICE sh
    ;;

  test)
    echo "Testing services..."
    echo ""

    # Test backend
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
      HEALTH=$(curl -s http://localhost:8000/health)
      echo -e "${GREEN}✅ Backend responding:${NC} $HEALTH"
    else
      echo -e "${RED}❌ Backend not responding${NC}"
    fi

    # Test frontend
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
      echo -e "${GREEN}✅ Frontend responding${NC}"
    else
      echo -e "${RED}❌ Frontend not responding${NC}"
    fi
    ;;

  help|*)
    echo "Usage: ./docker-local.sh [command]"
    echo ""
    echo "Commands:"
    echo "  up, start     - Start services (default)"
    echo "  down, stop    - Stop services"
    echo "  restart       - Restart services"
    echo "  logs [svc]    - Show logs (optional: backend/frontend)"
    echo "  build         - Rebuild containers"
    echo "  status, ps    - Show container status"
    echo "  clean         - Stop and remove containers + volumes"
    echo "  shell [svc]   - Open shell in container (default: backend)"
    echo "  test          - Test if services are responding"
    echo "  help          - Show this help"
    echo ""
    echo "Examples:"
    echo "  ./docker-local.sh up          # Start all services"
    echo "  ./docker-local.sh logs        # Show all logs"
    echo "  ./docker-local.sh logs backend # Show backend logs only"
    echo "  ./docker-local.sh shell backend # Shell into backend container"
    echo "  ./docker-local.sh test        # Test if services are up"
    echo "  ./docker-local.sh stop        # Stop services"
    ;;
esac
