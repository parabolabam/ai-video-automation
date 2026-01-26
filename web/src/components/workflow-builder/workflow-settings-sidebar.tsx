'use client';

import { useState, useEffect } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Loader2, Save } from 'lucide-react';
import { ScheduleConfig } from './schedule-config';
import { useAuth } from '@/lib/auth-context';

interface WorkflowSettingsSidebarProps {
  open: boolean;
  onClose: () => void;
  workflowId: string;
  initialData?: {
    name: string;
    description: string | null;
    active: boolean;
  };
  onSave?: () => void;
}

export function WorkflowSettingsSidebar({
  open,
  onClose,
  workflowId,
  initialData,
  onSave,
}: WorkflowSettingsSidebarProps) {
  const { session } = useAuth();
  const [description, setDescription] = useState(initialData?.description || '');
  const [isActive, setIsActive] = useState(initialData?.active ?? true);
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [cronExpression, setCronExpression] = useState('0 9 * * *');
  const [saving, setSaving] = useState(false);
  const [loadingSchedule, setLoadingSchedule] = useState(true);
  const [existingJobId, setExistingJobId] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Update local state when initialData changes
  useEffect(() => {
    if (initialData) {
      setDescription(initialData.description || '');
      setIsActive(initialData.active ?? true);
    }
  }, [initialData]);

  // Load existing schedule on mount
  useEffect(() => {
    const loadSchedule = async () => {
      if (!session?.access_token || !open) return;

      try {
        const response = await fetch(`${apiUrl}/api/cron/jobs`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          // Find job for this workflow - backend returns workflow_id directly on job
          const existingJob = data.jobs?.find(
            (job: { workflow_id?: string; job_id: string; schedule: string }) =>
              job.workflow_id === workflowId
          );

          if (existingJob) {
            setExistingJobId(existingJob.job_id);
            setScheduleEnabled(true);
            setCronExpression(existingJob.schedule || '0 9 * * *');
          }
        }
      } catch (error) {
        console.error('Error loading schedule:', error);
      } finally {
        setLoadingSchedule(false);
      }
    };

    loadSchedule();
  }, [session?.access_token, workflowId, apiUrl, open]);

  const handleSave = async () => {
    if (!session?.access_token) return;

    setSaving(true);

    try {
      // Update workflow metadata
      const updateResponse = await fetch(`${apiUrl}/api/workflows/${workflowId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          description,
          is_active: isActive,
        }),
      });

      if (!updateResponse.ok) {
        const errorData = await updateResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to update workflow: ${updateResponse.status}`);
      }

      // Handle schedule
      if (scheduleEnabled) {
        if (existingJobId) {
          // Delete existing job and create new one with updated schedule
          await fetch(`${apiUrl}/api/cron/jobs/${existingJobId}`, {
            method: 'DELETE',
            headers: {
              Authorization: `Bearer ${session.access_token}`,
            },
          });
        }

        // Create new cron job
        const scheduleResponse = await fetch(`${apiUrl}/api/cron/jobs/cron`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({
            cron_expression: cronExpression,
            input: { workflow_id: workflowId },
          }),
        });

        if (scheduleResponse.ok) {
          const scheduleData = await scheduleResponse.json();
          setExistingJobId(scheduleData.job?.job_id || null);
        }
      } else if (existingJobId) {
        // Delete existing job if schedule is disabled
        await fetch(`${apiUrl}/api/cron/jobs/${existingJobId}`, {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });
        setExistingJobId(null);
      }

      onSave?.();
      onClose();
    } catch (error) {
      console.error('Error saving settings:', error);
      alert(
        `Error saving settings: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent className="w-[400px] sm:w-[450px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Workflow Settings</SheetTitle>
          <SheetDescription>
            Configure workflow description, status, and scheduling
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this workflow does..."
              rows={4}
            />
          </div>

          <Separator />

          {/* Status */}
          <div className="space-y-4">
            <h4 className="text-sm font-medium">Status</h4>
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="active-toggle">Active</Label>
                <p className="text-xs text-muted-foreground">
                  Enable or disable this workflow
                </p>
              </div>
              <Switch
                id="active-toggle"
                checked={isActive}
                onCheckedChange={setIsActive}
              />
            </div>
          </div>

          <Separator />

          {/* Schedule */}
          <div className="space-y-4">
            <h4 className="text-sm font-medium">Schedule</h4>
            {loadingSchedule ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading schedule...
              </div>
            ) : (
              <ScheduleConfig
                enabled={scheduleEnabled}
                cronExpression={cronExpression}
                onEnabledChange={setScheduleEnabled}
                onCronChange={setCronExpression}
              />
            )}
          </div>

          <Separator />

          {/* Save Button */}
          <Button onClick={handleSave} disabled={saving} className="w-full">
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Settings
              </>
            )}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
