'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function WorkflowEditPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.workflowId as string;
  const userId = params.userId as string;

  // Redirect to the unified editor (main workflow page)
  useEffect(() => {
    router.replace(`/user/${userId}/workflow/${workflowId}`);
  }, [userId, workflowId, router]);

  return (
    <div className="h-screen w-screen flex items-center justify-center font-mono text-muted-foreground">
      Redirecting...
    </div>
  );
}
