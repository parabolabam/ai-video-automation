'use client';

import Link from 'next/link';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  isCurrentPage?: boolean;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  homeHref?: string;
  className?: string;
}

function truncateLabel(label: string, maxLength = 20): string {
  if (label.length <= maxLength) return label;
  return `${label.slice(0, maxLength)}...`;
}

export function Breadcrumbs({ items, homeHref = '/', className }: BreadcrumbsProps) {
  return (
    <nav aria-label="Breadcrumb" className={cn('flex items-center space-x-1 text-sm', className)}>
      <Link
        href={homeHref}
        className="flex items-center text-muted-foreground hover:text-foreground transition-colors"
        aria-label="Home"
      >
        <Home className="h-4 w-4" />
      </Link>

      {items.map((item, index) => (
        <div key={index} className="flex items-center">
          <ChevronRight className="h-4 w-4 text-muted-foreground mx-1" />
          {item.isCurrentPage || !item.href ? (
            <span
              className="text-foreground font-medium"
              aria-current={item.isCurrentPage ? 'page' : undefined}
            >
              {truncateLabel(item.label)}
            </span>
          ) : (
            <Link
              href={item.href}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              {truncateLabel(item.label)}
            </Link>
          )}
        </div>
      ))}
    </nav>
  );
}
