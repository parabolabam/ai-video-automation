#!/bin/bash

# Update nginx configuration to serve both frontend and backend
# Run this on the Digital Ocean droplet

set -e

DOMAIN="vingine.duckdns.org"
NGINX_CONTAINER="ai-video-nginx"
CONFIG_DIR="/opt/ai-video-automation/nginx/conf.d"

echo "========================================="
echo "Updating nginx for full-stack deployment"
echo "========================================="
echo ""

# Get backend and frontend container IPs
BACKEND_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ai-video-backend)
FRONTEND_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ai-video-frontend)

echo "Backend IP: $BACKEND_IP"
echo "Frontend IP: $FRONTEND_IP"
echo ""

if [ -z "$BACKEND_IP" ]; then
    echo "❌ Backend container not found or not running"
    exit 1
fi

if [ -z "$FRONTEND_IP" ]; then
    echo "❌ Frontend container not found or not running"
    echo "Please deploy the frontend first using GitHub Actions"
    exit 1
fi

# Create updated nginx configuration
echo "Creating nginx configuration..."

cat > $CONFIG_DIR/vingine.conf << NGINX_EOF
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server - Full Stack
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

    # Allow large file uploads (for video processing)
    client_max_body_size 500M;

    # Backend API routes
    location /api/ {
        proxy_pass http://$BACKEND_IP:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Increase timeout for long-running operations
        proxy_read_timeout 600s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 600s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://$BACKEND_IP:8000/health;
        access_log off;
    }

    # API docs
    location /docs {
        proxy_pass http://$BACKEND_IP:8000/docs;
    }

    location /openapi.json {
        proxy_pass http://$BACKEND_IP:8000/openapi.json;
    }

    # Frontend - Next.js application
    location / {
        proxy_pass http://$FRONTEND_IP:3000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Next.js specific settings
        proxy_buffering off;
        proxy_read_timeout 86400;
    }

    # Next.js static files
    location /_next/static/ {
        proxy_pass http://$FRONTEND_IP:3000/_next/static/;
        proxy_cache_valid 200 60m;
        proxy_cache_bypass \$http_pragma;
        add_header Cache-Control "public, immutable";
    }

    # Next.js webpack HMR (for development)
    location /_next/webpack-hmr {
        proxy_pass http://$FRONTEND_IP:3000/_next/webpack-hmr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGINX_EOF

echo "✅ Configuration created"

# Test nginx configuration
echo "Testing nginx configuration..."
if docker exec $NGINX_CONTAINER nginx -t; then
    echo "✅ Nginx configuration valid"
else
    echo "❌ Nginx configuration has errors"
    exit 1
fi

# Reload nginx
echo "Reloading nginx..."
docker exec $NGINX_CONTAINER nginx -s reload

echo ""
echo "========================================="
echo "✅ Nginx Configuration Updated!"
echo "========================================="
echo ""
echo "Your application is now accessible at:"
echo "  🌐 Frontend:        https://$DOMAIN"
echo "  🔌 Backend API:     https://$DOMAIN/api/"
echo "  🏥 Health Check:    https://$DOMAIN/health"
echo "  📚 API Docs:        https://$DOMAIN/docs"
echo ""
echo "Container IPs:"
echo "  Backend:  $BACKEND_IP:8000"
echo "  Frontend: $FRONTEND_IP:3000"
echo ""
