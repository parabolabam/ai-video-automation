'use client';

import { UnifiedWorkflowEditor } from '@/components/unified-workflow-editor';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { AppShell } from '@/components/layout';
import { useAuth } from '@/lib/auth-context';
import { useWorkflow } from '@/hooks/use-workflows';
import { useParams, useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function WorkflowPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const userId = params.userId as string;
  const workflowId = params.workflowId as string;
  const { data: workflow } = useWorkflow(workflowId);

  useEffect(() => {
    // If authenticated but trying to access another user's workflow, redirect
    if (user && user.id !== userId) {
      router.push(`/user/${user.id}`);
    }
  }, [user, userId, router]);

  const breadcrumbs = [
    { label: workflow?.name || 'Workflow', isCurrentPage: true },
  ];

  return (
    <ProtectedRoute>
      <AppShell
        breadcrumbs={breadcrumbs}
        homeHref={`/user/${userId}`}
        fullHeight
      >
        <UnifiedWorkflowEditor workflowId={workflowId} userId={userId} />
      </AppShell>
    </ProtectedRoute>
  );
}
