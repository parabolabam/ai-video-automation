'use client';

import { cn } from '@/lib/utils';
import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';

interface TuiButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'default' | 'primary' | 'destructive' | 'ghost';
  size?: 'sm' | 'default' | 'lg';
  keybind?: string;
}

export const TuiButton = forwardRef<HTMLButtonElement, TuiButtonProps>(
  ({ children, className, variant = 'default', size = 'default', keybind, disabled, ...props }, ref) => {
    const getVariantStyles = () => {
      if (disabled) {
        return 'text-[var(--tui-dim)] cursor-not-allowed';
      }
      switch (variant) {
        case 'primary':
          return 'text-[var(--tui-cyan)] hover:bg-[var(--tui-cyan)] hover:text-[var(--tui-bg)]';
        case 'destructive':
          return 'text-[var(--tui-red)] hover:bg-[var(--tui-red)] hover:text-[var(--tui-bg)]';
        case 'ghost':
          return 'text-[var(--tui-fg)] hover:text-[var(--tui-cyan)]';
        default:
          return 'text-[var(--tui-fg)] hover:bg-[var(--tui-fg)] hover:text-[var(--tui-bg)]';
      }
    };

    const getSizeStyles = () => {
      switch (size) {
        case 'sm':
          return 'text-xs px-1';
        case 'lg':
          return 'text-base px-3';
        default:
          return 'text-sm px-2';
      }
    };

    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(
          'font-mono inline-flex items-center justify-center gap-2 transition-colors duration-100',
          getSizeStyles(),
          getVariantStyles(),
          className
        )}
        {...props}
      >
        <span>[</span>
        <span className="whitespace-nowrap">{children}</span>
        <span>]</span>
        {keybind && (
          <span className="text-[var(--tui-dim)] text-xs ml-1">[{keybind}]</span>
        )}
      </button>
    );
  }
);

TuiButton.displayName = 'TuiButton';
