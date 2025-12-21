# Authentication Setup Quickstart

Complete step-by-step guide to configure Google OAuth authentication in your AI Video Automation project.

---

## Prerequisites

- [ ] Supabase account (https://supabase.com)
- [ ] Google Cloud Console account
- [ ] GitHub repository access
- [ ] Digital Ocean droplet running

---

## Step 1: Create Supabase Project (5 minutes)

### 1.1 Create Project

1. Go to https://supabase.com/dashboard
2. Click **"New Project"**
3. Fill in:
   - **Name**: `ai-video-automation`
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to your users
4. Click **"Create new project"**
5. Wait 2-3 minutes for project to initialize

### 1.2 Get Supabase Credentials

1. Go to **Settings** → **API**
2. Copy these values (you'll need them later):
   ```
   Project URL: https://xxxxx.supabase.co
   anon public key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   service_role key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
3. ⚠️ **IMPORTANT**: Keep `service_role` key secret (never commit to git)

---

## Step 2: Configure Google OAuth (10 minutes)

### 2.1 Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click **"Select a project"** → **"New Project"**
3. Name: `AI Video Automation`
4. Click **"Create"**

### 2.2 Enable OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** user type
3. Click **"Create"**
4. Fill in:
   - **App name**: `AI Video Automation`
   - **User support email**: Your email
   - **Developer contact**: Your email
5. Click **"Save and Continue"**
6. **Scopes**: Skip (click **"Save and Continue"**)
7. **Test users**: Skip (click **"Save and Continue"**)
8. Click **"Back to Dashboard"**

### 2.3 Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **"Create Credentials"** → **"OAuth 2.0 Client ID"**
3. Application type: **Web application**
4. Name: `AI Video Automation - Supabase`
5. **Authorized redirect URIs**: Click **"Add URI"**
   - Add: `https://YOUR_PROJECT_REF.supabase.co/auth/v1/callback`
   - Replace `YOUR_PROJECT_REF` with your Supabase project ID
   - Example: `https://abcdefghijklmn.supabase.co/auth/v1/callback`
6. Click **"Create"**
7. **SAVE THESE VALUES**:
   ```
   Client ID: 123456789-abc.apps.googleusercontent.com
   Client Secret: GOCSPX-xxxxxxxxxxxxx
   ```

**How to find your Supabase Project Ref:**
- Go to Supabase Dashboard → Settings → General
- Look for "Reference ID" or check your Project URL
- URL format: `https://[PROJECT_REF].supabase.co`

---

## Step 3: Enable Google Auth in Supabase (2 minutes)

### 3.1 Configure Google Provider

1. Go to Supabase Dashboard
2. Navigate to **Authentication** → **Providers**
3. Find **Google** in the list
4. Click to expand
5. Toggle **"Enable"** to ON
6. Paste your credentials:
   - **Client ID**: (from Google Cloud Console)
   - **Client Secret**: (from Google Cloud Console)
7. Click **"Save"**

### 3.2 Configure Redirect URLs

1. Still in Supabase, go to **Authentication** → **URL Configuration**
2. Add **Site URL**:
   - Development: `http://localhost:3000`
   - Production: `https://vingine.duckdns.org` (or your domain)
3. Add **Redirect URLs**:
   - `http://localhost:3000/auth/callback`
   - `https://vingine.duckdns.org/auth/callback`
4. Click **"Save"**

---

## Step 4: Configure GitHub Secrets (5 minutes)

### 4.1 Add Supabase Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Add these secrets ONE BY ONE:

**Backend Secrets:**
```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (anon public key)
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (service_role key)
```

**Frontend Secrets:**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (anon public key)
```

### 4.2 Add Other Required Secrets

Make sure these are also configured:
```bash
# API Keys
KIE_API_KEY=your_kie_api_key
OPENAI_API_KEY=sk-xxxxx

# Deployment
DO_DROPLET_IP=134.199.244.59
DO_DROPLET_USER=root
DO_SSH_PRIVATE_KEY=<your_ssh_private_key_content>

# Backend API URL
NEXT_PUBLIC_API_URL=https://vingine.duckdns.org
```

---

## Step 5: Update Local Environment (2 minutes)

### 5.1 Backend .env

Create/update `.env` in project root:

```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (anon)
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (service_role)

# API Keys
KIE_API_KEY=your_kie_api_key
OPENAI_API_KEY=sk-xxxxx

# YouTube (if using)
YOUTUBE_CLIENT_ID=xxxxx
YOUTUBE_CLIENT_SECRET=xxxxx
YOUTUBE_REFRESH_TOKEN=xxxxx
```

### 5.2 Frontend .env.local

Create `web/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Step 6: Test Locally (5 minutes)

### 6.1 Start Backend

```bash
# Install dependencies
uv sync

# Run backend
uv run uvicorn features.platform.server:app --reload

# Should see:
# ✅ Uvicorn running on http://127.0.0.1:8000
```

### 6.2 Start Frontend

```bash
cd web

# Install dependencies (if not done)
npm install

# Run frontend
npm run dev

# Should see:
# ✅ Ready on http://localhost:3000
```

### 6.3 Test Authentication

1. Open browser: http://localhost:3000
2. You should see **"Sign in with Google"** button
3. Click the button
4. Google OAuth popup should appear
5. Select your Google account
6. Grant permissions
7. You should be redirected to `/user/{your-user-id}`
8. Top right should show your email and **"Sign Out"** button

### 6.4 Test Backend Authentication

```bash
# This should fail (no auth)
curl http://localhost:8000/api/auth/me

# Expected: {"detail":"Missing authentication token"}

# Get token from browser:
# 1. Open DevTools (F12)
# 2. Go to Application → Storage → Cookies
# 3. Find cookie starting with "sb-"
# 4. Copy the value (this is your session)

# Now test with token (get from browser session)
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/auth/me

# Expected: {"id":"xxx","email":"you@gmail.com","user_metadata":{...}}
```

---

## Step 7: Deploy to Production (Automatic)

### 7.1 Commit and Push

```bash
# Your changes should already be committed
# Just push to main to trigger deployment

git checkout main
git merge deployment/github-actions-setup
git push origin main
```

### 7.2 Monitor Deployment

1. Go to GitHub → **Actions** tab
2. Watch workflows:
   - **Deploy Backend to Digital Ocean**
   - **Deploy Frontend to Digital Ocean**
3. Wait for both to complete (green checkmarks)

### 7.3 Verify Production

```bash
# Test backend health
curl https://vingine.duckdns.org/health

# Expected: {"status":"ok"}

# Test auth endpoint (should fail without token)
curl https://vingine.duckdns.org/api/auth/me

# Expected: {"detail":"Missing authentication token"}
```

---

## Step 8: Test Production Authentication (2 minutes)

1. Open browser: https://vingine.duckdns.org
2. Click **"Sign in with Google"**
3. Complete Google OAuth
4. You should see your dashboard
5. Try running a workflow
6. Check that it works end-to-end

---

## Troubleshooting

### Issue: "Missing authentication token"

**Cause**: Not signed in or session expired

**Solution**:
1. Sign out completely
2. Clear browser cookies for your domain
3. Sign in again with Google

### Issue: "Invalid authentication token"

**Cause**: Token expired or invalid

**Solution**:
1. Check `SUPABASE_SERVICE_KEY` is correct in GitHub Secrets
2. Restart backend container:
   ```bash
   ssh root@134.199.244.59
   docker restart ai-video-backend
   docker logs ai-video-backend
   ```

### Issue: "Unauthorized: You can only run your own workflows"

**Cause**: Trying to access another user's resources

**Solution**:
- Make sure you're using your own user_id
- Each user can only access their own workflows

### Issue: Google OAuth Redirect Error

**Cause**: Redirect URI mismatch

**Solution**:
1. Check Google Cloud Console → OAuth Credentials
2. Verify redirect URI matches exactly:
   - Format: `https://YOUR_PROJECT.supabase.co/auth/v1/callback`
3. Check Supabase → Authentication → URL Configuration
4. Ensure Site URL and Redirect URLs are correct

### Issue: Environment Validation Failed

**Cause**: Missing required environment variables

**Solution**:
1. Check container logs:
   ```bash
   docker logs ai-video-backend
   docker logs ai-video-frontend
   ```
2. Look for "❌ MISSING REQUIRED ENVIRONMENT VARIABLES"
3. Add missing variables to GitHub Secrets
4. Redeploy

---

## Verification Checklist

- [ ] Supabase project created
- [ ] Google OAuth credentials created
- [ ] Google provider enabled in Supabase
- [ ] Redirect URLs configured in Supabase
- [ ] GitHub Secrets added (all of them)
- [ ] Local .env files configured
- [ ] Backend runs locally (port 8000)
- [ ] Frontend runs locally (port 3000)
- [ ] Can sign in with Google locally
- [ ] Can access dashboard locally
- [ ] Deployed to production (GitHub Actions green)
- [ ] Can sign in with Google in production
- [ ] Can run workflows in production

---

## Summary

**Time Required**: ~30 minutes total

**What You Configured**:
1. ✅ Supabase project with database
2. ✅ Google OAuth credentials
3. ✅ Google provider in Supabase
4. ✅ Redirect URLs for local and production
5. ✅ GitHub Secrets for deployment
6. ✅ Local environment for development
7. ✅ Production deployment via GitHub Actions

**What Works Now**:
- ✅ Users can sign in with Google
- ✅ Frontend protected (requires login)
- ✅ Backend protected (requires JWT token)
- ✅ Users isolated (can't access others' data)
- ✅ Automatic deployments on push to main

---

## Next Steps

1. Test all workflows
2. Invite team members (add to Google OAuth test users if needed)
3. Monitor logs for any authentication errors
4. Set up error tracking (Sentry, etc.)
5. Configure database backups

---

## Quick Reference

**Supabase Dashboard**: https://supabase.com/dashboard
**Google Cloud Console**: https://console.cloud.google.com/
**GitHub Secrets**: https://github.com/YOUR_USERNAME/ai-video-automation/settings/secrets/actions

**Local URLs**:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Backend API Docs: http://localhost:8000/docs

**Production URLs**:
- Frontend: https://vingine.duckdns.org (update nginx config if different)
- Backend: https://vingine.duckdns.org
- Backend Health: https://vingine.duckdns.org/health

---

**Authentication is now fully configured!** 🎉
