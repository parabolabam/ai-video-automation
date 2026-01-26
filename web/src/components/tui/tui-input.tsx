'use client';

import { cn } from '@/lib/utils';
import { forwardRef, type InputHTMLAttributes } from 'react';

interface TuiInputProps extends InputHTMLAttributes<HTMLInputElement> {
  prefix?: string;
  label?: string;
}

export const TuiInput = forwardRef<HTMLInputElement, TuiInputProps>(
  ({ className, prefix = '>', label, disabled, ...props }, ref) => {
    return (
      <div className="font-mono">
        {label && (
          <label className="block text-xs text-[var(--tui-dim)] uppercase tracking-wider mb-1">
            {label}
          </label>
        )}
        <div
          className={cn(
            'flex items-center border border-[var(--tui-border)] bg-[var(--tui-bg)]',
            'focus-within:border-[var(--tui-cyan)]',
            disabled && 'opacity-50',
            className
          )}
        >
          <span className="text-[var(--tui-cyan)] px-2 select-none">{prefix}</span>
          <input
            ref={ref}
            disabled={disabled}
            className={cn(
              'flex-1 bg-transparent py-2 pr-2 text-sm text-[var(--tui-fg)]',
              'placeholder:text-[var(--tui-dim)]',
              'focus:outline-none',
              'disabled:cursor-not-allowed'
            )}
            {...props}
          />
          <span className="text-[var(--tui-cyan)] pr-2 tui-blink">_</span>
        </div>
      </div>
    );
  }
);

TuiInput.displayName = 'TuiInput';
