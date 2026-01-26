'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Play, Loader2, FlaskConical } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RunControlsProps {
  onRun: (input: string, dryRun: boolean) => void;
  isRunning: boolean;
  disabled?: boolean;
  className?: string;
}

export function RunControls({ onRun, isRunning, disabled, className }: RunControlsProps) {
  const [inputTopic, setInputTopic] = useState('');
  const [dryRun, setDryRun] = useState(false);

  const handleRun = () => {
    if (inputTopic.trim()) {
      onRun(inputTopic, dryRun);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && inputTopic.trim() && !isRunning) {
      handleRun();
    }
  };

  return (
    <div className={cn('space-y-4', className)}>
      <div className="space-y-2">
        <Label htmlFor="topic-input" className="text-xs text-muted-foreground font-mono">
          INPUT TOPIC
        </Label>
        <Input
          id="topic-input"
          placeholder="Enter topic to process..."
          value={inputTopic}
          onChange={(e) => setInputTopic(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isRunning || disabled}
          className="font-mono text-sm"
        />
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Switch
            id="dry-run"
            checked={dryRun}
            onCheckedChange={setDryRun}
            disabled={isRunning || disabled}
          />
          <Label
            htmlFor="dry-run"
            className={cn(
              'text-sm font-mono cursor-pointer flex items-center gap-1',
              dryRun ? 'text-yellow-500' : 'text-muted-foreground'
            )}
          >
            <FlaskConical className="h-3 w-3" />
            Dry Run
          </Label>
        </div>
      </div>

      <Button
        onClick={handleRun}
        disabled={!inputTopic.trim() || isRunning || disabled}
        className="w-full font-mono"
        variant={dryRun ? 'outline' : 'default'}
      >
        {isRunning ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
            {dryRun ? 'Simulating...' : 'Running...'}
          </>
        ) : (
          <>
            <Play className="h-4 w-4 mr-2" />
            {dryRun ? '[ Dry Run ]' : '[ Run Workflow ]'}
          </>
        )}
      </Button>

      <p className="text-xs text-muted-foreground font-mono text-center">
        {dryRun ? 'No AI calls will be made' : 'Press Ctrl+Enter to run'}
      </p>
    </div>
  );
}
