# Local Development Setup Guide

Quick guide to set up and verify local authentication with Google OAuth.

---

## Prerequisites

1. Node.js 18+ installed
2. Python 3.13+ with `uv` installed
3. Supabase project created (see `docs/AUTH-SETUP-QUICKSTART.md`)
4. Google OAuth credentials configured (see `docs/AUTH-SETUP-QUICKSTART.md`)

---

## Step 1: Environment Variables

### Backend (.env)

Create `.env` in the project root:

```bash
# Copy example
cp .env.example .env
```

Edit `.env` with your values:

```bash
# Required for authentication
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_service_role_key_here

# Required for video generation
KIE_API_KEY=your_kie_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional - YouTube publishing
YOUTUBE_CLIENT_ID=your_youtube_client_id_here
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret_here
YOUTUBE_REFRESH_TOKEN=your_youtube_refresh_token_here
```

**Important:** Get `SUPABASE_SERVICE_KEY` from:
- Supabase Dashboard → Project Settings → API
- Look for "service_role" key (NOT anon key)

### Frontend (web/.env.local)

Create `web/.env.local`:

```bash
# Copy example
cp web/.env.example web/.env.local
```

Edit `web/.env.local` with your values:

```bash
# Backend API URL (local development)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

**Important:** Use `NEXT_PUBLIC_SUPABASE_ANON_KEY` (NOT service_role key) for frontend

---

## Step 2: Install Dependencies

### Backend

```bash
# Install Python dependencies
uv sync
```

### Frontend

```bash
# Install Node dependencies
cd web
npm install
cd ..
```

---

## Step 3: Configure Supabase Redirect URLs

Add local redirect URL to Supabase:

1. Go to Supabase Dashboard → Authentication → URL Configuration
2. Add to "Redirect URLs":
   ```
   http://localhost:3000/auth/callback
   ```
3. Click "Save"

---

## Step 4: Start Services

### Terminal 1 - Backend

```bash
uv run python features/platform/server.py
```

You should see:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Verify backend is running:**
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

### Terminal 2 - Frontend

```bash
cd web
npm run dev
```

You should see:
```
  ▲ Next.js 15.x.x
  - Local:        http://localhost:3000
  - Ready in 2.3s
```

---

## Step 5: Verify Authentication

### Open Browser

1. Navigate to: http://localhost:3000
2. You should see: "AI Video Automation Platform" landing page
3. Click: "Sign in with Google"
4. You should be redirected to Google OAuth consent screen
5. Select your Google account
6. Grant permissions
7. You should be redirected back to: http://localhost:3000/user/[your-user-id]

### Verify Session

Open browser console (F12) and run:

```javascript
// Check if user is authenticated
const { data: { session } } = await window.supabase?.auth.getSession()
console.log('Session:', session)
console.log('User:', session?.user)
```

You should see:
- `session.access_token` - JWT token
- `session.user.id` - Your user UUID
- `session.user.email` - Your email

### Verify Backend Authentication

In browser console:

```javascript
// Test authenticated API call
const session = await (await window.supabase?.auth.getSession()).data.session
const response = await fetch('http://localhost:8000/api/auth/me', {
  headers: {
    'Authorization': `Bearer ${session.access_token}`
  }
})
const data = await response.json()
console.log('Backend user:', data)
```

You should see your user data returned from backend.

---

## Step 6: Test Workflow Execution (Optional)

If you have workflow data in Supabase:

```javascript
// Test workflow execution
const session = await (await window.supabase?.auth.getSession()).data.session
const response = await fetch('http://localhost:8000/api/run', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${session.access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    workflow_id: 'your-workflow-id',
    user_id: session.user.id,
    input: 'Test input'
  })
})
const result = await response.json()
console.log('Workflow result:', result)
```

---

## Troubleshooting

### Issue: "Invalid API key" or environment variable errors

**Solution:** Check your `.env` and `web/.env.local` files

Verify backend env vars are loaded:
```bash
uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('SUPABASE_URL:', os.getenv('SUPABASE_URL')[:30] if os.getenv('SUPABASE_URL') else 'NOT SET')"
```

### Issue: Google OAuth redirect fails

**Solution:** Check redirect URL configuration

1. Verify in Supabase Dashboard → Authentication → URL Configuration
2. Make sure `http://localhost:3000/auth/callback` is added
3. Check browser console for errors

### Issue: "Not authenticated" when calling backend

**Solution:** Verify token is being sent

Check network tab (F12 → Network):
1. Look for request to backend API
2. Check "Request Headers"
3. Verify `Authorization: Bearer <token>` is present

### Issue: CORS errors

**Solution:** Backend CORS is configured for localhost

Verify in `features/platform/server.py`:
```python
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    ...
]
```

### Issue: Frontend can't connect to backend

**Solution:** Check if backend is running

```bash
curl http://localhost:8000/health
```

If connection refused, start backend:
```bash
uv run python features/platform/server.py
```

---

## Quick Verification Script

Run this to verify your setup:

```bash
#!/bin/bash

echo "=== Local Setup Verification ==="
echo ""

# Check backend .env
if [ -f .env ]; then
  echo "✅ Backend .env exists"
else
  echo "❌ Backend .env missing - run: cp .env.example .env"
fi

# Check frontend .env.local
if [ -f web/.env.local ]; then
  echo "✅ Frontend .env.local exists"
else
  echo "❌ Frontend .env.local missing - run: cp web/.env.example web/.env.local"
fi

# Check backend running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
  echo "✅ Backend is running on http://localhost:8000"
else
  echo "❌ Backend not running - start with: uv run python features/platform/server.py"
fi

# Check frontend running
if curl -s http://localhost:3000 > /dev/null 2>&1; then
  echo "✅ Frontend is running on http://localhost:3000"
else
  echo "❌ Frontend not running - start with: cd web && npm run dev"
fi

echo ""
echo "If all checks pass, open http://localhost:3000 and try signing in!"
```

Save as `verify-local-setup.sh`, make executable, and run:

```bash
chmod +x verify-local-setup.sh
./verify-local-setup.sh
```

---

## Next Steps

Once authentication is working:

1. **Workflow Builder UI** - Create interface for building workflows
2. **Cron Jobs Dashboard** - Manage scheduled workflows
3. **Workflow Execution Dashboard** - Monitor running workflows

See `docs/CRON-API.md` for cron job management API documentation.

---

## Summary

Local development requires:

1. ✅ Backend `.env` with Supabase service key
2. ✅ Frontend `web/.env.local` with Supabase anon key
3. ✅ Local redirect URL in Supabase config
4. ✅ Backend running on :8000
5. ✅ Frontend running on :3000
6. ✅ Google OAuth sign-in working

After setup, you can:
- Sign in with Google
- Call authenticated backend APIs
- Build workflow management UI
- Test cron job scheduling
