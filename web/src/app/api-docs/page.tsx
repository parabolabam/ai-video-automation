'use client';

import { ProtectedRoute } from '@/components/auth/protected-route';
import { useAuth } from '@/lib/auth-context';
import { supabase } from '@/lib/supabase';
import { useEffect, useState, useRef } from 'react';

export default function ApiDocsPage() {
  const { user, loading } = useAuth();
  const [token, setToken] = useState<string | null>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);

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
    if (token && iframeRef.current) {
      // Wait for iframe to load, then inject token
      const iframe = iframeRef.current;

      iframe.onload = () => {
        try {
          // Inject JavaScript to auto-authorize Swagger UI
          const script = iframe.contentWindow?.document.createElement('script');
          if (script) {
            script.textContent = `
              // Wait for Swagger UI to initialize
              const interval = setInterval(() => {
                if (window.ui) {
                  // Auto-authorize with token
                  window.ui.preauthorizeApiKey('HTTPBearer', '${token}');
                  clearInterval(interval);
                  console.log('Swagger UI auto-authorized!');
                }
              }, 100);
            `;
            iframe.contentWindow?.document.body.appendChild(script);
          }
        } catch {
          // CORS restriction - iframe is cross-origin
          console.log('Cannot inject into iframe (cross-origin)');
        }
      };
    }
  }, [token]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <ProtectedRoute>
      <div className="h-screen flex flex-col">
        <div className="bg-background border-b px-4 py-3">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div>
              <h1 className="text-xl font-bold">API Documentation</h1>
              <p className="text-sm text-muted-foreground">
                {token ? '🔒 Authenticated' : '⚠️ Not authenticated'}
              </p>
            </div>
            <div className="flex gap-2 items-center">
              {token && (
                <div className="text-xs bg-green-500/10 text-green-600 dark:text-green-400 px-3 py-1.5 rounded-full">
                  Token Active
                </div>
              )}
              <a
                href={`http://localhost:8000/docs`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-muted-foreground hover:text-foreground underline"
              >
                Open in new tab
              </a>
            </div>
          </div>
        </div>

        {token ? (
          <div className="flex-1 relative">
            <iframe
              ref={iframeRef}
              src="http://localhost:8000/docs"
              className="absolute inset-0 w-full h-full border-0"
              title="API Documentation"
            />
            <div className="absolute top-4 right-4 bg-yellow-500/10 border border-yellow-500/20 text-yellow-600 dark:text-yellow-400 px-4 py-2 rounded-lg text-sm max-w-md">
              <p className="font-semibold mb-1">Manual Authorization Required</p>
              <p className="text-xs">
                Due to browser security, you need to click &quot;Authorize&quot; in Swagger UI and paste your token manually.
                Use the &quot;Copy Token&quot; button from your dashboard.
              </p>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <p className="text-lg text-muted-foreground">
                Please sign in to view API documentation
              </p>
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
