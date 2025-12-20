#!/bin/bash

# Setup script for vingine.duckdns.org domain
# Run this on your Digital Ocean droplet after setting up the droplet

set -e

DOMAIN="vingine.duckdns.org"

echo "========================================="
echo "Setting up $DOMAIN"
echo "========================================="
echo ""

# Get current IP
DROPLET_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null)

if [ -z "$DROPLET_IP" ]; then
    echo "❌ Could not detect droplet IP address"
    echo "Please enter your droplet IP manually:"
    read -p "Droplet IP: " DROPLET_IP
fi

echo "✅ Detected droplet IP: $DROPLET_IP"
echo ""

# Check if DuckDNS is pointing to this IP
echo "Checking DNS resolution..."
RESOLVED_IP=$(nslookup $DOMAIN 8.8.8.8 2>/dev/null | grep -A 1 "Name:" | tail -1 | awk '{print $2}')

if [ "$RESOLVED_IP" == "$DROPLET_IP" ]; then
    echo "✅ DNS already pointing to this droplet!"
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

# Install nginx if not present
if ! command -v nginx &> /dev/null; then
    echo ""
    echo "Installing nginx..."
    sudo apt-get update
    sudo apt-get install -y nginx
fi

# Install certbot for SSL
if ! command -v certbot &> /dev/null; then
    echo ""
    echo "Installing certbot for SSL..."
    sudo apt-get install -y certbot python3-certbot-nginx
fi

# Create nginx configuration
echo ""
echo "Creating nginx configuration..."

sudo tee /etc/nginx/sites-available/vingine-backend > /dev/null << 'NGINX_EOF'
server {
    listen 80;
    server_name vingine.duckdns.org;

    # Allow large file uploads (for video processing)
    client_max_body_size 500M;

    location / {
        proxy_pass http://localhost:8000;
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
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
NGINX_EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/vingine-backend /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx config
echo ""
echo "Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration valid"
    sudo systemctl restart nginx
    sudo systemctl enable nginx
else
    echo "❌ Nginx configuration has errors"
    exit 1
fi

# Setup SSL with Let's Encrypt
echo ""
echo "Setting up SSL certificate..."
read -p "Do you want to setup SSL/HTTPS now? (y/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Make sure backend is running first
    if ! curl -f http://localhost:8000/health &>/dev/null && ! curl -f http://localhost:8000/ &>/dev/null; then
        echo "⚠️  Backend doesn't seem to be running on port 8000"
        echo "   SSL setup may fail. Please start your backend first."
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Skipping SSL setup. Run this later:"
            echo "  sudo certbot --nginx -d $DOMAIN"
            exit 0
        fi
    fi

    # Get SSL certificate
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --register-unsafely-without-email || \
    sudo certbot --nginx -d $DOMAIN

    if [ $? -eq 0 ]; then
        echo "✅ SSL certificate installed!"
        echo ""
        echo "Your backend is now accessible at:"
        echo "  🌐 https://$DOMAIN"
        echo "  🏥 https://$DOMAIN/health"
        echo "  📚 https://$DOMAIN/docs"
    else
        echo "❌ SSL setup failed"
        echo ""
        echo "Common issues:"
        echo "1. DNS not propagated yet - wait 5-10 minutes and try:"
        echo "   sudo certbot --nginx -d $DOMAIN"
        echo ""
        echo "2. Backend not running - start it first, then run:"
        echo "   sudo certbot --nginx -d $DOMAIN"
        echo ""
        echo "3. Port 80 blocked - check firewall:"
        echo "   sudo ufw allow 80/tcp"
        echo "   sudo ufw allow 443/tcp"
    fi
else
    echo ""
    echo "Skipping SSL setup for now."
    echo "Your backend is accessible at:"
    echo "  🌐 http://$DOMAIN"
    echo "  🏥 http://$DOMAIN/health"
    echo "  📚 http://$DOMAIN/docs"
    echo ""
    echo "To setup SSL later, run:"
    echo "  sudo certbot --nginx -d $DOMAIN"
fi

# Setup auto-renewal
if command -v certbot &> /dev/null; then
    echo ""
    echo "Setting up SSL auto-renewal..."

    # Test auto-renewal
    sudo certbot renew --dry-run 2>/dev/null || true

    echo "✅ Auto-renewal configured (certbot.timer)"
fi

# Update firewall
echo ""
echo "Updating firewall rules..."
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

echo ""
echo "========================================="
echo "✅ Domain Setup Complete!"
echo "========================================="
echo ""
echo "Domain: $DOMAIN"
echo "Droplet IP: $DROPLET_IP"
echo ""
echo "Backend accessible at:"
if [ -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
    echo "  🔒 https://$DOMAIN (SSL secured)"
    echo "  🏥 https://$DOMAIN/health"
    echo "  📚 https://$DOMAIN/docs"
else
    echo "  🌐 http://$DOMAIN"
    echo "  🏥 http://$DOMAIN/health"
    echo "  📚 http://$DOMAIN/docs"
fi
echo ""
echo "Nginx logs:"
echo "  sudo tail -f /var/log/nginx/access.log"
echo "  sudo tail -f /var/log/nginx/error.log"
echo ""
echo "Backend logs:"
echo "  docker logs -f ai-video-backend"
echo ""
