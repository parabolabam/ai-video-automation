import { WorkflowVisualizer } from '@/components/workflow-visualizer';

export default async function WorkflowPage({ params }: { params: Promise<{ userId: string, workflowId: string }> }) {
  const { userId, workflowId } = await params;
  return (
    <div className="h-screen flex flex-col p-4 font-[family-name:var(--font-geist-sans)]">
      <div className="mb-4">
         <h1 className="text-2xl font-bold">Workflow Visualizer</h1>
         <div className="flex gap-2 text-sm text-muted-foreground">
           <span>User: {userId.slice(0,8)}</span>
           <span>•</span>
           <span>Flow: {workflowId.slice(0,8)}</span>
         </div>
      </div>
      
      <div className="flex-1">
        <WorkflowVisualizer userId={userId} workflowId={workflowId} />
      </div>
    </div>
  );
}
