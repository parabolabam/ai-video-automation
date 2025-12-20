#!/bin/bash

# Setup script for Digital Ocean Droplet
# Run this script on your droplet to prepare it for deployments

set -e

echo "=== AI Video Automation - Droplet Setup ==="
echo ""

# Update system
echo "1. Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "2. Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker installed successfully"
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "3. Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installed successfully"
else
    echo "Docker Compose already installed"
fi

# Create deployment directories
echo "4. Creating deployment directories..."
sudo mkdir -p /opt/ai-video-automation/{backend,frontend,data}
sudo chown -R $USER:$USER /opt/ai-video-automation

# Create .env file template
echo "5. Creating .env template..."
cat > /opt/ai-video-automation/.env.template << 'EOF'
# API Keys
KIE_API_KEY=your_kie_api_key
OPENAI_API_KEY=your_openai_api_key

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# YouTube Configuration (optional)
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_REFRESH_TOKEN=

# Video Configuration
VIDEO_OUTPUT_DIR=/data/videos
VIDEO_DURATION=60
VIDEO_QUALITY=1080
KIE_MODEL=llama-3.3-70b

# Application Settings
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
EOF

echo ""
echo "6. Please create your .env file:"
echo "   cp /opt/ai-video-automation/.env.template /opt/ai-video-automation/.env"
echo "   nano /opt/ai-video-automation/.env"
echo ""

# Setup nginx (optional reverse proxy)
read -p "Do you want to install Nginx as a reverse proxy? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "7. Installing Nginx..."
    sudo apt-get install -y nginx

    # Create nginx config
    sudo tee /etc/nginx/sites-available/ai-video-automation > /dev/null << 'NGINX_EOF'
server {
    listen 80;
    server_name your_domain.com;  # Change this to your domain

    client_max_body_size 100M;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeout for long-running operations
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # WebSocket support for streaming
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
NGINX_EOF

    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/ai-video-automation /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default

    # Test and restart nginx
    sudo nginx -t
    sudo systemctl restart nginx
    sudo systemctl enable nginx

    echo "Nginx configured successfully!"
    echo "Update server_name in /etc/nginx/sites-available/ai-video-automation with your domain"
fi

# Setup firewall
echo "8. Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Setup log rotation
echo "9. Setting up log rotation..."
sudo tee /etc/logrotate.d/ai-video-automation > /dev/null << 'EOF'
/opt/ai-video-automation/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 $USER $USER
    sharedscripts
}
EOF

mkdir -p /opt/ai-video-automation/logs

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "1. Configure your .env file: nano /opt/ai-video-automation/.env"
echo "2. Add GitHub Container Registry credentials (if using private repos)"
echo "3. Configure GitHub Actions secrets in your repository"
echo "4. Push to main branch to trigger deployment"
echo ""
echo "Deployment paths:"
echo "  Backend:  /opt/ai-video-automation/backend"
echo "  Frontend: /opt/ai-video-automation/frontend"
echo "  Data:     /opt/ai-video-automation/data"
echo "  Logs:     /opt/ai-video-automation/logs"
echo ""
