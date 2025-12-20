'use client';

import { WorkflowEditor } from '@/components/workflow-editor';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { useAuth } from '@/lib/auth-context';
import { useParams, useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function WorkflowEditPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const userId = params.userId as string;
  const workflowId = params.workflowId as string;

  useEffect(() => {
    // If authenticated but trying to access another user's workflow, redirect
    if (user && user.id !== userId) {
      router.push(`/user/${user.id}`);
    }
  }, [user, userId, router]);

  return (
    <ProtectedRoute>
      <div className="h-screen flex flex-col p-4 font-[family-name:var(--font-geist-sans)]">
        <div className="mb-4">
          <h1 className="text-2xl font-bold">Workflow Editor</h1>
          <div className="flex gap-2 text-sm text-muted-foreground">
            <span>Editing Mode</span>
            <span>•</span>
            <span>Flow: {workflowId.slice(0,8)}</span>
          </div>
        </div>

        <div className="flex-1 border rounded-lg overflow-hidden">
          <WorkflowEditor userId={userId} workflowId={workflowId} />
        </div>
      </div>
    </ProtectedRoute>
  );
}
