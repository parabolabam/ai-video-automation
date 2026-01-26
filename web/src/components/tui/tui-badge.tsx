'use client';

import { cn } from '@/lib/utils';
import { type ReactNode } from 'react';

interface TuiBadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  className?: string;
}

export function TuiBadge({ children, variant = 'default', className }: TuiBadgeProps) {
  const getVariantStyles = () => {
    switch (variant) {
      case 'success':
        return 'text-[var(--tui-green)] border-[var(--tui-green)]';
      case 'warning':
        return 'text-[var(--tui-yellow)] border-[var(--tui-yellow)]';
      case 'error':
        return 'text-[var(--tui-red)] border-[var(--tui-red)]';
      case 'info':
        return 'text-[var(--tui-cyan)] border-[var(--tui-cyan)]';
      default:
        return 'text-[var(--tui-dim)] border-[var(--tui-dim)]';
    }
  };

  return (
    <span
      className={cn(
        'font-mono text-xs uppercase tracking-wider',
        getVariantStyles(),
        className
      )}
    >
      [{children}]
    </span>
  );
}
