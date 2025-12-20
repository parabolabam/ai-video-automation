# Google Authentication Setup Guide

This guide walks you through setting up Google OAuth authentication for both the frontend and backend of the AI Video Automation platform using Supabase.

---

## Overview

The authentication system uses:
- **Supabase Auth** - Handles OAuth flow and session management
- **Google OAuth** - Provides user authentication
- **JWT Tokens** - Secure communication between frontend and backend
- **FastAPI Auth Middleware** - Validates tokens on protected endpoints

---

## Prerequisites

1. A Supabase project (create one at [supabase.com](https://supabase.com))
2. Google Cloud Console account
3. Your application URLs:
   - Development: `http://localhost:3000`
   - Production: `https://vingine.duckdns.org` (or your domain)

---

## Step 1: Create Google OAuth Credentials

### 1.1 Go to Google Cloud Console

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** → **Credentials**

### 1.2 Configure OAuth Consent Screen

1. Click **OAuth consent screen** in the left sidebar
2. Choose **External** user type
3. Fill in the application information:
   - App name: `AI Video Automation`
   - User support email: Your email
   - Developer contact: Your email
4. Add scopes (optional for basic authentication):
   - `userinfo.email`
   - `userinfo.profile`
5. Click **Save and Continue**

### 1.3 Create OAuth 2.0 Client ID

1. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
2. Application type: **Web application**
3. Name: `AI Video Automation - Supabase`
4. Add **Authorized redirect URIs**:
   ```
   https://YOUR_PROJECT_REF.supabase.co/auth/v1/callback
   ```
   Replace `YOUR_PROJECT_REF` with your Supabase project reference (found in Supabase dashboard URL)

5. Click **Create**
6. **Save your Client ID and Client Secret** - you'll need these for Supabase

---

## Step 2: Configure Supabase Authentication

### 2.1 Enable Google Provider in Supabase

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Authentication** → **Providers**
4. Find **Google** in the list and click to configure
5. Enable the Google provider
6. Enter your Google OAuth credentials:
   - **Client ID**: From Google Cloud Console
   - **Client Secret**: From Google Cloud Console
7. Click **Save**

### 2.2 Configure Redirect URLs

1. In Supabase Dashboard, go to **Authentication** → **URL Configuration**
2. Add your redirect URLs:
   - Development: `http://localhost:3000/auth/callback`
   - Production: `https://vingine.duckdns.org/auth/callback`
3. Set **Site URL** to:
   - Development: `http://localhost:3000`
   - Production: `https://vingine.duckdns.org`

### 2.3 Get Supabase API Keys

1. Navigate to **Settings** → **API**
2. Copy the following values (you'll need these for environment variables):
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon public** key (for frontend)
   - **service_role** key (for backend - keep this secret!)

---

## Step 3: Configure Frontend Environment Variables

### 3.1 Update Frontend .env Files

Create or update `web/.env.local` for development:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_public_key_here
```

Update `web/.env.production` for production:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=https://vingine.duckdns.org

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_public_key_here
```

---

## Step 4: Configure Backend Environment Variables

### 4.1 Update Backend .env File

Add to your root `.env` file:

```bash
# Supabase Configuration (for backend authentication)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_service_role_key_here
```

**Important**: The backend uses the `service_role` key, not the `anon` key. This allows it to verify JWT tokens and access user data.

---

## Step 5: Using Authentication in Your App

### 5.1 Frontend Usage

The authentication context is already set up. Use it in your components:

```tsx
import { useAuth } from '@/lib/auth-context';

export default function MyComponent() {
  const { user, loading, signInWithGoogle, signOut } = useAuth();

  if (loading) return <div>Loading...</div>;

  if (!user) {
    return <button onClick={signInWithGoogle}>Sign in with Google</button>;
  }

  return (
    <div>
      <p>Welcome, {user.email}!</p>
      <button onClick={signOut}>Sign out</button>
    </div>
  );
}
```

### 5.2 Protected Routes

Wrap pages that require authentication:

```tsx
import { ProtectedRoute } from '@/components/auth/protected-route';

export default function WorkflowPage() {
  return (
    <ProtectedRoute>
      {/* Your protected content here */}
    </ProtectedRoute>
  );
}
```

### 5.3 Add Login Button to Navigation

We've created a reusable `LoginButton` component:

```tsx
import { LoginButton } from '@/components/auth/login-button';

export default function Header() {
  return (
    <header>
      <nav>
        {/* Your navigation */}
        <LoginButton />
      </nav>
    </header>
  );
}
```

### 5.4 Sending Authenticated Requests

When calling the backend API, include the access token:

```tsx
import { useAuth } from '@/lib/auth-context';
import { runWorkflowStream } from '@/lib/api-stream';

export default function RunWorkflow() {
  const { session } = useAuth();

  const handleRun = async () => {
    await runWorkflowStream({
      workflow_id: 'xxx',
      user_id: session?.user.id || '',
      input: 'test',
      accessToken: session?.access_token, // Include token
      onEvent: (event) => console.log(event),
    });
  };

  return <button onClick={handleRun}>Run Workflow</button>;
}
```

---

## Step 6: Backend Authentication

### 6.1 Protected Endpoints

The backend now supports optional authentication. If a user is authenticated, it validates their access:

```python
# Automatically validates user_id matches authenticated user
@app.post("/api/run_stream")
async def run_workflow_stream(
    request: WorkflowExecutionRequest,
    current_user: dict = Depends(get_optional_user)
):
    # If authenticated, user can only access their own workflows
    if current_user:
        verify_user_access(request.user_id, current_user)

    # ... rest of endpoint
```

### 6.2 Required Authentication

For endpoints that MUST have authentication:

```python
from features.platform.auth import get_current_user

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user  # Returns 401 if not authenticated
```

---

## Step 7: Testing Authentication

### 7.1 Test Frontend Login

1. Start the frontend:
   ```bash
   cd web
   npm run dev
   ```

2. Navigate to `http://localhost:3000`
3. Click "Sign in with Google"
4. Complete Google OAuth flow
5. You should be redirected back and see your email

### 7.2 Test Backend Authentication

1. Get your access token from the frontend (check browser console or use the `/api/auth/me` endpoint)

2. Test protected endpoint:
   ```bash
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     https://vingine.duckdns.org/api/auth/me
   ```

3. Should return your user information

### 7.3 Test Workflow Execution

```bash
curl -X POST https://vingine.duckdns.org/api/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "workflow_id": "xxx",
    "user_id": "YOUR_USER_ID",
    "input": "test"
  }'
```

---

## Step 8: Deploy to Production

### 8.1 Update Supabase URLs

Make sure your production Supabase configuration includes:
- Redirect URL: `https://vingine.duckdns.org/auth/callback`
- Site URL: `https://vingine.duckdns.org`

### 8.2 Update Google OAuth Redirect URIs

In Google Cloud Console, add your production Supabase callback URL:
```
https://YOUR_PROJECT_REF.supabase.co/auth/v1/callback
```

### 8.3 Update Docker Environment

If deploying with Docker, make sure your backend container has:

```bash
# In docker run command or docker-compose.yml
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
```

### 8.4 Rebuild and Deploy

```bash
# Backend
docker build -t ai-video-backend .
docker run -d --name ai-video-backend \
  -e SUPABASE_URL="https://xxxxx.supabase.co" \
  -e SUPABASE_SERVICE_KEY="your_service_key" \
  ai-video-backend

# Frontend
cd web
npm run build
npm start
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         User Browser                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1. Click "Sign in with Google"
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Next.js Frontend (Port 3000)               │
│  • AuthProvider (auth-context.tsx)                           │
│  • LoginButton component                                     │
│  • ProtectedRoute component                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 2. Redirect to Supabase OAuth
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Supabase Auth                          │
│  • Handles Google OAuth flow                                 │
│  • Issues JWT access token                                   │
│  • Manages user session                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 3. Redirect back with session
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Frontend (/auth/callback route)                 │
│  • Exchanges code for session                                │
│  • Stores session in context                                 │
│  • Redirects to home page                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 4. API request with Bearer token
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (Port 8000)                  │
│  • Auth middleware (features/platform/auth.py)               │
│  • Validates JWT with Supabase                               │
│  • Verifies user_id matches token                            │
│  • Executes workflow                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Error: "Invalid authentication token"

**Cause**: Token expired or invalid

**Solution**:
- Check token is being sent in `Authorization: Bearer <token>` header
- Verify `SUPABASE_SERVICE_KEY` is correct in backend `.env`
- Try signing out and signing in again

### Error: "You don't have permission to access this resource"

**Cause**: Authenticated user trying to access another user's resources

**Solution**:
- Ensure `user_id` in request matches authenticated user's ID
- Use `session.user.id` from frontend auth context

### Google OAuth redirect not working

**Cause**: Redirect URL mismatch

**Solution**:
- Check Google Cloud Console has correct callback URL
- Verify Supabase redirect URL configuration
- Ensure `/auth/callback` route exists in Next.js app

### Backend not validating tokens

**Cause**: Missing or incorrect Supabase configuration

**Solution**:
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are set
- Check backend logs for authentication errors
- Test with `curl` to isolate frontend/backend issues

---

## Security Best Practices

1. **Never commit secrets**: Keep `.env` files in `.gitignore`
2. **Use service_role key only in backend**: Never expose it to frontend
3. **Enable RLS in Supabase**: Add Row Level Security policies to database tables
4. **HTTPS only in production**: Enforce HTTPS for all authentication flows
5. **Validate user_id**: Always verify authenticated user owns requested resources
6. **Token expiration**: Supabase tokens expire automatically, handle refresh
7. **CORS configuration**: Only allow trusted origins in backend CORS settings

---

## Next Steps

1. **Add profile creation**: Create user profiles in database on first login
2. **Implement RLS**: Add Supabase Row Level Security policies
3. **Add role-based access**: Extend auth to support admin/user roles
4. **Session management**: Implement token refresh logic
5. **Social providers**: Add GitHub, Facebook, etc. alongside Google

---

## Files Created/Modified

### Backend
- `features/platform/auth.py` - Authentication utilities and middleware
- `features/platform/server.py` - Updated with auth dependencies and CORS

### Frontend
- `web/src/lib/auth-context.tsx` - React context for authentication state
- `web/src/app/auth/callback/route.ts` - OAuth callback handler
- `web/src/components/auth/login-button.tsx` - Reusable login/logout button
- `web/src/components/auth/protected-route.tsx` - Route protection wrapper
- `web/src/lib/api-stream.ts` - Updated to support access tokens
- `web/src/app/providers.tsx` - Added AuthProvider

### Configuration
- `web/.env.example` - Updated with Supabase credentials
- `web/.env.production` - Updated with Supabase credentials
- `.env.example` - Updated with backend Supabase service key

---

## Support

For issues or questions:
- Supabase Docs: https://supabase.com/docs/guides/auth
- Google OAuth Docs: https://developers.google.com/identity/protocols/oauth2
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/

---

**Authentication setup complete!** 🎉

Your application now supports secure Google authentication with JWT token validation on both frontend and backend.
