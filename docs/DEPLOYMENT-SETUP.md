# Deployment Setup Guide

This guide explains how to set up automated deployments for both the backend and frontend using GitHub Actions.

---

## Overview

The deployment system uses:
- **GitHub Actions** - CI/CD automation
- **GitHub Container Registry (GHCR)** - Docker image storage
- **GitHub Secrets** - Secure environment variable management
- **Digital Ocean Droplet** - Hosting server
- **Separate Workflows** - Independent backend and frontend deployments

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Developer                            │
│              git push origin main                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      GitHub Actions                          │
│                                                              │
│  ┌──────────────────────┐    ┌─────────────────────────┐   │
│  │  Backend Workflow    │    │  Frontend Workflow      │   │
│  │  (deploy-backend.yml)│    │  (deploy-frontend.yml)  │   │
│  │                      │    │                         │   │
│  │  • Build Docker      │    │  • Build Docker         │   │
│  │  • Push to GHCR      │    │  • Push to GHCR         │   │
│  │  • SSH to droplet    │    │  • SSH to droplet       │   │
│  │  • Deploy backend    │    │  • Deploy frontend      │   │
│  └──────────────────────┘    └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 GitHub Container Registry                    │
│                                                              │
│  ghcr.io/parabolabam/ai-video-automation/backend:latest     │
│  ghcr.io/parabolabam/ai-video-automation/frontend:latest    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Digital Ocean Droplet                      │
│                     134.199.244.59                           │
│                                                              │
│  ┌────────────────────┐         ┌──────────────────────┐   │
│  │  ai-video-backend  │         │  ai-video-frontend   │   │
│  │  Port: 8000        │         │  Port: 3000          │   │
│  │  Env: From secrets │         │  Env: From secrets   │   │
│  └────────────────────┘         └──────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Nginx Reverse Proxy                 │  │
│  │  vingine.duckdns.org → backend:8000                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Configure GitHub Secrets

All environment variables are managed through GitHub Secrets. No `.env` files are copied to the server.

### 1.1 Add Deployment Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

#### Required Deployment Secrets:

```bash
# Digital Ocean Connection
DO_DROPLET_IP=134.199.244.59
DO_DROPLET_USER=root
DO_SSH_PRIVATE_KEY=<your_ssh_private_key_content>
DO_SSH_PORT=22  # Optional, defaults to 22
```

### 1.2 Add Backend Environment Secrets

#### Required Backend Secrets:

```bash
# API Keys (Required)
KIE_API_KEY=<your_kie_api_key>
OPENAI_API_KEY=<your_openai_api_key>

# Supabase (Required for authentication)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=<your_supabase_anon_key>
SUPABASE_SERVICE_KEY=<your_supabase_service_role_key>

# YouTube OAuth (Required if using YouTube features)
YOUTUBE_CLIENT_ID=<your_youtube_client_id>
YOUTUBE_CLIENT_SECRET=<your_youtube_client_secret>
YOUTUBE_REFRESH_TOKEN=<your_youtube_refresh_token>

# TikTok OAuth (Optional)
TIKTOK_CLIENT_KEY=<your_tiktok_client_key>
TIKTOK_CLIENT_SECRET=<your_tiktok_client_secret>

# Instagram (Optional)
IG_USER_ID=<your_instagram_user_id>
IG_ACCESS_TOKEN=<your_instagram_access_token>
```

#### Optional Backend Secrets (with defaults):

```bash
# Video Configuration
VIDEO_DURATION=8
VIDEO_QUALITY=high
VEO_MAX_WAIT_TIME=600
KIE_MODEL=veo3_fast
EXTENDED_MODE=true
VIDEO_SCENES=4

# AI Configuration
OPENAI_MODEL=gpt-4o
LOG_LEVEL=INFO

# Audio Configuration
ENABLE_VOICEOVER=true
TTS_VOICE=nova
TTS_MODEL=tts-1-hd

# Subtitle Configuration
ENABLE_SUBTITLES=true
SUBTITLE_FONT_SIZE=28
SUBTITLE_WORDS_PER_LINE=5
```

