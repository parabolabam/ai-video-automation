#!/bin/bash

# One-time setup script for Digital Ocean Droplet - Backend Only
# Run this on your droplet before the first deployment

set -e

echo "========================================="
echo "AI Video Automation - Backend Setup"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please run as normal user (not root)"
    echo "This script will use sudo when needed"
    exit 1
fi

# Update system
echo "1. Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker if not present
echo "2. Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker installed"
    echo "⚠️  You may need to log out and back in for docker group to take effect"
else
    echo "✅ Docker already installed"
fi

# Install additional tools
echo "3. Installing additional tools..."
sudo apt-get install -y git curl jq

# Create deployment structure
echo "4. Creating deployment directories..."
sudo mkdir -p /opt/ai-video-automation/{data,logs,repo}
sudo chown -R $USER:$USER /opt/ai-video-automation

# Create .env file template
echo "5. Creating .env template..."
cat > /opt/ai-video-automation/.env << 'EOF'
# API Keys
KIE_API_KEY=your_kie_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

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
echo "========================================="
echo "⚠️  IMPORTANT: Configure your .env file"
echo "========================================="
echo "Edit: /opt/ai-video-automation/.env"
echo ""
echo "Required variables:"
echo "  - KIE_API_KEY"
echo "  - OPENAI_API_KEY"
echo "  - SUPABASE_URL"
echo "  - SUPABASE_KEY"
echo ""
read -p "Press Enter to open .env in nano editor..." -r
nano /opt/ai-video-automation/.env

# Configure firewall
echo ""
echo "6. Configuring firewall..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 22/tcp comment 'SSH'
    sudo ufw allow 8000/tcp comment 'Backend API'
    sudo ufw --force enable
    echo "✅ Firewall configured (ports 22, 8000 open)"
else
    echo "⚠️  UFW not found - configure firewall manually"
fi

# Setup log rotation
echo "7. Setting up log rotation..."
sudo tee /etc/logrotate.d/ai-video-automation > /dev/null << 'LOGROTATE_EOF'
/opt/ai-video-automation/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
    sharedscripts
    postrotate
        docker kill -s USR1 ai-video-backend 2>/dev/null || true
    endscript
}
LOGROTATE_EOF

# Create helpful management scripts
echo "8. Creating management scripts..."

# Status check script
cat > /opt/ai-video-automation/status.sh << 'STATUS_EOF'
#!/bin/bash
echo "=== Backend Status ==="
docker ps -f name=ai-video-backend --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "=== Resource Usage ==="
docker stats --no-stream -f name=ai-video-backend --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
echo ""
echo "=== Health Check ==="
curl -f http://localhost:8000/health && echo "✅ Healthy" || echo "❌ Unhealthy"
STATUS_EOF

# Logs script
cat > /opt/ai-video-automation/logs.sh << 'LOGS_EOF'
#!/bin/bash
docker logs -f --tail 100 ai-video-backend
LOGS_EOF

# Restart script
cat > /opt/ai-video-automation/restart.sh << 'RESTART_EOF'
#!/bin/bash
echo "Restarting backend..."
docker restart ai-video-backend
sleep 5
docker logs --tail 20 ai-video-backend
RESTART_EOF

chmod +x /opt/ai-video-automation/*.sh

echo ""
echo "========================================="
echo "✅ Droplet Setup Complete!"
echo "========================================="
echo ""
echo "Directory structure:"
echo "  /opt/ai-video-automation/"
echo "    ├── .env          (environment variables)"
echo "    ├── data/         (video output)"
echo "    ├── logs/         (application logs)"
echo "    ├── repo/         (git repository - auto-created)"
echo "    ├── status.sh     (check backend status)"
echo "    ├── logs.sh       (view backend logs)"
echo "    └── restart.sh    (restart backend)"
# Setup GitHub Container Registry authentication
echo ""
echo "9. Setting up GitHub Container Registry authentication..."
read -p "Enter your GitHub username: " GITHUB_USER
read -sp "Enter your GitHub Personal Access Token (with read:packages scope): " GITHUB_TOKEN
echo ""

# Test GHCR login
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin

if [ $? -eq 0 ]; then
    echo "✅ GitHub Container Registry authentication successful"

    # Store credentials for future use
    echo "Creating credential helper script..."
    mkdir -p ~/.docker
    cat > ~/.docker/config.json.backup << EOF
{
  "auths": {
    "ghcr.io": {
      "auth": "$(echo -n "$GITHUB_USER:$GITHUB_TOKEN" | base64)"
    }
  }
}
EOF
    echo "Note: Credentials stored. GitHub Actions will provide fresh tokens on each deployment."
else
    echo "❌ GitHub Container Registry login failed"
    echo "You'll need to login manually before deployment works:"
    echo "  echo YOUR_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin"
fi

echo ""
echo "========================================="
echo "Next Steps"
echo "========================================="
echo ""
echo "1. Configure GitHub Secrets in your repository:"
echo "   Settings → Secrets and variables → Actions → New repository secret"
echo ""
echo "   Required secrets:"
echo "   - DO_DROPLET_IP: $(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_DROPLET_IP')"
echo "   - DO_DROPLET_USER: $USER"
echo "   - DO_SSH_PRIVATE_KEY: (see step 2 below)"
echo ""
echo "2. Generate SSH key for GitHub Actions:"
echo "   ssh-keygen -t ed25519 -f ~/.ssh/github_actions -N ''"
echo "   cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys"
echo "   chmod 600 ~/.ssh/authorized_keys"
echo ""
echo "   Copy this private key for DO_SSH_PRIVATE_KEY secret:"
echo "   cat ~/.ssh/github_actions"
echo ""
echo "3. Make GitHub Container Registry package public (recommended):"
echo "   After first deployment, go to:"
echo "   https://github.com/YOUR_USERNAME/YOUR_REPO/packages"
echo "   → Click on 'backend' package → Package settings"
echo "   → Change visibility to Public (or manage access)"
echo ""
echo "4. Test deployment:"
echo "   git push origin main"
echo ""
echo "5. Monitor deployment:"
echo "   Watch GitHub Actions: https://github.com/YOUR_REPO/actions"
echo "   Or on droplet: /opt/ai-video-automation/logs.sh"
echo ""
echo "Useful commands:"
echo "  Status:  /opt/ai-video-automation/status.sh"
echo "  Logs:    /opt/ai-video-automation/logs.sh"
echo "  Restart: /opt/ai-video-automation/restart.sh"
echo ""
