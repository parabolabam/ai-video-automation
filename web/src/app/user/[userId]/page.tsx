'use client';

import { WorkflowsList } from '@/components/workflows-list';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { TokenDisplay } from '@/components/auth/token-display';
import { CronJobsDashboard } from '@/components/cron-jobs-dashboard';
import { AppShell } from '@/components/layout';
import { useAuth } from '@/lib/auth-context';
import { useParams, useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function UserDashboard() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const userId = params.userId as string;

  useEffect(() => {
    // If authenticated but trying to access another user's dashboard, redirect to own dashboard
    if (user && user.id !== userId) {
      router.push(`/user/${user.id}`);
    }
  }, [user, userId, router]);

  return (
    <ProtectedRoute>
      <AppShell homeHref={`/user/${userId}`}>
        <div className="p-8 font-[family-name:var(--font-geist-sans)]">
          <main className="max-w-6xl mx-auto space-y-8">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Agent Workflows</h1>
              <p className="text-muted-foreground mt-2">
                Manage your AI agent workflows and automations
              </p>
            </div>

            <TokenDisplay />

            <CronJobsDashboard />

            <WorkflowsList userId={userId} />
          </main>
        </div>
      </AppShell>
    </ProtectedRoute>
  );
}
