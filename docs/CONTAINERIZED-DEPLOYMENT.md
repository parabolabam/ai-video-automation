# Fully Containerized Deployment Guide

## Overview

This deployment architecture uses **docker-compose** with separate deployment workflows for each service. No manual SSH scripting or server-side configuration required - everything is containerized and managed via GitHub Actions.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    vingine.duckdns.org                      │
│                         (HTTPS)                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │   Nginx Container            │
          │   (Port 80/443)             │
          │   - SSL termination         │
          │   - Reverse proxy           │
          └──────┬──────────────┬────────┘
                 │              │
       ┌─────────┘              └──────────┐
       │                                   │
       ▼                                   ▼
┌─────────────────┐              ┌──────────────────┐
│ Frontend        │              │ Backend          │
│ Container       │              │ Container        │
│ (Port 3000)     │              │ (Port 8000)      │
│ - Next.js UI    │              │ - FastAPI        │
│ - Server-side   │              │ - Workflows      │
│   rendering     │              │ - Cron scheduler │
└─────────────────┘              └──────────────────┘
```

## Services

### 1. Backend (FastAPI)
- **Image**: `ghcr.io/parabolabam/ai-video-automation/backend:latest`
- **Container**: `ai-video-backend`
- **Port**: 8000 (internal)
- **Purpose**: API server, workflow execution, cron jobs

### 2. Frontend (Next.js)
- **Image**: `ghcr.io/parabolabam/ai-video-automation/frontend:latest`
- **Container**: `ai-video-frontend`
- **Port**: 3000 (internal)
- **Purpose**: Web UI, server-side rendering

### 3. Nginx (Reverse Proxy)
- **Image**: `ghcr.io/parabolabam/ai-video-automation/nginx:latest`
- **Container**: `ai-video-nginx`
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Purpose**: SSL termination, routing, load balancing

## Deployment Workflows

### Backend Deployment
**Workflow**: `.github/workflows/deploy-backend-compose.yml`

**Trigger**: Manual dispatch

**Steps**:
1. Build backend Docker image
2. Push to GitHub Container Registry
3. SSH to droplet
4. Pull latest image
5. Recreate backend container via docker-compose
6. Health check

**Deploy**:
```bash
# Go to GitHub → Actions → Deploy Backend (Docker Compose) → Run workflow
# Select branch: deployment/github-actions-setup
```

### Frontend Deployment
**Workflow**: `.github/workflows/deploy-frontend-compose.yml`

**Trigger**: Manual dispatch

**Steps**:
1. Build frontend Docker image
2. Push to GitHub Container Registry
3. SSH to droplet
4. Pull latest image
5. Recreate frontend container via docker-compose
6. Health check

**Deploy**:
```bash
# Go to GitHub → Actions → Deploy Frontend (Docker Compose) → Run workflow
# Select branch: deployment/github-actions-setup
```

### Nginx Deployment
**Workflow**: `.github/workflows/deploy-nginx.yml`

**Trigger**: Manual dispatch

**Steps**:
1. Build nginx Docker image with configs
2. Push to GitHub Container Registry
3. SSH to droplet
4. Pull latest image
5. Recreate nginx container via docker-compose
6. Test configuration

**Deploy**:
```bash
# Go to GitHub → Actions → Deploy Nginx (Docker Compose) → Run workflow
# Select branch: deployment/github-actions-setup
```

## Initial Setup (One-Time)

### 1. Prepare Droplet

SSH into your Digital Ocean droplet:

```bash
ssh root@134.199.244.59
```

Create application directory:

```bash
mkdir -p /opt/ai-video-automation
cd /opt/ai-video-automation
```

### 2. Setup SSL Certificates

**Option A: Using Certbot (Recommended)**

```bash
# Install certbot
apt-get update
apt-get install -y certbot

# Stop any service on port 80
docker stop ai-video-nginx 2>/dev/null || true

# Get certificate
certbot certonly --standalone \
  -d vingine.duckdns.org \
  --agree-tos \
  --register-unsafely-without-email

