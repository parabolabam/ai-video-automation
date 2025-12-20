# Backend Deployment Guide - Digital Ocean

This guide covers deploying the Python backend to your Digital Ocean droplet using GitHub Actions and GitHub Container Registry.

## Architecture

- **Backend**: FastAPI + Uvicorn (Python 3.13)
- **Port**: 8000
- **Build**: GitHub Actions builds Docker image and pushes to GitHub Container Registry (GHCR)
- **Deployment**: Droplet pulls image from GHCR and runs container
- **CI/CD**: Fully automated via GitHub Actions (auto-deploy on push to main)

## Quick Start Summary

1. **Setup droplet**: Run `setup-backend-droplet.sh` on your droplet
2. **Create GitHub token**: Settings → Developer settings → Personal access tokens → `read:packages`
3. **Add GitHub secrets**: `DO_DROPLET_IP`, `DO_DROPLET_USER`, `DO_SSH_PRIVATE_KEY`
4. **Deploy**: `git push origin main`
5. **Monitor**: Check GitHub Actions tab

That's it! Full details below.

---

## Prerequisites

1. A Digital Ocean droplet (Ubuntu 20.04+ recommended)
2. SSH access to your droplet
3. GitHub repository with Actions enabled
4. GitHub account (for Container Registry)

## One-Time Setup

### Step 1: Setup Your Droplet

Copy the setup script to your droplet and run it:

```bash
# On your local machine
scp scripts/setup-backend-droplet.sh your-user@your-droplet-ip:~/

# SSH into your droplet
ssh your-user@your-droplet-ip

# Run the setup script
bash setup-backend-droplet.sh
```

This script will:
- Install Docker
- Create directory structure at `/opt/ai-video-automation/`
- Create `.env` template
- Configure firewall (opens ports 22, 8000)
- Setup log rotation
- Create management scripts

### Step 2: Configure Environment Variables

Edit the `.env` file on your droplet:

```bash
nano /opt/ai-video-automation/.env
```

Required variables:
```env
# API Keys
KIE_API_KEY=your_actual_kie_api_key
OPENAI_API_KEY=your_actual_openai_api_key

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Optional: YouTube
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_REFRESH_TOKEN=

# Video Configuration
VIDEO_OUTPUT_DIR=/data/videos
VIDEO_DURATION=60
VIDEO_QUALITY=1080
KIE_MODEL=llama-3.3-70b
```

### Step 3: Create GitHub Personal Access Token

You need a GitHub token for the droplet to pull images from GitHub Container Registry:

1. Go to GitHub: **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Give it a name: `Digital Ocean Deployment`
4. Select scopes:
   - ✅ `read:packages` (Download packages from GitHub Package Registry)
5. Click **Generate token**
6. **Copy the token** - you'll need it in the next step

### Step 4: Setup GitHub Actions SSH Access

Generate a dedicated SSH key for GitHub Actions:

```bash
# On your droplet
ssh-keygen -t ed25519 -f ~/.ssh/github_actions -N ''
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Display the private key (copy this for GitHub secrets)
cat ~/.ssh/github_actions
```

### Step 5: Configure GitHub Repository Secrets

Go to your GitHub repository: `Settings → Secrets and variables → Actions → New repository secret`

Add these secrets:

| Secret Name | Value | How to Get |
|------------|-------|------------|
| `DO_DROPLET_IP` | Your droplet's IP address | Run `curl ifconfig.me` on droplet |
| `DO_DROPLET_USER` | SSH username (e.g., `ubuntu`, `root`) | Usually `ubuntu` or `root` |
| `DO_SSH_PRIVATE_KEY` | SSH private key | Content of `~/.ssh/github_actions` |
| `DO_SSH_PORT` | SSH port (optional, defaults to 22) | Usually 22 |

Optional secret:
- `DO_SSH_PORT`: Custom SSH port if not using 22

## How It Works

### Deployment Workflow

Every push to the `main` branch automatically triggers this workflow:

