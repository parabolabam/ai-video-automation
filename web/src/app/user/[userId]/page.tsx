import { WorkflowsList } from '@/components/workflows-list';

export default async function UserDashboard({ params }: { params: Promise<{ userId: string }> }) {
  const { userId } = await params;

  return (
    <div className="min-h-screen p-8 font-[family-name:var(--font-geist-sans)]">
      <main className="max-w-6xl mx-auto space-y-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Agent Workflows</h1>
            <p className="text-muted-foreground mt-2">
              User ID: <code className="bg-muted px-1 py-0.5 rounded">{userId}</code>
            </p>
          </div>
        </div>
        
        <WorkflowsList userId={userId} />
      </main>
    </div>
  );
}