# Create volume directory and copy certs
mkdir -p /opt/ai-video-automation/letsencrypt
cp -r /etc/letsencrypt/* /opt/ai-video-automation/letsencrypt/

# Set up auto-renewal
cat > /opt/ai-video-automation/renew-ssl.sh << 'EOF'
#!/bin/bash
docker stop ai-video-nginx
certbot renew --standalone --quiet
cp -r /etc/letsencrypt/* /opt/ai-video-automation/letsencrypt/
docker start ai-video-nginx
EOF

chmod +x /opt/ai-video-automation/renew-ssl.sh

# Add to cron (monthly renewal)
(crontab -l 2>/dev/null; echo "0 0 1 * * /opt/ai-video-automation/renew-ssl.sh") | crontab -
```

**Option B: Self-Signed (Development Only)**

```bash
mkdir -p /opt/ai-video-automation/letsencrypt/live/vingine.duckdns.org
cd /opt/ai-video-automation/letsencrypt/live/vingine.duckdns.org

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout privkey.pem \
  -out fullchain.pem \
  -subj "/CN=vingine.duckdns.org"
```

### 3. Deploy Stack

**Deploy in this order**:

1. **Deploy Backend**:
   - Go to GitHub Actions
   - Run "Deploy Backend (Docker Compose)"
   - Wait for completion

2. **Deploy Frontend**:
   - Go to GitHub Actions
   - Run "Deploy Frontend (Docker Compose)"
   - Wait for completion

3. **Deploy Nginx**:
   - Go to GitHub Actions
   - Run "Deploy Nginx (Docker Compose)"
   - Wait for completion

### 4. Verify Deployment

Check all containers are running:

```bash
cd /opt/ai-video-automation
docker-compose -f docker-compose.prod.yml ps
```

Expected output:
```
NAME                 STATUS              PORTS
ai-video-backend     Up (healthy)        0.0.0.0:8000->8000/tcp
ai-video-frontend    Up (healthy)        0.0.0.0:3000->3000/tcp
ai-video-nginx       Up                  0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

Test services:
```bash
# Backend health
curl http://localhost:8000/health
# {"status":"ok"}

# Frontend
curl http://localhost:3000/
# HTML output

# Nginx routing
curl https://vingine.duckdns.org/health
# {"status":"ok"}

curl https://vingine.duckdns.org/
# HTML output (frontend)
```

## Managing Services

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Restart Services

```bash
# Restart all
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart frontend
docker-compose -f docker-compose.prod.yml restart nginx
```

### Stop/Start Services

```bash
# Stop all
docker-compose -f docker-compose.prod.yml stop

# Start all
docker-compose -f docker-compose.prod.yml start

# Stop specific service
docker-compose -f docker-compose.prod.yml stop backend
```

### Update Single Service

Backend only:
```bash
# GitHub Actions → Deploy Backend (Docker Compose)
```

Frontend only:
```bash
# GitHub Actions → Deploy Frontend (Docker Compose)
```

Nginx only:
```bash
# GitHub Actions → Deploy Nginx (Docker Compose)
```

## Environment Variables

Environment variables are injected during deployment via GitHub Secrets.

**Required secrets** (set in GitHub repository settings):
- `KIE_API_KEY`
- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_KEY`
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`
- `DO_DROPLET_IP`
- `DO_DROPLET_USER`
- `DO_SSH_PRIVATE_KEY`
- `DO_SSH_PORT` (optional, defaults to 22)

The deployment workflows create a `.env` file on the droplet with these values.

## Nginx Configuration

Nginx uses environment variable substitution via `docker-entrypoint.sh`.

**Environment variables**:
- `DOMAIN`: vingine.duckdns.org
- `BACKEND_HOST`: backend (container name)
- `BACKEND_PORT`: 8000
- `FRONTEND_HOST`: frontend (container name)
- `FRONTEND_PORT`: 3000

**Routing**:
- `/` → Frontend container
- `/api/*` → Backend container
- `/health` → Backend container
- `/docs` → Backend container (API documentation)

## Docker Volumes

Persistent data is stored in Docker volumes:

```yaml
volumes:
  backend_data:      # Backend data (workflow executions, etc.)
  letsencrypt_certs: # SSL certificates (mounted read-only)
  certbot_www:       # ACME challenge files (mounted read-only)
```

**Volume locations** on droplet:
```bash
docker volume inspect ai-video-automation_backend_data
docker volume inspect ai-video-automation_letsencrypt_certs
```

## Troubleshooting

### Backend won't start

**Check logs**:
```bash
docker logs ai-video-backend
```

**Common issues**:
- Missing environment variables
- Database connection failure (check SUPABASE_* vars)
- Port already in use

### Frontend won't start

**Check logs**:
```bash
docker logs ai-video-frontend
```

**Common issues**:
- Missing NEXT_PUBLIC_* environment variables
- Backend not reachable (check network connectivity)
- Build failure (check image was built correctly)

### Nginx won't start

**Check logs**:
```bash
docker logs ai-video-nginx
```

**Common issues**:
- SSL certificates not found (run SSL setup first)
- Backend/frontend containers not running
- Invalid nginx configuration

**Test configuration**:
```bash
docker exec ai-video-nginx nginx -t
```

### SSL certificate issues

**Verify certificates exist**:
```bash
ls -la /opt/ai-video-automation/letsencrypt/live/vingine.duckdns.org/
```

**Should see**:
```
fullchain.pem
privkey.pem
```

**Renew manually**:
```bash
/opt/ai-video-automation/renew-ssl.sh
```

### Container networking issues

**Check network**:
```bash
docker network inspect ai-video-automation_app-network
```

**Verify containers are on same network**:
```bash
docker exec ai-video-nginx ping -c 1 backend
docker exec ai-video-nginx ping -c 1 frontend
```

## Advantages of This Architecture

✅ **Separation of Concerns**: Each service deploys independently
✅ **No SSH Scripts**: All configuration in Docker images
✅ **Reproducible**: Same container runs everywhere
✅ **Easy Rollback**: Redeploy previous image version
✅ **Health Checks**: Automated service health monitoring
✅ **Resource Limits**: CPU/memory limits per service
✅ **Centralized Logging**: All logs via docker-compose
✅ **Zero Downtime**: Recreate containers without affecting others

## Migration from Old Setup

If you have the old setup (manual nginx + docker run), migrate:

1. **Backup current data**:
   ```bash
   docker cp ai-video-backend:/data /opt/ai-video-automation/backup-data
   ```

2. **Stop old containers**:
   ```bash
   docker stop ai-video-backend ai-video-frontend ai-video-nginx
   docker rm ai-video-backend ai-video-frontend ai-video-nginx
   ```

3. **Deploy new stack** (follow "Deploy Stack" steps above)

4. **Restore data** (if needed):
   ```bash
   docker cp /opt/ai-video-automation/backup-data ai-video-backend:/data
   ```

## Next Steps

After deployment:

1. ✅ Test frontend: https://vingine.duckdns.org
2. ✅ Test backend API: https://vingine.duckdns.org/docs
3. ✅ Verify main pipeline cron job is running
4. ✅ Check all services are healthy
5. ✅ Setup monitoring/alerts (optional)
