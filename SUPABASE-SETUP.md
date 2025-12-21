# Supabase OAuth Configuration

## Important: Configure Redirect URLs in Supabase

For OAuth authentication to work correctly on your production domain, you **must** add the production redirect URL to your Supabase project settings.

## Step-by-Step Instructions

### 1. Go to Supabase Dashboard
Navigate to: https://supabase.com/dashboard

### 2. Select Your Project
Click on your project: `lkcxipsuntggnjykhvoo`

### 3. Navigate to Authentication Settings
- Click on **Authentication** in the left sidebar
- Click on **URL Configuration**

### 4. Add Production Redirect URLs

In the **Redirect URLs** section, add the following URLs:

```
https://vingine.duckdns.org/auth/callback
http://vingine.duckdns.org/auth/callback
```

**Important Notes:**
- Add **both** HTTPS and HTTP versions (HTTPS will be used in production)
- The URLs must match **exactly** - including the `/auth/callback` path
- After adding, click **Save**

### 5. Verify Site URL

In the **Site URL** field, ensure it's set to:
```
https://vingine.duckdns.org
```

This is the URL users will be redirected to after email confirmations.

## Current Configuration

Your application is configured with:
- **NEXT_PUBLIC_SITE_URL**: `https://vingine.duckdns.org`
- **NEXT_PUBLIC_API_URL**: `https://vingine.duckdns.org`
- **Supabase Project**: `https://lkcxipsuntggnjykhvoo.supabase.co`

## OAuth Flow

```
┌─────────────┐                                    ┌──────────────┐
│   User      │                                    │   Supabase   │
│  Browser    │                                    │    OAuth     │
└─────────────┘                                    └──────────────┘
       │                                                   │
       │  1. Click "Sign in with Google"                  │
       │─────────────────────────────────────────────────►│
       │                                                   │
       │  2. Redirect to Google OAuth                     │
       │◄─────────────────────────────────────────────────│
       │                                                   │
       │  3. User authenticates with Google               │
       │─────────────────────────────────────────────────►│
       │                                                   │
       │  4. Google redirects to Supabase                 │
       │◄─────────────────────────────────────────────────│
       │                                                   │
       │  5. Supabase redirects to:                       │
       │     https://vingine.duckdns.org/auth/callback    │
       │     with access_token                            │
       │◄─────────────────────────────────────────────────│
       │                                                   │
       │  6. App extracts token and completes auth        │
       │                                                   │
       ▼                                                   │
  Authenticated                                           │
```

## Troubleshooting

### Issue: Still redirecting to 0.0.0.0:3000

**Cause**: Redirect URL not added to Supabase settings

**Solution**:
1. Follow steps above to add `https://vingine.duckdns.org/auth/callback` to Supabase
2. Clear browser cache
3. Try signing in again

### Issue: "Invalid redirect URL" error

**Cause**: URL in Supabase settings doesn't match exactly

**Solution**:
- Ensure you added the **exact** URL: `https://vingine.duckdns.org/auth/callback`
- Check for trailing slashes (should NOT have one after `callback`)
- Verify protocol is HTTPS (not HTTP)

### Issue: Redirect works but authentication fails

**Cause**: CORS or site URL misconfiguration

**Solution**:
1. Verify **Site URL** in Supabase is set to `https://vingine.duckdns.org`
2. Check **Additional Redirect URLs** includes your production domain
3. Ensure **NEXT_PUBLIC_SUPABASE_URL** and **NEXT_PUBLIC_SUPABASE_ANON_KEY** are correct

## Local Development

For local development, also add:
```
http://localhost:3000/auth/callback
```

This allows you to test OAuth locally without affecting production.

## Security Notes

- **Never** commit Supabase keys to Git (they're in .env which is .gitignored)
- Use **HTTPS** in production for secure token transmission
- Redirect URLs act as a security measure - only listed URLs can receive tokens
- Keep your **Service Role Key** secret (it has full database access)

## Additional Resources

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [OAuth with Supabase](https://supabase.com/docs/guides/auth/social-login)
- [Redirect URLs Configuration](https://supabase.com/docs/guides/auth/redirect-urls)
