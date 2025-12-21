'use client';

import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

export function TokenDisplay() {
  const { user } = useAuth();
  const [token, setToken] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

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

  const copyToken = () => {
    if (token) {
      navigator.clipboard.writeText(token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!user || !token) return null;

  return (
    <div className="border rounded-lg p-4 bg-muted/50">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold">API Token</h3>
        <Button
          onClick={copyToken}
          variant="outline"
          size="sm"
        >
          {copied ? '✓ Copied!' : 'Copy Token'}
        </Button>
      </div>
      <div className="bg-background rounded p-2 font-mono text-xs break-all">
        {token.substring(0, 50)}...
      </div>
      <p className="text-xs text-muted-foreground mt-2">
        Use this token to authenticate API requests in Swagger UI
      </p>
    </div>
  );
}
