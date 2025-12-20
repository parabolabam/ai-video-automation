# Backend Deployment - Quick Start Guide

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         DEPLOYMENT FLOW                         │
└─────────────────────────────────────────────────────────────────┘

  Developer                 GitHub                    Digital Ocean
     │                        │                             │
     │  git push main        │                             │
     ├──────────────────────>│                             │
     │                        │                             │
     │                   ┌────▼─────┐                      │
     │                   │ GitHub   │                      │
     │                   │ Actions  │                      │
     │                   └────┬─────┘                      │
     │                        │                             │
     │                   Build Docker                       │
     │                   Image (Python)                     │
     │                        │                             │
     │                   ┌────▼─────┐                      │
     │                   │  GHCR    │                      │
     │                   │  (Image  │                      │
     │                   │  Storage)│                      │
     │                   └────┬─────┘                      │
     │                        │                             │
     │                     SSH to ────────────────────────> │
     │                     Droplet                          │
     │                        │                        ┌────▼─────┐
     │                        │                        │  Pull    │
     │                        │                        │  Image   │
     │                        │                        └────┬─────┘
     │                        │                             │
     │                        │                        Run Docker
     │                        │                        Container
     │                        │                             │
     │                        │ <─── Health Check ─────────┤
     │                        │                             │
     │ <─── Deployment OK ────┤                             │
     │                        │                             │
```

## 5-Minute Setup

### 1. On Your Droplet (One-Time)

```bash
# Upload setup script
scp scripts/setup-backend-droplet.sh user@YOUR_DROPLET_IP:~/

# SSH and run
ssh user@YOUR_DROPLET_IP
bash setup-backend-droplet.sh
```

The script will:
- ✅ Install Docker
- ✅ Create `/opt/ai-video-automation/` structure
- ✅ Setup `.env` file
- ✅ Configure firewall
- ✅ Login to GitHub Container Registry

### 2. Generate SSH Key for GitHub Actions

```bash
# On droplet
ssh-keygen -t ed25519 -f ~/.ssh/github_actions -N ''
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys

# Copy this for GitHub secrets
cat ~/.ssh/github_actions
```

### 3. Create GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Generate new token (classic)
3. Name: `Digital Ocean Deployment`
4. Scope: ✅ `read:packages`
5. **Copy the token**

### 4. Add GitHub Repository Secrets

Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions`

Click "New repository secret" for each:

| Name | Value | Where to Get |
|------|-------|--------------|
| `DO_DROPLET_IP` | `123.456.789.0` | Your droplet's IP |
| `DO_DROPLET_USER` | `ubuntu` or `root` | Your SSH username |
| `DO_SSH_PRIVATE_KEY` | `-----BEGIN OPENSSH...` | Output of `cat ~/.ssh/github_actions` |

### 5. Deploy!

```bash
git add .
git commit -m "feat: setup deployment"
git push origin main
```

Watch deployment: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`

## What Gets Built

**Docker Image**: `ghcr.io/YOUR_USERNAME/YOUR_REPO/backend:latest`

**Contains**:
- Python 3.13
- FastAPI application
- All dependencies from `pyproject.toml`
- FFmpeg (for video processing)

## Verify Deployment

### From Browser

```
http://YOUR_DROPLET_IP:8000          → API Root
http://YOUR_DROPLET_IP:8000/health   → Health Check
http://YOUR_DROPLET_IP:8000/docs     → API Documentation
```

### From Command Line

```bash
# Health check
curl http://YOUR_DROPLET_IP:8000/health

# View API docs
curl http://YOUR_DROPLET_IP:8000/docs
```

### On Droplet

```bash
# Check status
/opt/ai-video-automation/status.sh

# View logs
/opt/ai-video-automation/logs.sh

# Restart backend
/opt/ai-video-automation/restart.sh
```

## How Automatic Deployment Works

1. **You push code** to `main` branch
2. **GitHub Actions triggers** (`.github/workflows/deploy-backend.yml`)
3. **Build job runs**:
   - Checks out code
   - Builds Docker image
   - Pushes to GitHub Container Registry
4. **Deploy job runs**:
   - SSHs into droplet
   - Pulls latest image from GHCR
   - Stops old container
   - Starts new container
   - Runs health check
5. **You get notified** (check Actions tab)

## Common Commands

### On Your Droplet

```bash
# View container status
docker ps

# View logs
docker logs ai-video-backend

# Follow logs in real-time
docker logs -f ai-video-backend

# Restart
docker restart ai-video-backend

# Stop
docker stop ai-video-backend

# Start
docker start ai-video-backend

# Shell into container
docker exec -it ai-video-backend bash
```

### On Your Local Machine

```bash
# Trigger deployment
git push origin main

# View deployment status
# Go to: https://github.com/YOUR_REPO/actions

# Test from your machine
curl http://YOUR_DROPLET_IP:8000/health
```

## Troubleshooting

### Deployment Failed in GitHub Actions

1. Check Actions tab: `https://github.com/YOUR_REPO/actions`
2. Click failed workflow
3. Review logs for errors
4. Common issues:
   - SSH key incorrect → Re-add `DO_SSH_PRIVATE_KEY`
   - Droplet IP wrong → Check `DO_DROPLET_IP`
   - Permissions issue → Verify SSH key added to `authorized_keys`

### Backend Not Responding

```bash
# On droplet
docker logs ai-video-backend

# Check if running
docker ps | grep ai-video-backend

# Restart
docker restart ai-video-backend
```

### Can't Access from Browser

1. Check firewall:
   ```bash
   sudo ufw status
   ```
2. Port 8000 should be open
3. Try from droplet first:
   ```bash
   curl http://localhost:8000/health
   ```

## File Locations

```
/opt/ai-video-automation/
├── .env              # Environment variables (API keys, etc.)
├── data/             # Persistent data (videos, files)
├── logs/             # Application logs
├── status.sh         # Quick status check
├── logs.sh           # View logs
└── restart.sh        # Restart backend
```

## Environment Variables

Edit `.env` on droplet:

```bash
nano /opt/ai-video-automation/.env
```

Required:
- `KIE_API_KEY` - Your KIE API key
- `OPENAI_API_KEY` - Your OpenAI API key
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key

After editing, restart:
```bash
docker restart ai-video-backend
```

## GitHub Container Registry

Your images are stored at:
```
https://github.com/YOUR_USERNAME/YOUR_REPO/packages
```

**Make Package Public** (recommended):
1. Go to package settings
2. Change visibility to Public
3. This allows easier pulls without authentication

## Next Steps

- ✅ **Setup SSL/TLS**: Use nginx reverse proxy with Let's Encrypt
- ✅ **Custom Domain**: Point domain to droplet IP
- ✅ **Monitoring**: Setup Grafana/Prometheus
- ✅ **Backups**: Automated backups of `/opt/ai-video-automation/data`
- ✅ **Scaling**: Deploy to multiple droplets with load balancer

## Support

- 📖 Full docs: See `DEPLOYMENT.md`
- 🐛 Issues: GitHub Issues
- 📝 Logs: `/opt/ai-video-automation/logs.sh`

---

**That's it!** Your backend is now auto-deploying on every push to `main`. 🚀
