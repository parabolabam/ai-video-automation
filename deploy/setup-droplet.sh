#!/bin/bash
set -e

# =============================================================================
# AI Video Automation - Digital Ocean Droplet Setup Script
# =============================================================================
# This script sets up a fresh Ubuntu droplet for deployment
# Run as root or with sudo
# =============================================================================

echo "=== AI Video Automation - Server Setup ==="

# Update system
echo ">>> Updating system packages..."
apt-get update && apt-get upgrade -y

# Install required packages
echo ">>> Installing required packages..."
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw \
    fail2ban

# Install Docker
echo ">>> Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh

    # Add current user to docker group (if not root)
    if [ "$SUDO_USER" ]; then
        usermod -aG docker $SUDO_USER
    fi
fi

# Install Docker Compose
echo ">>> Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Configure firewall
echo ">>> Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure fail2ban
echo ">>> Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Create app directory
echo ">>> Creating application directory..."
mkdir -p /opt/ai-video-automation
cd /opt/ai-video-automation

# Create data directories
mkdir -p data certbot/conf certbot/www

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Clone your repository to /opt/ai-video-automation"
echo "2. Copy .env.example to .env and fill in your API keys"
echo "3. Run: docker-compose -f docker-compose.prod.yml up -d --build"
echo ""
echo "Your server IP can be used with nip.io for a free domain:"
echo "  http://YOUR_IP.nip.io"
echo ""
