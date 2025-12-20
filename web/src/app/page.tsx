'use client';

import { useAuth } from '@/lib/auth-context';
import { LoginButton } from '@/components/auth/login-button';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Redirect to user's dashboard if authenticated
    if (user) {
      router.push(`/user/${user.id}`);
    }
  }, [user, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Redirecting to your dashboard...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <main className="max-w-2xl text-center space-y-8">
        <h1 className="text-4xl font-bold tracking-tight">
          AI Video Automation Platform
        </h1>
        <p className="text-lg text-muted-foreground">
          Create and manage AI-powered video workflows with ease.
        </p>
        <div className="pt-4">
          <LoginButton />
        </div>
      </main>
    </div>
  );
}
