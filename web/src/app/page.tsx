'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { LoginButton } from '@/components/auth/login-button';
import { useAuth } from '@/lib/auth-context';
import { Loader2 } from 'lucide-react';

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.push(`/user/${user.id}`);
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (user) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <p className="ml-2 text-muted-foreground">Redirecting to your dashboard...</p>
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
