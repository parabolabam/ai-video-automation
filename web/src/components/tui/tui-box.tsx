'use client';

import { cn } from '@/lib/utils';
import { type ReactNode } from 'react';

interface TuiBoxProps {
  title?: string;
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'highlight' | 'success' | 'error' | 'warning';
}

export function TuiBox({ title, children, className, variant = 'default' }: TuiBoxProps) {
  const getVariantStyles = () => {
    switch (variant) {
      case 'highlight':
        return 'border-[var(--tui-cyan)] text-[var(--tui-cyan)]';
      case 'success':
        return 'border-[var(--tui-green)] text-[var(--tui-green)]';
      case 'error':
        return 'border-[var(--tui-red)] text-[var(--tui-red)]';
      case 'warning':
        return 'border-[var(--tui-yellow)] text-[var(--tui-yellow)]';
      default:
        return 'border-[var(--tui-border)]';
    }
  };

  const borderColor = getVariantStyles();

  // Calculate title display
  const titleDisplay = title ? ` ${title} ` : '';
  const topLeftCorner = '┌';
  const topRightCorner = '┐';
  const bottomLeftCorner = '└';
  const bottomRightCorner = '┘';
  const horizontalLine = '─';
  const verticalLine = '│';

  return (
    <div className={cn('font-mono text-sm', className)}>
      {/* Top border with optional title */}
      <div className={cn('flex items-center', borderColor)}>
        <span>{topLeftCorner}</span>
        {title && (
          <>
            <span>{horizontalLine}</span>
            <span className="px-1">{title}</span>
          </>
        )}
        <span className="flex-1 overflow-hidden">
          {Array(50).fill(horizontalLine).join('')}
        </span>
        <span>{topRightCorner}</span>
      </div>

      {/* Content with side borders */}
      <div className={cn('relative', borderColor)}>
        <div className="flex">
          <span className={borderColor}>{verticalLine}</span>
          <div className="flex-1 px-2 py-1 text-[var(--tui-fg)]">{children}</div>
          <span className={borderColor}>{verticalLine}</span>
        </div>
      </div>

      {/* Bottom border */}
      <div className={cn('flex items-center', borderColor)}>
        <span>{bottomLeftCorner}</span>
        <span className="flex-1 overflow-hidden">
          {Array(50).fill(horizontalLine).join('')}
        </span>
        <span>{bottomRightCorner}</span>
      </div>
    </div>
  );
}
