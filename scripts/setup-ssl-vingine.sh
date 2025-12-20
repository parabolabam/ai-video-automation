#!/bin/bash

# Setup SSL/HTTPS for vingine.duckdns.org using existing certbot setup
# This works with your existing nginx and certbot containers

set -e

DOMAIN="vingine.duckdns.org"
NGINX_CONTAINER="ai-video-nginx"
CONFIG_DIR="/opt/ai-video-automation/nginx/conf.d"
CERTBOT_DIR="/opt/ai-video-automation/certbot"

echo "========================================="
echo "Setting up SSL for $DOMAIN"
echo "========================================="
echo ""

# Check if certbot directory exists
if [ ! -d "$CERTBOT_DIR" ]; then
    echo "Creating certbot directories..."
    mkdir -p $CERTBOT_DIR/{conf,www}
fi

# Install certbot if not present
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    sudo apt-get update
    sudo apt-get install -y certbot
fi

# Stop nginx temporarily to get certificate
echo "Obtaining SSL certificate..."
echo "This may take a minute..."

# Get certificate using standalone mode
sudo certbot certonly --standalone \
    --preferred-challenges http \
    -d $DOMAIN \
    --agree-tos \
    --register-unsafely-without-email \
    --pre-hook "docker stop $NGINX_CONTAINER" \
    --post-hook "docker start $NGINX_CONTAINER"

if [ $? -ne 0 ]; then
    echo "❌ Certificate acquisition failed"
    echo "Make sure port 80 is accessible and DNS is configured"
    docker start $NGINX_CONTAINER 2>/dev/null || true
    exit 1
fi

echo "✅ Certificate obtained!"

# Copy certificates to certbot directory
echo "Copying certificates..."
sudo cp -r /etc/letsencrypt/* $CERTBOT_DIR/conf/

# Update nginx configuration with SSL
echo "Updating nginx configuration..."

cat > $CONFIG_DIR/vingine.conf << 'NGINX_EOF'
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name vingine.duckdns.org;

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name vingine.duckdns.org;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/vingine.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vingine.duckdns.org/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

    # Allow large file uploads (for video processing)
    client_max_body_size 500M;

    location / {
        # Proxy to backend container IP
        proxy_pass http://172.17.0.2:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
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
        proxy_pass http://172.17.0.2:8000/health;
        access_log off;
    }

    # API docs
    location /docs {
        proxy_pass http://172.17.0.2:8000/docs;
    }
}
NGINX_EOF

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

# Setup auto-renewal
echo "Setting up SSL auto-renewal..."

cat > /opt/ai-video-automation/renew-ssl.sh << 'RENEW_EOF'
#!/bin/bash
# Renew SSL certificates

# Stop nginx
docker stop ai-video-nginx

# Renew certificate
certbot renew --standalone --quiet

# Copy renewed certificates
cp -r /etc/letsencrypt/* /opt/ai-video-automation/certbot/conf/

# Start nginx
docker start ai-video-nginx

echo "SSL certificates renewed: $(date)" >> /opt/ai-video-automation/logs/ssl-renewal.log
RENEW_EOF

chmod +x /opt/ai-video-automation/renew-ssl.sh

# Add to crontab (runs monthly)
(crontab -l 2>/dev/null | grep -v renew-ssl; echo "0 0 1 * * /opt/ai-video-automation/renew-ssl.sh") | crontab -

echo ""
echo "========================================="
echo "✅ SSL Setup Complete!"
echo "========================================="
echo ""
echo "Your backend is now accessible at:"
echo "  🔒 https://$DOMAIN"
echo "  🏥 https://$DOMAIN/health"
echo "  📚 https://$DOMAIN/docs"
echo ""
echo "HTTP traffic is automatically redirected to HTTPS"
echo ""
echo "SSL certificate auto-renewal:"
echo "  Script: /opt/ai-video-automation/renew-ssl.sh"
echo "  Schedule: Monthly (1st of each month)"
echo "  Logs: /opt/ai-video-automation/logs/ssl-renewal.log"
echo ""
echo "Test your SSL:"
echo "  curl https://$DOMAIN/health"
echo ""
