'use client';

import { ProtectedRoute } from '@/components/auth/protected-route';
import { useAuth } from '@/lib/auth-context';
import { supabase } from '@/lib/supabase';
import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

// Dynamically import SwaggerUI to avoid SSR issues
const SwaggerUI = dynamic(() => import('swagger-ui-react'), { ssr: false });

export default function DocsPage() {
  const { user, loading } = useAuth();
  const [token, setToken] = useState<string | null>(null);
  const [spec, setSpec] = useState<any>(null);

  useEffect(() => {
    const getToken = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        setToken(session.access_token);
      }
    };

    if (user) {
      getToken();
    }
  }, [user]);

  useEffect(() => {
    // Fetch OpenAPI spec from backend
    fetch('http://localhost:8000/openapi.json')
      .then(res => res.json())
      .then(data => setSpec(data))
      .catch(err => console.error('Failed to load API spec:', err));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen">
        <div className="bg-background border-b px-4 py-3 sticky top-0 z-50">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div>
              <h1 className="text-xl font-bold">AI Video Platform API</h1>
              <p className="text-sm text-muted-foreground">
                {token ? '🔒 Auto-authenticated with your Google account' : '⚠️ Not authenticated'}
              </p>
            </div>
            <div className="flex gap-2 items-center">
              {token && (
                <div className="text-xs bg-green-500/10 text-green-600 dark:text-green-400 px-3 py-1.5 rounded-full font-medium">
                  Token Injected
                </div>
              )}
              <a
                href="/"
                className="text-sm text-muted-foreground hover:text-foreground underline"
              >
                ← Back to Dashboard
              </a>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto">
          {spec && token ? (
            <SwaggerUI
              spec={spec}
              onComplete={(system: any) => {
                // Auto-inject the bearer token
                system.preauthorizeApiKey('HTTPBearer', token);
              }}
              requestInterceptor={(req: any) => {
                // Ensure bearer token is always included
                if (token && !req.headers.Authorization) {
                  req.headers.Authorization = `Bearer ${token}`;
                }
                return req;
              }}
            />
          ) : (
            <div className="flex items-center justify-center p-12">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 dark:border-gray-100 mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading API documentation...</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
