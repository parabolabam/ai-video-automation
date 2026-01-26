'use client';

import { cn } from '@/lib/utils';
import { type ReactNode } from 'react';
import { TuiStatusBar } from './tui-status-bar';
import { TuiKeybindGroup } from './tui-keybind';

interface TuiLayoutProps {
  children: ReactNode;
  title?: string;
  userInfo?: string;
  keybindings?: Array<{ key: string; label: string }>;
  className?: string;
  showHeader?: boolean;
  showFooter?: boolean;
  headerLeft?: ReactNode;
  headerRight?: ReactNode;
  footerContent?: ReactNode;
}

export function TuiLayout({
  children,
  title = 'AI Video Automation',
  userInfo,
  keybindings = [],
  className,
  showHeader = true,
  showFooter = true,
  headerLeft,
  headerRight,
  footerContent,
}: TuiLayoutProps) {
  return (
    <div
      className={cn(
        'min-h-screen flex flex-col font-mono',
        'bg-[var(--tui-bg)] text-[var(--tui-fg)]',
        className
      )}
    >
      {/* Header */}
      {showHeader && (
        <TuiStatusBar
          position="top"
          left={
            headerLeft || (
              <span className="text-[var(--tui-cyan)] font-bold">
                ┌─ {title} ─
              </span>
            )
          }
          right={
            headerRight || (
              userInfo && (
                <span className="text-[var(--tui-dim)]">
                  ─ {userInfo} ─┐
                </span>
              )
            )
          }
        />
      )}

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">{children}</main>

      {/* Footer */}
      {showFooter && (
        <TuiStatusBar
          position="bottom"
          left={
            footerContent || (
              keybindings.length > 0 && <TuiKeybindGroup bindings={keybindings} />
            )
          }
          right={
            <span className="text-[var(--tui-dim)]">
              {new Date().toLocaleTimeString()}
            </span>
          }
        />
      )}
    </div>
  );
}
