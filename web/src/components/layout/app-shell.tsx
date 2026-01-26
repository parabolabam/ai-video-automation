'use client';

import { ReactNode } from 'react';
import { Navbar, BreadcrumbItem } from '@/components/navigation';
import { cn } from '@/lib/utils';

interface AppShellProps {
  children: ReactNode;
  breadcrumbs?: BreadcrumbItem[];
  homeHref?: string;
  fullHeight?: boolean;
  className?: string;
}

export function AppShell({
  children,
  breadcrumbs = [],
  homeHref,
  fullHeight = false,
  className,
}: AppShellProps) {
  return (
    <div className={cn('min-h-screen flex flex-col', fullHeight && 'h-screen')}>
      <Navbar breadcrumbs={breadcrumbs} homeHref={homeHref} />
      <main className={cn('flex-1', fullHeight && 'overflow-hidden', className)}>
        {children}
      </main>
    </div>
  );
}
