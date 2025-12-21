'use client';

import { useEffect, useState, useTransition, useCallback } from 'react';
import { useAuth } from '@/lib/auth-context';
import {
  listCronJobs,
  createCronJob,
  triggerCronJob,
  pauseCronJob,
  resumeCronJob,
  deleteCronJob,
} from '@/app/actions/cron';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';

interface CronJob {
  job_id: string;
  name: string;
  workflow_id: string;
  user_id: string;
  input_text: string;
  schedule_type: string;
  schedule: string;
  next_run_time: string | null;
  paused: boolean;
  trigger: string;
}

export function CronJobsDashboard() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<CronJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [actioningJobId, setActioningJobId] = useState<string | null>(null);

  // Create job dialog state
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newJobId, setNewJobId] = useState('');
  const [newWorkflowId, setNewWorkflowId] = useState('');
  const [newInput, setNewInput] = useState('');
  const [newCronExpression, setNewCronExpression] = useState('0 */6 * * *');

  const loadJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    const result = await listCronJobs();

    if (result.success) {
      setJobs(result.data.jobs || []);
    } else {
      setError(result.error || 'Failed to load cron jobs');
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (!user) return;

    let cancelled = false;
    const fetchJobs = async () => {
      setLoading(true);
      setError(null);
      const result = await listCronJobs();

      if (!cancelled) {
        if (result.success) {
          setJobs(result.data.jobs || []);
        } else {
          setError(result.error || 'Failed to load cron jobs');
        }
        setLoading(false);
      }
    };

    fetchJobs();

    return () => {
      cancelled = true;
    };
  }, [user]);

  const handleCreateJob = async () => {
    if (!user || !newJobId || !newWorkflowId || !newCronExpression) {
      alert('Please fill in all required fields');
      return;
    }

    startTransition(async () => {
      const result = await createCronJob({
        job_id: newJobId,
        workflow_id: newWorkflowId,
        user_id: user.id,
        input: newInput,
        cron_expression: newCronExpression,
      });

      if (result.success) {
        setCreateDialogOpen(false);
        setNewJobId('');
        setNewWorkflowId('');
        setNewInput('');
        setNewCronExpression('0 */6 * * *');
        await loadJobs();
      } else {
        alert(`Error: ${result.error}`);
      }
    });
  };

  const handleTrigger = async (job_id: string) => {
    setActioningJobId(job_id);
    startTransition(async () => {
      const result = await triggerCronJob(job_id);
      if (result.success) {
        alert('Job triggered successfully!');
      } else {
        alert(`Error: ${result.error}`);
      }
      setActioningJobId(null);
    });
  };

  const handlePause = async (job_id: string) => {
    setActioningJobId(job_id);
    startTransition(async () => {
      const result = await pauseCronJob(job_id);
      if (result.success) {
        await loadJobs();
      } else {
        alert(`Error: ${result.error}`);
      }
      setActioningJobId(null);
    });
  };

  const handleResume = async (job_id: string) => {
    setActioningJobId(job_id);
    startTransition(async () => {
      const result = await resumeCronJob(job_id);
      if (result.success) {
        await loadJobs();
      } else {
        alert(`Error: ${result.error}`);
      }
      setActioningJobId(null);
    });
  };

  const handleDelete = async (job_id: string) => {
    if (!confirm(`Are you sure you want to delete job "${job_id}"?`)) {
      return;
    }

    setActioningJobId(job_id);
    startTransition(async () => {
      const result = await deleteCronJob(job_id);
      if (result.success) {
        await loadJobs();
      } else {
        alert(`Error: ${result.error}`);
      }
      setActioningJobId(null);
    });
  };

  if (loading) {
    return (
      <div className="border rounded-lg p-8">
        <div className="text-center text-muted-foreground">Loading cron jobs...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="border rounded-lg p-8 bg-destructive/10">
        <div className="text-center text-destructive">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Scheduled Jobs</h2>
          <p className="text-sm text-muted-foreground mt-1">
            {jobs.length} {jobs.length === 1 ? 'job' : 'jobs'} scheduled
          </p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>+ Create Job</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Cron Job</DialogTitle>
              <DialogDescription>
                Schedule a workflow to run automatically at specified times.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <Label htmlFor="job_id">Job ID *</Label>
                <input
                  id="job_id"
                  type="text"
                  className="w-full px-3 py-2 border rounded-md mt-1"
                  placeholder="my-daily-job"
                  value={newJobId}
                  onChange={(e) => setNewJobId(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="workflow_id">Workflow ID *</Label>
                <input
                  id="workflow_id"
                  type="text"
                  className="w-full px-3 py-2 border rounded-md mt-1"
                  placeholder="my-workflow"
                  value={newWorkflowId}
                  onChange={(e) => setNewWorkflowId(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="input">Input</Label>
                <textarea
                  id="input"
                  className="w-full px-3 py-2 border rounded-md mt-1"
                  placeholder="Input for the workflow"
                  rows={3}
                  value={newInput}
                  onChange={(e) => setNewInput(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="cron_expression">Cron Expression *</Label>
                <input
                  id="cron_expression"
                  type="text"
                  className="w-full px-3 py-2 border rounded-md mt-1"
                  placeholder="0 */6 * * *"
                  value={newCronExpression}
                  onChange={(e) => setNewCronExpression(e.target.value)}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Examples: &quot;0 */6 * * *&quot; (every 6 hours), &quot;0 9 * * *&quot; (daily at 9 AM)
                </p>
              </div>
              <Button
                onClick={handleCreateJob}
                disabled={isPending}
                className="w-full"
              >
                {isPending ? 'Creating...' : 'Create Job'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {jobs.length === 0 ? (
        <div className="border rounded-lg p-12 text-center">
          <p className="text-muted-foreground mb-4">No scheduled jobs yet</p>
          <Button onClick={() => setCreateDialogOpen(true)}>
            Create Your First Job
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <div
              key={job.job_id}
              className="border rounded-lg p-4 bg-card hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{job.job_id}</h3>
                    {job.paused && (
                      <span className="text-xs bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 px-2 py-0.5 rounded-full">
                        Paused
                      </span>
                    )}
                    <span className="text-xs bg-blue-500/10 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded-full">
                      {job.schedule_type}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    Workflow: <code className="bg-muted px-1 rounded">{job.workflow_id}</code>
                  </p>
                  <div className="mt-2 space-y-1">
                    <p className="text-xs text-muted-foreground">
                      Schedule: <span className="font-mono">{job.schedule}</span>
                    </p>
                    {job.next_run_time && (
                      <p className="text-xs text-muted-foreground">
                        Next run: {new Date(job.next_run_time).toLocaleString()}
                      </p>
                    )}
                    {job.input_text && (
                      <p className="text-xs text-muted-foreground">
                        Input: {job.input_text}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex gap-2 ml-4">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleTrigger(job.job_id)}
                    disabled={isPending && actioningJobId === job.job_id}
                  >
                    ▶ Run Now
                  </Button>
                  {job.paused ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleResume(job.job_id)}
                      disabled={isPending && actioningJobId === job.job_id}
                    >
                      ▶ Resume
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handlePause(job.job_id)}
                      disabled={isPending && actioningJobId === job.job_id}
                    >
                      ⏸ Pause
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDelete(job.job_id)}
                    disabled={isPending && actioningJobId === job.job_id}
                  >
                    🗑 Delete
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Separator className="my-4" />

      <div className="flex justify-between items-center text-sm text-muted-foreground">
        <p>Jobs auto-refresh on action</p>
        <Button variant="ghost" size="sm" onClick={loadJobs} disabled={loading}>
          ↻ Refresh
        </Button>
      </div>
    </div>
  );
}
