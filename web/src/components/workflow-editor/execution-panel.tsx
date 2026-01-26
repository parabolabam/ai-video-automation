'use client';

import { useEffect, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Terminal, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export interface LogEntry {
  timestamp: Date;
  message: string;
  type: 'info' | 'success' | 'error' | 'dry-run';
  agentName?: string;
}

interface ExecutionPanelProps {
  logs: LogEntry[];
  onClear?: () => void;
  className?: string;
}

export function ExecutionPanel({ logs, onClear, className }: ExecutionPanelProps) {
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const getLogStyles = (type: LogEntry['type']) => {
    switch (type) {
      case 'success':
        return 'text-green-400';
      case 'error':
        return 'text-red-400';
      case 'dry-run':
        return 'text-yellow-400';
      default:
        return 'text-neutral-300';
    }
  };

  const getLogPrefix = (type: LogEntry['type']) => {
    switch (type) {
      case 'success':
        return '[OK]';
      case 'error':
        return '[ERR]';
      case 'dry-run':
        return '[DRY]';
      default:
        return '[LOG]';
    }
  };

  return (
    <div className={cn('flex flex-col h-full font-mono text-sm', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-neutral-800 bg-neutral-900/50">
        <div className="flex items-center gap-2 text-neutral-400">
          <Terminal className="w-4 h-4" />
          <span className="text-xs uppercase tracking-wider">Live Logs</span>
        </div>
        {onClear && logs.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClear}
            className="h-6 px-2 text-xs text-neutral-500 hover:text-neutral-300"
          >
            <Trash2 className="w-3 h-3 mr-1" />
            Clear
          </Button>
        )}
      </div>

      {/* Logs */}
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-1">
          {logs.length === 0 ? (
            <div className="text-neutral-500 text-xs text-center py-8">
              No logs yet. Run the workflow to see output.
            </div>
          ) : (
            logs.map((log, i) => (
              <div
                key={i}
                className={cn(
                  'break-words border-b border-neutral-900 pb-1 mb-1 last:border-0',
                  getLogStyles(log.type)
                )}
              >
                <span className="opacity-50 mr-2 text-xs">
                  {log.timestamp.toLocaleTimeString()}
                </span>
                <span className="opacity-70 mr-2 text-xs">
                  {getLogPrefix(log.type)}
                </span>
                {log.agentName && (
                  <span className="text-cyan-400 mr-1">[{log.agentName}]</span>
                )}
                {log.message}
              </div>
            ))
          )}
          <div ref={logEndRef} />
        </div>
      </ScrollArea>
    </div>
  );
}
