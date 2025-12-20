'use client';

import Link from 'next/link';
import { trpc } from '@/lib/trpc';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Loader2, Play, AlertCircle } from 'lucide-react';
import { useState, useTransition } from 'react';
import { runWorkflow as runWorkflowAction } from '@/app/actions/workflow';

export function WorkflowsList({ userId }: { userId?: string }) {
  const { data: workflows, isLoading, error } = trpc.workflow.list.useQuery(userId ? { userId } : undefined);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [openDialogId, setOpenDialogId] = useState<string | null>(null);
  const [inputTopic, setInputTopic] = useState("");
  const [isPending, startTransition] = useTransition();

  const handleRunWorkflow = async (id: string, wfUserId: string) => {
    setRunningId(id);
    setOpenDialogId(null); // Close dialog

    startTransition(async () => {
      try {
        // Use Server Action instead of direct fetch
        const result = await runWorkflowAction({
          workflowId: id,
          userId: wfUserId,
          input: inputTopic || "No input provided",
        });

        if (result.success) {
          console.log('Run result:', result.data);
          alert(`Workflow started for topic: "${inputTopic}"\nCheck logs!`);
        } else {
          console.error('Workflow error:', result.error);
          alert(`Failed to start workflow: ${result.error}`);
        }
      } catch (err) {
        console.error(err);
        alert('Failed to start workflow');
      } finally {
        setRunningId(null);
        setInputTopic(""); // Reset input
      }
    });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 p-4 text-destructive bg-destructive/10 rounded-md">
        <AlertCircle className="h-4 w-4" />
        <p>Error loading workflows: {error.message}</p>
      </div>
    );
  }

  if (!workflows || workflows.length === 0) {
    return (
      <div className="text-center p-8 border rounded-lg border-dashed">
        <h3 className="text-lg font-medium">No Workflows Found</h3>
        <p className="text-muted-foreground">Create your first workflow to get started.</p>
        <Button className="mt-4" variant="outline">Create Workflow</Button>
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {workflows.map((wf) => (
        <Card key={wf.id} className="hover:shadow-md transition-shadow">
          <CardHeader className="pb-2">
            <div className="flex justify-between items-start">
              <CardTitle className="text-lg">{wf.name}</CardTitle>
              <Badge variant={wf.active ? 'default' : 'secondary'}>
                {wf.active ? 'Active' : 'Inactive'}
              </Badge>
            </div>
            <CardDescription>{wf.description || 'No description provided'}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex justify-between items-center pt-4">
              <Dialog open={openDialogId === wf.id} onOpenChange={(open) => setOpenDialogId(open ? wf.id : null)}>
                <DialogTrigger asChild>
                  <Button
                    size="sm"
                    variant="default"
                    disabled={runningId !== null}
                  >
                    {runningId === wf.id ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Running...</>
                    ) : (
                      <><Play className="mr-2 h-4 w-4" /> Run</>
                    )}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Run Workflow: {wf.name}</DialogTitle>
                    <DialogDescription>
                      Enter your input prompt for this workflow
                    </DialogDescription>
                  </DialogHeader>
                  <div className="py-4">
                    <Label htmlFor="input">Input Topic</Label>
                    <Input
                      id="input"
                      value={inputTopic}
                      onChange={(e) => setInputTopic(e.target.value)}
                      placeholder="e.g., AI advancements in 2024"
                    />
                  </div>
                  <DialogFooter>
                    <Button onClick={() => handleRunWorkflow(wf.id, wf.user_id)}>
                      Start Workflow
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <div className="flex gap-2">
                <Link href={`/user/${wf.user_id}/workflow/${wf.id}`}>
                  <Button size="sm" variant="outline">
                    Visualizer
                  </Button>
                </Link>
                <Link href={`/user/${wf.user_id}/workflow/${wf.id}/edit`}>
                  <Button size="sm" variant="outline">
                    Edit
                  </Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
