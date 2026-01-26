'use client';

import { cn } from '@/lib/utils';
import { type ReactNode } from 'react';

interface TuiStatusBarProps {
  left?: ReactNode;
  center?: ReactNode;
  right?: ReactNode;
  className?: string;
  position?: 'top' | 'bottom';
}

export function TuiStatusBar({
  left,
  center,
  right,
  className,
  position = 'bottom',
}: TuiStatusBarProps) {
  return (
    <div
      className={cn(
        'font-mono text-xs flex items-center justify-between px-4 py-1',
        'bg-[var(--tui-border)] text-[var(--tui-fg)]',
        position === 'top' && 'border-b border-[var(--tui-border)]',
        position === 'bottom' && 'border-t border-[var(--tui-border)]',
        className
      )}
    >
      <div className="flex items-center gap-4">{left}</div>
      <div className="flex items-center gap-4">{center}</div>
      <div className="flex items-center gap-4">{right}</div>
    </div>
  );
}
