'use client';

import { useState, useEffect } from 'react';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Clock } from 'lucide-react';

interface ScheduleConfigProps {
  enabled: boolean;
  cronExpression?: string;
  onEnabledChange: (enabled: boolean) => void;
  onCronChange: (cron: string) => void;
}

const SCHEDULE_PRESETS = [
  { label: 'Every 6 hours', value: '0 */6 * * *' },
  { label: 'Daily at 9 AM', value: '0 9 * * *' },
  { label: 'Daily at 12 PM', value: '0 12 * * *' },
  { label: 'Weekly Monday 9 AM', value: '0 9 * * 1' },
  { label: 'Custom', value: 'custom' },
];

function getNextRun(cronExpression: string): string {
  // Simple approximation for display - in a real app, use a library like cronstrue
  const now = new Date();
  const parts = cronExpression.split(' ');

  if (parts.length !== 5) return 'Invalid cron expression';

  const [minute, hour] = parts;

  if (cronExpression === '0 */6 * * *') {
    const nextHour = Math.ceil(now.getHours() / 6) * 6;
    const next = new Date(now);
    next.setHours(nextHour >= 24 ? 6 : nextHour, 0, 0, 0);
    if (next <= now) next.setDate(next.getDate() + 1);
    return next.toLocaleString();
  }

  if (hour !== '*' && minute !== '*') {
    const next = new Date(now);
    next.setHours(parseInt(hour), parseInt(minute), 0, 0);
    if (next <= now) next.setDate(next.getDate() + 1);
    return next.toLocaleString();
  }

  return 'Calculated at runtime';
}

function getPresetFromCron(cron: string): string {
  const preset = SCHEDULE_PRESETS.find(p => p.value === cron);
  return preset ? preset.value : 'custom';
}

export function ScheduleConfig({
  enabled,
  cronExpression = '0 9 * * *',
  onEnabledChange,
  onCronChange,
}: ScheduleConfigProps) {
  const [preset, setPreset] = useState(() => getPresetFromCron(cronExpression));
  const [customCron, setCustomCron] = useState(cronExpression);

  useEffect(() => {
    if (preset !== 'custom') {
      onCronChange(preset);
    }
  }, [preset, onCronChange]);

  const handlePresetChange = (value: string) => {
    setPreset(value);
    if (value !== 'custom') {
      onCronChange(value);
    }
  };

  const handleCustomCronChange = (value: string) => {
    setCustomCron(value);
    onCronChange(value);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Label htmlFor="schedule-enabled" className="flex items-center gap-2">
          <Clock className="h-4 w-4" />
          Enable Schedule
        </Label>
        <Switch
          id="schedule-enabled"
          checked={enabled}
          onCheckedChange={onEnabledChange}
        />
      </div>

      {enabled && (
        <>
          <div className="space-y-2">
            <Label htmlFor="schedule-preset">Schedule</Label>
            <Select value={preset} onValueChange={handlePresetChange}>
              <SelectTrigger id="schedule-preset">
                <SelectValue placeholder="Select schedule" />
              </SelectTrigger>
              <SelectContent>
                {SCHEDULE_PRESETS.map((p) => (
                  <SelectItem key={p.value} value={p.value}>
                    {p.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {preset === 'custom' && (
            <div className="space-y-2">
              <Label htmlFor="custom-cron">Cron Expression</Label>
              <Input
                id="custom-cron"
                value={customCron}
                onChange={(e) => handleCustomCronChange(e.target.value)}
                placeholder="0 9 * * *"
                className="font-mono"
              />
              <p className="text-xs text-muted-foreground">
                Format: minute hour day month weekday
              </p>
            </div>
          )}

          <div className="text-sm text-muted-foreground bg-muted/50 p-2 rounded">
            <span className="font-medium">Next run:</span>{' '}
            {getNextRun(preset === 'custom' ? customCron : preset)}
          </div>
        </>
      )}
    </div>
  );
}
