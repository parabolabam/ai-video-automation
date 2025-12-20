'use client';

import { WorkflowsList } from '@/components/workflows-list';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { LoginButton } from '@/components/auth/login-button';
import { useAuth } from '@/lib/auth-context';
import { useParams, useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function UserDashboard() {
  const params = useParams();
  const router = useRouter();
  const { user, loading } = useAuth();
  const userId = params.userId as string;

  useEffect(() => {
    // If authenticated but trying to access another user's dashboard, redirect to own dashboard
    if (user && user.id !== userId) {
      router.push(`/user/${user.id}`);
    }
  }, [user, userId, router]);

  return (
    <ProtectedRoute>
      <div className="min-h-screen p-8 font-[family-name:var(--font-geist-sans)]">
        <main className="max-w-6xl mx-auto space-y-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Agent Workflows</h1>
              <p className="text-muted-foreground mt-2">
                User ID: <code className="bg-muted px-1 py-0.5 rounded">{userId}</code>
              </p>
            </div>
            <LoginButton />
          </div>

          <WorkflowsList userId={userId} />
        </main>
      </div>
    </ProtectedRoute>
  );
}
