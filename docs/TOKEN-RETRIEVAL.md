# How to Get Your API Token

This guide shows all the ways to retrieve your JWT authentication token for API requests.

---

## Method 1: From the UI (Easiest)

After signing in, your dashboard displays a **"API Token"** card with a "Copy Token" button.

1. Go to http://localhost:3000
2. Sign in with Google
3. You'll see an "API Token" card on your dashboard
4. Click "Copy Token"
5. Paste in Swagger UI at http://localhost:8000/docs

---

## Method 2: Browser Console

Open your browser's Developer Tools and run:

```javascript
// Get just the token
(await window.supabase.auth.getSession()).data.session.access_token

// Get full session info
(await window.supabase.auth.getSession()).data.session

// Get user info
(await window.supabase.auth.getSession()).data.session.user
```

**Note:** The token is valid for 1 hour by default.

---

## Method 3: In React Components (Client-Side)

### Using the `useAuth` hook:

```typescript
'use client';

import { useAuth } from '@/lib/auth-context';
import { supabase } from '@/lib/supabase';
import { useState, useEffect } from 'react';

export function MyComponent() {
  const { user } = useAuth();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const getToken = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        setToken(session.access_token);
        console.log('Token:', session.access_token);
      }
    };

    if (user) {
      getToken();
    }
  }, [user]);

  // Use token for API calls...
}
```

### Using the helper function:

```typescript
'use client';

import { getAccessToken, getAuthHeader } from '@/lib/get-token';

export function MyComponent() {
  const makeAuthenticatedRequest = async () => {
    // Option 1: Get token directly
    const token = await getAccessToken();
    console.log('Token:', token);

    // Option 2: Get formatted header
    const headers = await getAuthHeader();
    // headers = { Authorization: 'Bearer eyJ...' }

    // Use in fetch
    const response = await fetch('http://localhost:8000/api/cron/jobs', {
      headers: {
        ...headers,
        'Content-Type': 'application/json'
      }
    });
  };
}
```

---

## Method 4: In Server Actions (Server-Side)

Server Actions automatically get the token from httpOnly cookies:

```typescript
'use server'

import { createClient } from '@/lib/supabase-server'

export async function myServerAction() {
  const supabase = await createClient()
  const { data: { session }, error } = await supabase.auth.getSession()

  if (!session) {
    return { error: 'Not authenticated' }
  }

  // Use session.access_token for backend API calls
  const response = await fetch('http://localhost:8000/api/cron/jobs', {
    headers: {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json'
    }
  })

  return await response.json()
}
```

---

## Using the Token in Swagger UI

1. **Get your token** using any method above
2. **Go to Swagger UI:** http://localhost:8000/docs
3. **Click "Authorize"** button (🔒 icon at top right)
4. **Paste your token** in the "Value" field
5. **Click "Authorize"** then "Close"
6. **Test endpoints** - they'll automatically include your token

---

## Token Format

The token is a JWT (JSON Web Token) that looks like:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx...
```

**Structure:**
- Starts with `eyJ`
- Three parts separated by dots (`.`)
- Contains encoded user information
- Signed by Supabase

**Important:**
- Valid for 1 hour (configurable in Supabase)
- Refresh automatically handled by Supabase client
- Never share your token publicly
- Only send over HTTPS in production

---

## Complete Example: Making an Authenticated API Call

### From React Component:

```typescript
'use client';

import { getAuthHeader } from '@/lib/get-token';
import { useState } from 'react';

export function CronJobsList() {
  const [jobs, setJobs] = useState([]);

  const loadJobs = async () => {
    const headers = await getAuthHeader();

    if (!headers) {
      console.error('Not authenticated');
      return;
    }

    const response = await fetch('http://localhost:8000/api/cron/jobs', {
      headers: {
        ...headers,
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const data = await response.json();
      setJobs(data.jobs);
    }
  };

  return (
    <div>
      <button onClick={loadJobs}>Load Cron Jobs</button>
      {/* Display jobs... */}
    </div>
  );
}
```

### From Server Action:

```typescript
'use server'

import { createClient } from '@/lib/supabase-server'

export async function listCronJobs() {
  const supabase = await createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session) {
    return { success: false, error: 'Not authenticated' }
  }

  const response = await fetch('http://localhost:8000/api/cron/jobs', {
    headers: {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json'
    }
  })

  const data = await response.json()
  return { success: true, data }
}
```

---

## Token Refresh

Supabase automatically refreshes tokens when they expire:

```typescript
import { supabase } from '@/lib/supabase';

// Listen for token refresh
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'TOKEN_REFRESHED') {
    console.log('Token refreshed!');
    console.log('New token:', session?.access_token);
  }
});
```

The `useAuth` context hook automatically handles token refresh.

---

## Summary

**Easiest for Swagger:** Use the Token Display component on your dashboard

**Easiest for Code:**
- Client-side: `getAccessToken()` or `getAuthHeader()`
- Server-side: Use Server Actions with `supabase-server`

**Direct Access:** Browser console with `(await window.supabase.auth.getSession()).data.session.access_token`

All methods return the same JWT token that's valid for authenticated API requests.
