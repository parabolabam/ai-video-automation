#!/bin/bash

# Configure vingine.duckdns.org on existing nginx Docker container
# This works with your existing ai-video-nginx container

set -e

DOMAIN="vingine.duckdns.org"
NGINX_CONTAINER="ai-video-nginx"

echo "========================================="
echo "Configuring $DOMAIN on existing nginx"
echo "========================================="
echo ""

# Check if nginx container is running
if ! docker ps | grep -q $NGINX_CONTAINER; then
    echo "❌ Nginx container '$NGINX_CONTAINER' is not running"
    echo "Available containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    exit 1
fi

echo "✅ Found nginx container: $NGINX_CONTAINER"

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
    echo "Please update DuckDNS:"
    echo "1. Go to: https://www.duckdns.org/domains"
    echo "2. Update 'vingine' to IP: $DROPLET_IP"
    echo "3. Wait a few minutes for DNS propagation"
    echo ""
    read -p "Press Enter once you've updated DuckDNS..."
fi

# Create nginx configuration
echo ""
echo "Creating nginx configuration for $DOMAIN..."

# Check if nginx config volume exists
CONFIG_DIR="/etc/nginx/conf.d"
if docker exec $NGINX_CONTAINER ls $CONFIG_DIR &>/dev/null; then
    echo "✅ Config directory exists in container"
else
    CONFIG_DIR="/etc/nginx/http.d"
    if docker exec $NGINX_CONTAINER ls $CONFIG_DIR &>/dev/null; then
        echo "✅ Using Alpine nginx config directory"
    else
        echo "❌ Cannot find nginx config directory"
        exit 1
    fi
fi

# Create configuration
cat > /tmp/vingine.conf << 'NGINX_EOF'
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
}
NGINX_EOF

# Copy config to container
echo "Copying configuration to nginx container..."
docker cp /tmp/vingine.conf $NGINX_CONTAINER:$CONFIG_DIR/vingine.conf

# Test nginx config
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
echo "✅ Nginx configured successfully!"
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
    # Check if certbot is installed in container
    if docker exec $NGINX_CONTAINER which certbot &>/dev/null; then
        echo "✅ Certbot found in container"
    else
        echo "Installing certbot in nginx container..."
        docker exec $NGINX_CONTAINER apk add --no-cache certbot certbot-nginx || \
        docker exec $NGINX_CONTAINER apt-get update && docker exec $NGINX_CONTAINER apt-get install -y certbot python3-certbot-nginx
    fi

    # Get SSL certificate
    echo "Obtaining SSL certificate..."
    docker exec $NGINX_CONTAINER certbot --nginx -d $DOMAIN --non-interactive --agree-tos --register-unsafely-without-email || \
    docker exec $NGINX_CONTAINER certbot --nginx -d $DOMAIN

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ SSL certificate installed!"
        echo ""
        echo "Your backend is now accessible at:"
        echo "  🔒 https://$DOMAIN"
        echo "  🏥 https://$DOMAIN/health"
        echo "  📚 https://$DOMAIN/docs"

        # Setup auto-renewal
        echo ""
        echo "Setting up SSL auto-renewal..."
        # Create renewal script
        cat > /tmp/renew-ssl.sh << 'RENEW_EOF'
#!/bin/bash
docker exec ai-video-nginx certbot renew --nginx
RENEW_EOF
        chmod +x /tmp/renew-ssl.sh
        mv /tmp/renew-ssl.sh /opt/ai-video-automation/renew-ssl.sh

        # Add to crontab
        (crontab -l 2>/dev/null | grep -v renew-ssl; echo "0 0 * * * /opt/ai-video-automation/renew-ssl.sh") | crontab -
        echo "✅ Auto-renewal configured (runs daily)"
    else
        echo ""
        echo "❌ SSL setup failed"
        echo ""
        echo "Common issues:"
        echo "1. DNS not propagated - wait 5-10 minutes and try:"
        echo "   docker exec $NGINX_CONTAINER certbot --nginx -d $DOMAIN"
        echo ""
        echo "2. Backend not responding - check:"
        echo "   docker logs ai-video-backend"
    fi
else
    echo ""
    echo "Skipping SSL setup."
    echo "To setup SSL later, run:"
    echo "  docker exec $NGINX_CONTAINER certbot --nginx -d $DOMAIN"
fi

# Cleanup
rm -f /tmp/vingine.conf

echo ""
echo "========================================="
echo "✅ Configuration Complete!"
echo "========================================="
echo ""
echo "Domain: $DOMAIN"
echo "Backend container: ai-video-backend"
echo "Nginx container: $NGINX_CONTAINER"
echo ""
echo "Test your backend:"
echo "  curl http://$DOMAIN/health"
echo "  curl https://$DOMAIN/health  # if SSL enabled"
echo ""
echo "View nginx logs:"
echo "  docker logs -f $NGINX_CONTAINER"
echo ""
echo "View backend logs:"
echo "  docker logs -f ai-video-backend"
echo ""
