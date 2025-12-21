#!/bin/sh
set -e

echo "=========================================="
echo "Nginx Container Starting"
echo "=========================================="

# Set default values if not provided
export DOMAIN="${DOMAIN:-vingine.duckdns.org}"
export BACKEND_HOST="${BACKEND_HOST:-ai-video-backend}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"
export FRONTEND_HOST="${FRONTEND_HOST:-ai-video-frontend}"
export FRONTEND_PORT="${FRONTEND_PORT:-3000}"

echo "Domain: $DOMAIN"
echo "Backend: $BACKEND_HOST:$BACKEND_PORT"
echo "Frontend: $FRONTEND_HOST:$FRONTEND_PORT"
echo "=========================================="

# Substitute environment variables in nginx config
envsubst '${DOMAIN} ${BACKEND_HOST} ${BACKEND_PORT} ${FRONTEND_HOST} ${FRONTEND_PORT}' \
  < /etc/nginx/nginx.conf.template \
  > /etc/nginx/nginx.conf

envsubst '${DOMAIN} ${BACKEND_HOST} ${BACKEND_PORT} ${FRONTEND_HOST} ${FRONTEND_PORT}' \
  < /etc/nginx/conf.d/vingine.conf.template \
  > /etc/nginx/conf.d/vingine.conf

echo "Nginx configuration generated"

# Test configuration
nginx -t

echo "✅ Nginx ready to start"

# Execute the CMD (nginx)
exec "$@"