### 1.3 Add Frontend Environment Secrets

#### Required Frontend Secrets:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=https://vingine.duckdns.org

# Supabase (Required for authentication)
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your_supabase_anon_key>
```

---

## Step 2: Workflow Triggers

### Backend Workflow (`deploy-backend.yml`)

Triggers on push to `main` branch when these paths change:
- `features/**` - Backend Python code
- `pyproject.toml` - Python dependencies
- `Dockerfile` - Backend Docker configuration
- `main.py` or `main_v2.py` - Entry points
- `.github/workflows/deploy-backend.yml` - Workflow file

### Frontend Workflow (`deploy-frontend.yml`)

Triggers on push to `main` branch when these paths change:
- `web/**` - Frontend Next.js code
- `.github/workflows/deploy-frontend.yml` - Workflow file

**This means:**
- Changing only backend code will deploy only backend
- Changing only frontend code will deploy only frontend
- Changing both will deploy both (in parallel)

---

## Step 3: How Deployments Work

### Backend Deployment Process

1. **Build Phase:**
   - Checkout code
   - Build Docker image for Python FastAPI backend
   - Push image to `ghcr.io/parabolabam/ai-video-automation/backend:latest`

2. **Deploy Phase:**
   - SSH into Digital Ocean droplet
   - Pull latest image from GHCR
   - Stop old `ai-video-backend` container
   - Start new container with environment variables from GitHub secrets
   - Health check at `http://localhost:8000/health`
   - Clean up old images

3. **Environment Variables:**
   - All env vars passed as `-e KEY=VALUE` flags
   - No `.env` file needed on server
   - Secrets managed entirely in GitHub

### Frontend Deployment Process

1. **Build Phase:**
   - Checkout code
   - Build Docker image for Next.js frontend
   - Pass `NEXT_PUBLIC_*` vars as build args (baked into build)
   - Push image to `ghcr.io/parabolabam/ai-video-automation/frontend:latest`

2. **Deploy Phase:**
   - SSH into Digital Ocean droplet
   - Pull latest image from GHCR
   - Stop old `ai-video-frontend` container
   - Start new container with runtime env vars
   - Health check at `http://localhost:3000`
   - Clean up old images

3. **Environment Variables:**
   - `NEXT_PUBLIC_*` vars built into image during build
   - Runtime env vars passed as `-e` flags
   - No `.env` file needed on server

---

## Step 4: Testing Deployments

### Test Backend Deployment

1. Make a change to backend code (e.g., `features/platform/server.py`)
2. Commit and push to `main`:
   ```bash
   git add features/platform/server.py
   git commit -m "test: Update backend"
   git push origin main
   ```
3. Check GitHub Actions tab for workflow progress
4. Once complete, verify:
   ```bash
   curl https://vingine.duckdns.org/health
   # Should return: {"status":"ok"}
   ```

### Test Frontend Deployment

1. Make a change to frontend code (e.g., `web/src/app/page.tsx`)
2. Commit and push to `main`:
   ```bash
   git add web/src/app/page.tsx
   git commit -m "test: Update frontend"
   git push origin main
   ```
3. Check GitHub Actions tab for workflow progress
4. Once complete, verify:
   ```bash
   curl http://134.199.244.59:3000
   # Should return HTML
   ```

---

## Step 5: Monitoring Deployments

### View Logs on Droplet

SSH into the droplet and check container logs:

```bash
ssh root@134.199.244.59

# Backend logs
docker logs -f ai-video-backend

# Frontend logs
docker logs -f ai-video-frontend

# Check container status
docker ps -f name=ai-video
```

### View GitHub Actions Logs

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Select the workflow run
4. Click on the job to see detailed logs

---

## Step 6: Rollback Strategy

If a deployment fails, you can rollback to a previous version:

### Rollback Backend

```bash
ssh root@134.199.244.59

# List available images
docker images ghcr.io/parabolabam/ai-video-automation/backend

# Stop current container
docker stop ai-video-backend
docker rm ai-video-backend

# Run previous version (replace <IMAGE_ID> with older image)
docker run -d \
  --name ai-video-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /opt/ai-video-automation/data:/data \
  -e KIE_API_KEY="..." \
  -e OPENAI_API_KEY="..." \
  # ... add all env vars ...
  ghcr.io/parabolabam/ai-video-automation/backend:<IMAGE_ID>
```

### Rollback Frontend

```bash
# Same process as backend
docker stop ai-video-frontend
docker rm ai-video-frontend

docker run -d \
  --name ai-video-frontend \
  --restart unless-stopped \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL="..." \
  # ... add env vars ...
  ghcr.io/parabolabam/ai-video-automation/frontend:<IMAGE_ID>
```

---

## Step 7: Security Best Practices

### Secrets Management

- ✅ **Never commit secrets** to the repository
- ✅ **Use GitHub Secrets** for all sensitive data
- ✅ **Rotate secrets regularly** (API keys, tokens, etc.)
- ✅ **Use service role key** only in backend (not frontend)
- ✅ **Limit secret access** to necessary workflows only

### SSH Security

- ✅ **Use SSH keys** instead of passwords
- ✅ **Dedicated deployment key** (not your personal key)
- ✅ **Restrict key permissions** on droplet
- ✅ **Regular key rotation** every 90 days

### Docker Security

- ✅ **Non-root user** in containers
- ✅ **Resource limits** (memory, CPU)
- ✅ **Read-only mounts** where possible
- ✅ **Regular image updates** for security patches

---

## Step 8: Troubleshooting

### Issue: "Authentication failed - Supabase not configured"

**Cause:** Missing `SUPABASE_SERVICE_KEY` secret

**Solution:**
1. Go to Supabase Dashboard → Settings → API
2. Copy the `service_role` key (NOT anon key)
3. Add as `SUPABASE_SERVICE_KEY` secret in GitHub

### Issue: "Docker login failed"

**Cause:** GitHub token expired or insufficient permissions

**Solution:**
1. Check workflow has `packages: write` permission
2. Verify `GITHUB_TOKEN` is being used correctly
3. Check GHCR settings allow package writes

### Issue: "Health check failed"

**Cause:** Container started but application not responding

**Solution:**
1. SSH into droplet
2. Check container logs: `docker logs ai-video-backend`
3. Verify all required env vars are set
4. Check for Python errors or missing dependencies

### Issue: "Frontend 404 on all routes"

**Cause:** Missing `output: "standalone"` in `next.config.ts`

**Solution:**
- Already configured correctly in `web/next.config.ts`
- If issue persists, rebuild: `npm run build`

---

## Environment Variable Reference

### Backend Required Secrets

| Secret | Description | Example |
|--------|-------------|---------|
| `KIE_API_KEY` | Kie AI API key | `kie_xxx` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-xxx` |
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | `eyJxxx` |
| `DO_DROPLET_IP` | Droplet IP address | `134.199.244.59` |
| `DO_DROPLET_USER` | SSH username | `root` |
| `DO_SSH_PRIVATE_KEY` | SSH private key content | `-----BEGIN...` |

### Frontend Required Secrets

| Secret | Description | Example |
|--------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `https://vingine.duckdns.org` |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key | `eyJxxx` |

---

## Workflow Files

- **Backend:** `.github/workflows/deploy-backend.yml`
- **Frontend:** `.github/workflows/deploy-frontend.yml`

Both workflows:
- Build Docker images on GitHub runners
- Push to GitHub Container Registry
- Deploy to Digital Ocean via SSH
- Inject environment variables from secrets
- Perform health checks
- Clean up old images

---

## Next Steps

1. ✅ Configure all required GitHub secrets
2. ✅ Test backend deployment
3. ✅ Test frontend deployment
4. ✅ Configure Supabase Google OAuth (see `docs/GOOGLE-AUTH-SETUP.md`)
5. ✅ Monitor first production deployment
6. ✅ Set up error tracking (optional: Sentry, LogRocket)
7. ✅ Configure backup strategy for database

---

**Deployment system is now fully automated!** 🎉

Every push to `main` will automatically deploy the changed services with zero manual intervention.
