'use client';

import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';

export function LoginButton() {
  const { user, loading, signInWithGoogle, signOut } = useAuth();

  if (loading) {
    return (
      <Button disabled variant="outline">
        Loading...
      </Button>
    );
  }

  if (user) {
    return (
      <div className="flex items-center gap-4">
        <span className="text-sm text-muted-foreground">
          {user.email}
        </span>
        <Button onClick={signOut} variant="outline">
          Sign Out
        </Button>
      </div>
    );
  }

  return (
    <Button onClick={signInWithGoogle} variant="default">
      Sign in with Google
    </Button>
  );
}
