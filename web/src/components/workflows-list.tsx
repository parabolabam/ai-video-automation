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
import { Loader2, Play, AlertCircle, Plus, Trash2 } from 'lucide-react';
import { useState, useTransition } from 'react';
import { runWorkflow as runWorkflowAction, deleteWorkflow } from '@/app/actions/workflow';
import { useAuth } from '@/lib/auth-context';

export function WorkflowsList({ userId }: { userId?: string }) {
  const { data: workflows, isLoading, error, refetch } = trpc.workflow.list.useQuery(userId ? { userId } : undefined);
  const { session } = useAuth();
  const [runningId, setRunningId] = useState<string | null>(null);
  const [openDialogId, setOpenDialogId] = useState<string | null>(null);
  const [inputTopic, setInputTopic] = useState("");
  const [isPending, startTransition] = useTransition();

  // Create workflow dialog state
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newWorkflowName, setNewWorkflowName] = useState("");
  const [newWorkflowDescription, setNewWorkflowDescription] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleCreateWorkflow = async () => {
    if (!newWorkflowName.trim()) {
      alert('Please enter a workflow name');
      return;
    }

    if (!session?.access_token) {
      alert('Not authenticated. Please sign in again.');
      return;
    }

    startTransition(async () => {
      try {
        const response = await fetch('/api/workflows', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({
            name: newWorkflowName,
            description: newWorkflowDescription || undefined,
          }),
        });

        if (!response.ok) {
          const error = await response.json();
          alert(`Error: ${error.error || 'Failed to create workflow'}`);
          return;
        }

        const data = await response.json();
        setCreateDialogOpen(false);
        setNewWorkflowName("");
        setNewWorkflowDescription("");
        await refetch();
        alert('Workflow created successfully!');
      } catch (error) {
        console.error('Create workflow error:', error);
        alert(`Error: ${error instanceof Error ? error.message : 'Failed to create workflow'}`);
      }
    });
  };

  const handleDeleteWorkflow = async (id: string) => {
    if (!confirm('Are you sure you want to delete this workflow?')) {
      return;
    }

    setDeletingId(id);
    startTransition(async () => {
      const result = await deleteWorkflow(id);

      if (result.success) {
        await refetch();
      } else {
        alert(`Error: ${result.error}`);
      }
      setDeletingId(null);
    });
  };

  const handleRunWorkflow = async (id: string, wfUserId: string) => {
    console.log('Run workflow - Full session object:', JSON.stringify(session, null, 2));
    console.log('Run workflow - access_token:', session?.access_token);
    console.log('Run workflow - Has session?', !!session);
    console.log('Run workflow - Session keys:', session ? Object.keys(session) : 'null');

    if (!session?.access_token) {
      console.error('No access token - session:', session);
      alert(`Not authenticated. Session: ${session ? 'exists but no token' : 'null'}`);
      return;
    }

    setRunningId(id);
    setOpenDialogId(null); // Close dialog

    startTransition(async () => {
      try {
        // Call backend API directly with token
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/run`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({
            workflow_id: id,
            user_id: wfUserId,
            input: inputTopic || "No input provided",
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          alert(`Failed to start workflow: ${errorData.detail || `HTTP error ${response.status}`}`);
          return;
        }

        const data = await response.json();
        console.log('Run result:', data);
        alert(`Workflow started for topic: "${inputTopic}"\nCheck logs!`);
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
      <div className="space-y-4">
        <div className="flex justify-end">
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" /> Create Workflow
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Workflow</DialogTitle>
                <DialogDescription>
                  Create a new workflow to automate your video content generation.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 mt-4">
                <div>
                  <Label htmlFor="workflow_name">Workflow Name *</Label>
                  <Input
                    id="workflow_name"
                    type="text"
                    placeholder="My Workflow"
                    value={newWorkflowName}
                    onChange={(e) => setNewWorkflowName(e.target.value)}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="workflow_description">Description</Label>
                  <Input
                    id="workflow_description"
                    type="text"
                    placeholder="What does this workflow do?"
                    value={newWorkflowDescription}
                    onChange={(e) => setNewWorkflowDescription(e.target.value)}
                    className="mt-1"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  onClick={handleCreateWorkflow}
                  disabled={isPending || !newWorkflowName.trim()}
                >
                  {isPending ? 'Creating...' : 'Create Workflow'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
        <div className="text-center p-8 border rounded-lg border-dashed">
          <h3 className="text-lg font-medium">No Workflows Found</h3>
          <p className="text-muted-foreground">Create your first workflow to get started.</p>
          <Button className="mt-4" variant="outline" onClick={() => setCreateDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> Create Workflow
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" /> Create Workflow
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Workflow</DialogTitle>
              <DialogDescription>
                Create a new workflow to automate your video content generation.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <Label htmlFor="workflow_name">Workflow Name *</Label>
                <Input
                  id="workflow_name"
                  type="text"
                  placeholder="My Workflow"
                  value={newWorkflowName}
                  onChange={(e) => setNewWorkflowName(e.target.value)}
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="workflow_description">Description</Label>
                <Input
                  id="workflow_description"
                  type="text"
                  placeholder="What does this workflow do?"
                  value={newWorkflowDescription}
                  onChange={(e) => setNewWorkflowDescription(e.target.value)}
                  className="mt-1"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                onClick={handleCreateWorkflow}
                disabled={isPending || !newWorkflowName.trim()}
              >
                {isPending ? 'Creating...' : 'Create Workflow'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {workflows.map((wf) => (
          <Card key={wf.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-2">
              <div className="flex justify-between items-start">
                <CardTitle className="text-lg">{wf.name}</CardTitle>
                <div className="flex gap-2 items-center">
                  <Badge variant={wf.active ? 'default' : 'secondary'}>
                    {wf.active ? 'Active' : 'Inactive'}
                  </Badge>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDeleteWorkflow(wf.id)}
                    disabled={deletingId === wf.id}
                    className="h-6 w-6 p-0 text-destructive hover:text-destructive"
                  >
                    {deletingId === wf.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </Button>
                </div>
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
    </div>
  );
}
