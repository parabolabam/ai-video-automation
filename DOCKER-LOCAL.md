# Docker Compose - Local Development

Run the entire stack (backend + frontend) with Docker Compose using your local `.env` credentials.

---

## Quick Start

### 1. Configure Environment Variables

Make sure you have your credentials in `.env` and `web/.env.local`:

```bash
# If you haven't already, run the setup wizard
./setup-local-env.sh

# Or verify manually
./verify-local-setup.sh
```

### 2. Start Services

```bash
./docker-local.sh up
```

This will:
- Build Docker images for backend and frontend
- Start both containers
- Automatically load environment variables from `.env` and `web/.env.local`
- Run environment validation before starting services
- Expose backend on http://localhost:8000
- Expose frontend on http://localhost:3000

### 3. Test Sign-In

1. Open http://localhost:3000
2. Click "Sign in with Google"
3. Complete OAuth flow
4. You should be redirected to your dashboard

---

## Docker Commands

### Start Services
```bash
./docker-local.sh up
# or
./docker-local.sh start
```

### Stop Services
```bash
./docker-local.sh stop
# or
./docker-local.sh down
```

### View Logs
```bash
# All logs
./docker-local.sh logs

# Backend only
./docker-local.sh logs backend

# Frontend only
./docker-local.sh logs frontend
```

### Check Status
```bash
./docker-local.sh status
# or
./docker-local.sh ps
```

### Restart Services
```bash
./docker-local.sh restart
```

### Rebuild Containers
```bash
# Rebuild without cache
./docker-local.sh build

# Then restart
./docker-local.sh up
```

### Test Services
```bash
./docker-local.sh test
```

Output:
```
✅ Backend responding: {"status":"ok"}
✅ Frontend responding
```

### Open Shell in Container
```bash
# Backend shell
./docker-local.sh shell backend

# Frontend shell
./docker-local.sh shell frontend
```

### Clean Up Everything
```bash
# Stop containers and remove volumes
./docker-local.sh clean
```

---

## Docker Compose Configuration

The `docker-compose.yml` file defines two services:

### Backend Service (`backend`)
- **Container:** `ai-video-backend`
- **Port:** 8000
- **Environment:** Loaded from `.env`
- **Validation:** Runs `validate_env.py` on startup
- **Command:** `uvicorn features.platform.server:app --host 0.0.0.0 --port 8000 --reload`
- **Health Check:** `curl http://localhost:8000/health`
- **Volumes:**
  - `./data:/data` - Data persistence
  - `./:/app` - Source code (for hot reload)
  - `/app/.venv` - Python virtual environment

### Frontend Service (`frontend`)
- **Container:** `ai-video-frontend`
- **Port:** 3000
- **Environment:** Loaded from `web/.env.local`
- **Command:** `npm run dev`
- **Depends On:** `backend` (waits for backend to start)
- **Volumes:**
  - `./web:/app` - Source code (for hot reload)
  - `/app/node_modules` - Node modules
  - `/app/.next` - Next.js build cache

---

## Environment Variables

### Backend (.env)
Required variables automatically loaded from `.env`:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
KIE_API_KEY=your_kie_api_key
OPENAI_API_KEY=your_openai_api_key
```

### Frontend (web/.env.local)
Required variables automatically loaded from `web/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

---

## Features

### ✅ Environment Validation
Both containers validate required environment variables on startup:
- Backend validates: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `KIE_API_KEY`, `OPENAI_API_KEY`
- Frontend validates: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`

If any required variable is missing, the container will fail with a clear error message.

### ✅ Hot Reload
Both backend and frontend support hot reload:
- **Backend:** Changes to Python files automatically restart the server
- **Frontend:** Changes to React/Next.js files automatically rebuild

### ✅ Health Checks
Backend has a health check that monitors service availability:
```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### ✅ Dependency Management
Frontend waits for backend to be ready before starting (via `depends_on`).

---

## Troubleshooting

### Container fails to start

**Check logs:**
```bash
./docker-local.sh logs backend
./docker-local.sh logs frontend
```

**Common issues:**
1. Missing environment variables - Run `./verify-local-setup.sh`
2. Port already in use - Stop other services on :8000 or :3000
3. Build cache issues - Run `./docker-local.sh build`

### Can't connect to backend from frontend

**Check if backend is running:**
```bash
curl http://localhost:8000/health
```

**Check backend logs:**
```bash
./docker-local.sh logs backend
```

### Google OAuth redirect fails

**Make sure Supabase redirect URL is configured:**
1. Go to Supabase Dashboard → Authentication → URL Configuration
2. Add: `http://localhost:3000/auth/callback`
3. Restart frontend: `./docker-local.sh restart`

### Environment variable changes not reflected

**Restart services after changing .env:**
```bash
./docker-local.sh restart
```

Or rebuild if needed:
```bash
./docker-local.sh stop
./docker-local.sh build
./docker-local.sh up
```

---

## Direct Docker Compose Commands

If you prefer using docker-compose directly:

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild
docker-compose build --no-cache

# Restart
docker-compose restart

# Shell into backend
docker-compose exec backend sh

# Shell into frontend
docker-compose exec frontend sh
```

---

## Comparison: Docker vs Direct

### Docker Compose (Recommended for Testing)
✅ Isolated environment
✅ Consistent across machines
✅ Easy to reset/clean up
✅ Automatic environment validation
✅ Simulates production more closely
❌ Slower startup
❌ Requires Docker installed

### Direct (Faster for Development)
✅ Faster startup
✅ Easier debugging
✅ Direct access to Python/Node
❌ Requires local Python/Node setup
❌ Environment differences possible

---

## Production vs Local

### Local Development (docker-compose.yml)
- Uses `--reload` for hot reload
- Mounts source code as volumes
- Uses `deps` stage for frontend (faster builds)
- Exposes ports directly

### Production (GitHub Actions)
- Builds optimized production images
- No source code volumes
- Uses `runner` stage for frontend
- Deployed to Digital Ocean droplets

---

## Next Steps

Once sign-in is working in Docker:

1. **Build Workflow UI** - Create interface for workflow management
2. **Add Cron Dashboard** - UI for cron job management (backend API already complete!)
3. **Deploy to Production** - Use GitHub Actions workflows

See:
- `docs/CRON-API.md` - Cron job API documentation
- `.github/workflows/deploy-backend-manual.yml` - Manual backend deployment
- `.github/workflows/deploy-frontend-manual.yml` - Manual frontend deployment

---

## Summary

Run everything with Docker:
```bash
./docker-local.sh up
```

View logs:
```bash
./docker-local.sh logs
```

Test sign-in:
```bash
open http://localhost:3000
```

Stop everything:
```bash
./docker-local.sh stop
```
