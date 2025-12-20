import { WorkflowEditor } from '@/components/workflow-editor';

export default async function WorkflowEditPage({ params }: { params: Promise<{ userId: string, workflowId: string }> }) {
  const { userId, workflowId } = await params;
  
  return (
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
  );
}
