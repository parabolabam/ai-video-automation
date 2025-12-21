'use client';

import { useParams } from 'next/navigation';
import { WorkflowBuilder } from '@/components/workflow-builder';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { LoginButton } from '@/components/auth/login-button';

export default function WorkflowEditPage() {
  const params = useParams();
  const workflowId = params.workflowId as string;
  const userId = params.userId as string;

  return (
    <ProtectedRoute>
      <div className="h-screen flex flex-col">
        <header className="border-b p-4 flex justify-between items-center bg-background">
          <div>
            <h1 className="text-2xl font-bold">Workflow Builder</h1>
            <p className="text-sm text-muted-foreground">
              Workflow ID: {workflowId}
            </p>
          </div>
          <LoginButton />
        </header>
        <main className="flex-1 overflow-hidden">
          <WorkflowBuilder workflowId={workflowId} userId={userId} />
        </main>
      </div>
    </ProtectedRoute>
  );
}
