#!/bin/bash

# Configure vingine.duckdns.org by adding config to host directory
# Works with existing nginx container that has mounted config

set -e

DOMAIN="vingine.duckdns.org"
NGINX_CONTAINER="ai-video-nginx"
CONFIG_DIR="/opt/ai-video-automation/nginx/conf.d"

echo "========================================="
echo "Configuring $DOMAIN"
echo "========================================="
echo ""

# Check if nginx container is running
if ! docker ps | grep -q $NGINX_CONTAINER; then
    echo "❌ Nginx container '$NGINX_CONTAINER' is not running"
    exit 1
fi

echo "✅ Found nginx container: $NGINX_CONTAINER"

# Check if config directory exists on host
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Creating config directory: $CONFIG_DIR"
    mkdir -p $CONFIG_DIR
fi

# Get droplet IP
DROPLET_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null)
echo "✅ Droplet IP: $DROPLET_IP"

# Check DNS
echo ""
echo "Checking DNS resolution..."
RESOLVED_IP=$(nslookup $DOMAIN 8.8.8.8 2>/dev/null | grep -A 1 "Name:" | tail -1 | awk '{print $2}')

if [ "$RESOLVED_IP" == "$DROPLET_IP" ]; then
    echo "✅ DNS correctly pointing to this droplet"
else
    echo "⚠️  DNS currently pointing to: $RESOLVED_IP"
    echo "   Expected: $DROPLET_IP"
    echo ""
    echo "Update DuckDNS: https://www.duckdns.org/domains"
    echo "Set 'vingine' to IP: $DROPLET_IP"
    echo ""
    read -p "Press Enter once DNS is updated..."
fi

# Check if ai-video-backend is on same network
echo ""
echo "Checking Docker network..."
BACKEND_NETWORK=$(docker inspect ai-video-backend --format '{{range $net, $conf := .NetworkSettings.Networks}}{{$net}} {{end}}')
NGINX_NETWORK=$(docker inspect ai-video-nginx --format '{{range $net, $conf := .NetworkSettings.Networks}}{{$net}} {{end}}')

echo "Backend networks: $BACKEND_NETWORK"
echo "Nginx networks: $NGINX_NETWORK"

# Find common network or use first backend network
COMMON_NETWORK=""
for net in $BACKEND_NETWORK; do
    if echo "$NGINX_NETWORK" | grep -q "$net"; then
        COMMON_NETWORK=$net
        break
    fi
done

if [ -z "$COMMON_NETWORK" ]; then
    # Use first backend network
    COMMON_NETWORK=$(echo $BACKEND_NETWORK | awk '{print $1}')
    echo "⚠️  Containers on different networks"
    echo "   Connecting nginx to backend network: $COMMON_NETWORK"
    docker network connect $COMMON_NETWORK ai-video-nginx 2>/dev/null || true
fi

echo "✅ Using network: $COMMON_NETWORK"

# Create nginx configuration on host
echo ""
echo "Creating nginx configuration..."

cat > $CONFIG_DIR/vingine.conf << 'NGINX_EOF'
server {
    listen 80;
    server_name vingine.duckdns.org;

    # Allow large file uploads (for video processing)
    client_max_body_size 500M;

    location / {
        # Proxy to backend container
        proxy_pass http://ai-video-backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeout for long-running video processing
        proxy_read_timeout 600s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 600s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://ai-video-backend:8000/health;
        access_log off;
    }

    # API docs
    location /docs {
        proxy_pass http://ai-video-backend:8000/docs;
    }
}
NGINX_EOF

echo "✅ Configuration created at: $CONFIG_DIR/vingine.conf"

# Test nginx config
echo ""
echo "Testing nginx configuration..."
if docker exec $NGINX_CONTAINER nginx -t; then
    echo "✅ Nginx configuration valid"
else
    echo "❌ Nginx configuration has errors"
    exit 1
fi

# Reload nginx
echo ""
echo "Reloading nginx..."
docker exec $NGINX_CONTAINER nginx -s reload

echo ""
echo "✅ Nginx reloaded successfully!"
echo ""
echo "Testing backend connectivity..."
sleep 2

if curl -f http://$DOMAIN/health 2>/dev/null; then
    echo "✅ Backend is accessible via $DOMAIN"
else
    echo "⚠️  Health check failed, but config is loaded"
    echo "   Check backend: docker logs ai-video-backend"
fi

echo ""
echo "Your backend is now accessible at:"
echo "  🌐 http://$DOMAIN"
echo "  🏥 http://$DOMAIN/health"
echo "  📚 http://$DOMAIN/docs"
echo ""

# Setup SSL
echo "========================================="
echo "SSL/HTTPS Setup"
echo "========================================="
echo ""
read -p "Do you want to setup SSL/HTTPS with Let's Encrypt? (y/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "To setup SSL with your existing nginx container:"
    echo ""
    echo "1. Make sure certbot is running as a separate container or"
    echo "2. Install certbot and run:"
    echo ""
    echo "   certbot certonly --webroot -w /opt/ai-video-automation/certbot/www \\"
    echo "     -d $DOMAIN --agree-tos --register-unsafely-without-email"
    echo ""
    echo "3. Then update $CONFIG_DIR/vingine.conf to add SSL:"
    echo ""
    echo "   server {"
    echo "       listen 443 ssl;"
    echo "       server_name $DOMAIN;"
    echo "       ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;"
    echo "       ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;"
    echo "       # ... rest of config"
    echo "   }"
    echo ""
    echo "4. Reload nginx:"
    echo "   docker exec $NGINX_CONTAINER nginx -s reload"
fi

echo ""
echo "========================================="
echo "✅ Configuration Complete!"
echo "========================================="
echo ""
echo "Configuration file: $CONFIG_DIR/vingine.conf"
echo ""
echo "Test your backend:"
echo "  curl http://$DOMAIN/health"
echo ""
echo "View logs:"
echo "  docker logs -f $NGINX_CONTAINER"
echo "  docker logs -f ai-video-backend"
echo ""