**GitHub Actions (Build Job)**:
1. ✅ Checkout code from repository
2. ✅ Build Docker image using GitHub runners
3. ✅ Push image to GitHub Container Registry (ghcr.io)
4. ✅ Cache layers for faster future builds

**GitHub Actions (Deploy Job)**:
1. ✅ SSH into your Digital Ocean droplet
2. ✅ Login to GitHub Container Registry
3. ✅ Pull latest Docker image from GHCR
4. ✅ Stop and remove old container
5. ✅ Start new container with latest image
6. ✅ Run health checks
7. ✅ Clean up old images

**Benefits of this approach**:
- 🚀 Faster deployments (no building on droplet)
- 💾 Less disk space used on droplet
- 🔄 Reusable images (can deploy to multiple servers)
- 📦 Centralized image storage on GitHub
- ⚡ Better resource usage (GitHub builds, droplet just runs)

### Triggering Deployment

**Automatic** - Push to main branch:
```bash
git add .
git commit -m "feat: add new feature"
git push origin main
```

### Manual Deployment

You can also trigger deployment manually:

1. Go to: `Actions → Deploy Backend to Digital Ocean → Run workflow`
2. Select branch: `main`
3. Click "Run workflow"

## Monitoring & Management

### On Your Droplet

Convenient scripts are available at `/opt/ai-video-automation/`:

```bash
# Check backend status
/opt/ai-video-automation/status.sh

# View real-time logs
/opt/ai-video-automation/logs.sh

# Restart backend
/opt/ai-video-automation/restart.sh
```

### Manual Docker Commands

```bash
# View running containers
docker ps

# View backend logs
docker logs ai-video-backend

# Follow logs in real-time
docker logs -f ai-video-backend

# Restart backend
docker restart ai-video-backend

# Stop backend
docker stop ai-video-backend

# Start backend
docker start ai-video-backend

# Remove backend (for clean rebuild)
docker rm -f ai-video-backend
```

### Health Check

Check if backend is running:

```bash
# From droplet
curl http://localhost:8000/health

# From external
curl http://YOUR_DROPLET_IP:8000/health
```

## Accessing the Backend

- **API Endpoint**: `http://YOUR_DROPLET_IP:8000`
- **Health Check**: `http://YOUR_DROPLET_IP:8000/health`
- **API Docs**: `http://YOUR_DROPLET_IP:8000/docs` (FastAPI auto-generated)

## Directory Structure on Droplet

```
/opt/ai-video-automation/
├── .env              # Environment variables (KEEP SECURE!)
├── data/             # Video output and persistent data
├── logs/             # Application logs
├── repo/             # Git repository (auto-managed by GitHub Actions)
├── status.sh         # Quick status check
├── logs.sh           # View logs
└── restart.sh        # Restart backend
```

## Troubleshooting

### Deployment Failed

1. Check GitHub Actions logs:
   - Go to `Actions` tab in your repository
   - Click on the failed workflow run
   - Review the logs

2. Check backend logs on droplet:
   ```bash
   docker logs ai-video-backend
   ```

### Backend Not Responding

1. Check if container is running:
   ```bash
   docker ps | grep ai-video-backend
   ```

2. Check logs for errors:
   ```bash
   docker logs ai-video-backend --tail 100
   ```

3. Restart the backend:
   ```bash
   docker restart ai-video-backend
   ```

### Port Already in Use

If port 8000 is already in use:

```bash
# Find what's using the port
sudo lsof -i :8000

# Kill the process (replace PID)
kill -9 PID

# Or stop the container
docker stop ai-video-backend
```

### Environment Variables Not Loading

1. Check `.env` file exists:
   ```bash
   cat /opt/ai-video-automation/.env
   ```

2. Verify Docker can access it:
   ```bash
   docker exec ai-video-backend env | grep KIE_API_KEY
   ```

### Out of Disk Space

Clean up old Docker images:

```bash
# Remove unused images
docker image prune -a

# See disk usage
docker system df

# Clean everything (CAREFUL!)
docker system prune -a
```

### SSH Connection Issues

