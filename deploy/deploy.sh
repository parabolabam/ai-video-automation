#!/bin/bash
set -e

# =============================================================================
# AI Video Automation - Deployment Script
# =============================================================================
# Run this script from the project root directory
# Usage: ./deploy/deploy.sh [start|stop|restart|logs|status|update]
# =============================================================================

COMPOSE_FILE="docker-compose.prod.yml"
PROJECT_NAME="ai-video-automation"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_env() {
    if [ ! -f ".env" ]; then
        log_error ".env file not found!"
        log_info "Copy .env.example to .env and fill in your API keys"
        exit 1
    fi

    # Check for required environment variables
    required_vars=("SUPABASE_URL" "SUPABASE_KEY" "OPENAI_API_KEY")
    missing_vars=()

    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env || grep -q "^${var}=your_" .env; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "Missing or unconfigured environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi

    log_info "Environment check passed"
}

start() {
    log_info "Starting $PROJECT_NAME..."
    check_env
    docker-compose -f $COMPOSE_FILE up -d --build
    log_info "Application started!"
    log_info "Web UI: http://localhost (or http://YOUR_IP.nip.io)"
    log_info "API: http://localhost/api/"
}

stop() {
    log_info "Stopping $PROJECT_NAME..."
    docker-compose -f $COMPOSE_FILE down
    log_info "Application stopped"
}

restart() {
    log_info "Restarting $PROJECT_NAME..."
    stop
    start
}

logs() {
    docker-compose -f $COMPOSE_FILE logs -f --tail=100
}

status() {
    log_info "Container status:"
    docker-compose -f $COMPOSE_FILE ps
    echo ""
    log_info "Resource usage:"
    docker stats --no-stream $(docker-compose -f $COMPOSE_FILE ps -q) 2>/dev/null || echo "No running containers"
}

update() {
    log_info "Updating $PROJECT_NAME..."

    # Pull latest changes
    if [ -d ".git" ]; then
        log_info "Pulling latest changes from git..."
        git pull
    fi

    # Rebuild and restart
    log_info "Rebuilding containers..."
    docker-compose -f $COMPOSE_FILE build --no-cache

    log_info "Restarting with new images..."
    docker-compose -f $COMPOSE_FILE up -d

    # Cleanup old images
    log_info "Cleaning up old images..."
    docker image prune -f

    log_info "Update complete!"
}

# Main
case "${1:-start}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    update)
        update
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|update}"
        exit 1
        ;;
esac
