#!/bin/bash

# Rollback script for deployments
# Usage: ./rollback.sh [backend|frontend|all]

set -e

COMPONENT=${1:-all}

echo "=== AI Video Automation - Rollback Script ==="
echo ""

rollback_backend() {
    echo "Rolling back backend..."

    # Get previous image
    PREVIOUS_IMAGE=$(docker images ghcr.io/*-backend --format "{{.Repository}}:{{.Tag}}" | sed -n '2p')

    if [ -z "$PREVIOUS_IMAGE" ]; then
        echo "Error: No previous backend image found"
        return 1
    fi

    echo "Rolling back to: $PREVIOUS_IMAGE"

    # Stop current container
    docker stop ai-video-backend || true
    docker rm ai-video-backend || true

    # Start previous version
    docker run -d \
        --name ai-video-backend \
        --restart unless-stopped \
        -p 8000:8000 \
        -v /opt/ai-video-automation/data:/data \
        -v /opt/ai-video-automation/.env:/app/.env:ro \
        --env-file /opt/ai-video-automation/.env \
        --memory="2g" \
        --cpus="2" \
        $PREVIOUS_IMAGE \
        uv run uvicorn features.platform.server:app --host 0.0.0.0 --port 8000

    echo "Backend rolled back successfully!"
}

rollback_frontend() {
    echo "Rolling back frontend..."

    # Get previous image
    PREVIOUS_IMAGE=$(docker images ghcr.io/*-frontend --format "{{.Repository}}:{{.Tag}}" | sed -n '2p')

    if [ -z "$PREVIOUS_IMAGE" ]; then
        echo "Error: No previous frontend image found"
        return 1
    fi

    echo "Rolling back to: $PREVIOUS_IMAGE"

    # Stop current container
    docker stop ai-video-frontend || true
    docker rm ai-video-frontend || true

    # Start previous version
    docker run -d \
        --name ai-video-frontend \
        --restart unless-stopped \
        -p 3000:3000 \
        --env-file /opt/ai-video-automation/.env \
        --memory="1g" \
        --cpus="1" \
        $PREVIOUS_IMAGE

    echo "Frontend rolled back successfully!"
}

case $COMPONENT in
    backend)
        rollback_backend
        ;;
    frontend)
        rollback_frontend
        ;;
    all)
        rollback_backend
        rollback_frontend
        ;;
    *)
        echo "Usage: $0 [backend|frontend|all]"
        exit 1
        ;;
esac

echo ""
echo "Rollback complete!"
echo ""