1. Verify SSH key is correct:
   ```bash
   ssh -i ~/.ssh/github_actions your-user@your-droplet-ip
   ```

2. Check GitHub secret `DO_SSH_PRIVATE_KEY` includes the full key:
   - Should start with `-----BEGIN OPENSSH PRIVATE KEY-----`
   - Should end with `-----END OPENSSH PRIVATE KEY-----`

3. Verify firewall allows SSH:
   ```bash
   sudo ufw status
   ```

## Workflow Customization

The workflow file is located at: `.github/workflows/deploy-backend.yml`

### Change Deployment Branch

Edit the `on.push.branches` section:

```yaml
on:
  push:
    branches:
      - production  # Deploy from 'production' branch instead
```

### Add Deployment Notifications

Add a notification step to the workflow (e.g., Slack, Discord, email).

### Resource Limits

Adjust Docker container resources in the workflow:

```yaml
--memory="4g"    # Increase memory to 4GB
--cpus="4"       # Use 4 CPU cores
```

## Security Best Practices

1. **Never commit `.env` files** - Already in `.gitignore`
2. **Use GitHub Secrets** for sensitive data
3. **Rotate API keys** regularly
4. **Keep system updated**: `sudo apt-get update && sudo apt-get upgrade`
5. **Monitor access logs**: `sudo tail -f /var/log/auth.log`
6. **Setup firewall**: Only open necessary ports
7. **Use SSH keys**, disable password authentication

## Rolling Back

If a deployment breaks something, you can rollback to a previous version:

### Method 1: Rollback via GitHub (Recommended)

1. Find the working commit:
   ```bash
   git log --oneline -10
   ```

2. Revert to that commit:
   ```bash
   git revert <bad-commit-hash>
   # or
   git reset --hard <good-commit-hash>
   git push origin main --force
   ```

3. This will trigger a new deployment with the old code

### Method 2: Manual Rollback on Droplet

Pull a previous image from GHCR:

```bash
# On your droplet
# List available images
docker images | grep ghcr.io

# Stop current container
docker stop ai-video-backend
docker rm ai-video-backend

# Find previous image tag from GitHub packages:
# https://github.com/YOUR_USERNAME/YOUR_REPO/packages

# Pull specific version (replace with actual SHA or tag)
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO/backend:main-abc123

# Run previous version
docker run -d \
  --name ai-video-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /opt/ai-video-automation/data:/data \
  -v /opt/ai-video-automation/.env:/app/.env:ro \
  --env-file /opt/ai-video-automation/.env \
  --memory="2g" \
  --cpus="2" \
  ghcr.io/YOUR_USERNAME/YOUR_REPO/backend:main-abc123 \
  uv run uvicorn features.platform.server:app --host 0.0.0.0 --port 8000
```

### View Available Image Versions

Check GitHub Container Registry for all available versions:
- Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/packages`
- Click on the `backend` package
- See all tagged versions

## Scaling & Performance

### Vertical Scaling (Upgrade Droplet)

1. Power off droplet
2. Resize in Digital Ocean console
3. Power on
4. No code changes needed

### Horizontal Scaling (Multiple Instances)

For load balancing across multiple droplets:

1. Setup load balancer (nginx, HAProxy, or DO Load Balancer)
2. Deploy to multiple droplets
3. Update workflow to deploy to all droplets

### Database Connection Pooling

If using Supabase heavily, consider connection pooling in `features/platform/server.py`.

## Support

- **GitHub Issues**: Report problems in the repository
- **Logs**: Check `/opt/ai-video-automation/logs/`
- **Docker Logs**: `docker logs ai-video-backend`
- **System Logs**: `journalctl -u docker`

## Next Steps

After backend is deployed:

1. Test API endpoints: `curl http://YOUR_IP:8000/docs`
2. Setup monitoring (optional): Prometheus, Grafana, etc.
3. Setup SSL/TLS with nginx reverse proxy (optional)
4. Configure custom domain (optional)
5. Setup automated backups for `/opt/ai-video-automation/data/`
