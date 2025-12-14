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
import { useState } from 'react';

export function WorkflowsList({ userId }: { userId?: string }) {
  const { data: workflows, isLoading, error } = trpc.workflow.list.useQuery({ userId: userId || undefined });
  const [runningId, setRunningId] = useState<string | null>(null);
  const [openDialogId, setOpenDialogId] = useState<string | null>(null);
  const [inputTopic, setInputTopic] = useState("");

  const runWorkflow = async (id: string, wfUserId: string) => {
    setRunningId(id);
    setOpenDialogId(null); // Close dialog
    try {
      const res = await fetch('http://localhost:8000/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id: id,
          user_id: wfUserId, // Use the user_id from the workflow object itself, which is always string
          input: inputTopic || "No input provided"
        })
      });
      const json = await res.json();
      console.log('Run result:', json);
      alert(`Workflow started for topic: "${inputTopic}"\nCheck logs!`);
    } catch (err) {
      console.error(err);
      alert('Failed to start workflow');
    } finally {
      setRunningId(null);
      setInputTopic(""); // Reset input
    }
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
            <div className="flex justify-end pt-4">
               <Link href={`/user/${wf.user_id}/workflow/${wf.id}`}>
                 <Button size="sm">
                    <Play className="mr-2 h-4 w-4" />
                    Open Visualizer
                 </Button>
               </Link>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
