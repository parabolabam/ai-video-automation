# Vingine Domain UI Not Loading - Diagnosis & Fix

## 🔍 Problem Diagnosis

**Issue**: https://vingine.duckdns.org/ returns `{"detail":"Not Found"}` instead of showing the UI

**Root Cause**: The nginx configuration only proxies to the **backend** container, not the **frontend** container.

### Current State

```bash
$ curl https://vingine.duckdns.org/
{"detail":"Not Found"}  # This is a FastAPI 404 response

$ curl https://vingine.duckdns.org/health
{"status":"ok"}  # Backend is working
```

### Analysis

1. **DNS**: ✅ `vingine.duckdns.org` → `134.199.244.59` (correct)
2. **SSL**: ✅ HTTPS certificate valid
3. **Nginx**: ✅ Running and responding
4. **Backend**: ✅ Container running and accessible
5. **Frontend**: ❓ Not proxied by nginx

The current nginx config (`/opt/ai-video-automation/nginx/conf.d/vingine.conf`) only has:

```nginx
location / {
    proxy_pass http://172.17.0.2:8000;  # Only backend!
}
```

This means **all requests** go to the backend, which doesn't serve the UI - it only has API endpoints.

## 🛠️ Solution

We need to update the nginx configuration to:
1. Serve **frontend** on `/` (root path)
2. Serve **backend API** on `/api/*`
3. Keep backend `/health` and `/docs` accessible

## 📋 Fix Steps

### Step 1: Verify Frontend is Deployed

SSH into your droplet:

```bash
ssh root@134.199.244.59
```

Check if frontend container is running:

```bash
docker ps | grep frontend
```

**Expected output**:
```
CONTAINER ID   IMAGE                                                   ...   PORTS
abc123...      ghcr.io/parabolabam/ai-video-automation/frontend:...   ...   3000/tcp
```

**If frontend is NOT running**, you need to deploy it first:

1. Go to GitHub repository: https://github.com/parabolabam/ai-video-automation
2. Click "Actions" tab
3. Find "Deploy Frontend (Manual)" workflow
4. Click "Run workflow"
5. Select branch: `deployment/github-actions-setup`
6. Click "Run workflow"

Wait for deployment to complete (~5-10 minutes).

### Step 2: Update Nginx Configuration

Once the frontend is deployed, run this command on the droplet:

```bash
# Download the update script
curl -o /tmp/update-nginx-full-stack.sh \
  https://raw.githubusercontent.com/parabolabam/ai-video-automation/deployment/github-actions-setup/scripts/update-nginx-full-stack.sh

# Make it executable
chmod +x /tmp/update-nginx-full-stack.sh

# Run it
/tmp/update-nginx-full-stack.sh
```

**What this script does**:
1. Detects backend and frontend container IPs
2. Creates new nginx config with proper routing:
   - `/` → Frontend (Next.js UI)
   - `/api/*` → Backend (FastAPI)
   - `/health` → Backend health check
   - `/docs` → Backend API docs
3. Tests and reloads nginx configuration

### Step 3: Verify Fix

After running the script, test the UI:

```bash
# Should show HTML (Next.js page)
curl -s https://vingine.duckdns.org/ | head -10

# Should still work
curl https://vingine.duckdns.org/health
# {"status":"ok"}

# Should still work
curl https://vingine.duckdns.org/docs
# HTML for API docs
```

Then open in browser:
- **UI**: https://vingine.duckdns.org
- **API Docs**: https://vingine.duckdns.org/docs

## 🚨 Alternative: Manual Configuration Update

If the script doesn't work, manually edit the nginx config:

```bash
ssh root@134.199.244.59

# Get container IPs
BACKEND_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ai-video-backend)
FRONTEND_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ai-video-frontend)

echo "Backend: $BACKEND_IP"
echo "Frontend: $FRONTEND_IP"

# Edit nginx config
nano /opt/ai-video-automation/nginx/conf.d/vingine.conf
```

Update the HTTPS server block to:

```nginx
server {
    listen 443 ssl http2;
    server_name vingine.duckdns.org;

    # SSL certificates (keep existing)
    ssl_certificate /etc/letsencrypt/live/vingine.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vingine.duckdns.org/privkey.pem;

    # SSL configuration (keep existing)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

    client_max_body_size 500M;

    # Backend API routes
    location /api/ {
        proxy_pass http://$BACKEND_IP:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 600s;
    }

    # Health check
    location /health {
        proxy_pass http://$BACKEND_IP:8000/health;
        access_log off;
    }

    # API docs
    location /docs {
        proxy_pass http://$BACKEND_IP:8000/docs;
    }

    location /openapi.json {
        proxy_pass http://$BACKEND_IP:8000/openapi.json;
    }

    # Frontend - Next.js
    location / {
        proxy_pass http://$FRONTEND_IP:3000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_read_timeout 86400;
    }
}
```

Test and reload:

```bash
docker exec ai-video-nginx nginx -t
docker exec ai-video-nginx nginx -s reload
```

## 📊 Expected Result

After the fix:

| URL | What You See | Backend |
|-----|--------------|---------|
| https://vingine.duckdns.org | **Next.js UI** (login page) | Frontend container |
| https://vingine.duckdns.org/api/* | API responses | Backend container |
| https://vingine.duckdns.org/health | `{"status":"ok"}` | Backend container |
| https://vingine.duckdns.org/docs | Swagger UI | Backend container |

## 🐛 Troubleshooting

### Frontend container not found

**Error**: "Frontend container not found or not running"

**Fix**: Deploy frontend using GitHub Actions workflow (see Step 1)

### Nginx test fails

**Error**: "nginx configuration has errors"

**Fix**:
1. Check syntax in the config file
2. Verify container IPs are correct
3. Make sure both containers are running

### UI shows "502 Bad Gateway"

**Possible causes**:
1. Frontend container crashed - check: `docker logs ai-video-frontend`
2. Wrong container IP - verify: `docker inspect ai-video-frontend`
3. Frontend not listening on port 3000 - check logs

### API calls from UI fail

**Problem**: UI loads but API calls fail with CORS errors

**Fix**: This shouldn't happen with our setup because frontend and backend are on same domain. If it does:

1. Check backend CORS settings in `features/platform/server.py`
2. Verify `NEXT_PUBLIC_API_URL` environment variable in frontend
3. Check browser console for exact error

## 📝 Summary

**Problem**: Nginx only proxies to backend, not frontend
**Solution**: Update nginx config to route:
- `/` → Frontend UI
- `/api/*` → Backend API

**Required Actions**:
1. ✅ Verify frontend is deployed
2. ✅ Run update script or manually edit nginx config
3. ✅ Reload nginx
4. ✅ Test in browser

**Files Involved**:
- `/opt/ai-video-automation/nginx/conf.d/vingine.conf` (on droplet)
- `scripts/update-nginx-full-stack.sh` (in repo)
