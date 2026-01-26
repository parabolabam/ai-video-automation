'use client';

import Link from 'next/link';
import { Breadcrumbs, BreadcrumbItem } from './breadcrumbs';
import { UserMenu } from './user-menu';
import { MobileNav } from './mobile-nav';
import { Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface NavbarProps {
  breadcrumbs?: BreadcrumbItem[];
  homeHref?: string;
}

export function Navbar({ breadcrumbs = [], homeHref = '/' }: NavbarProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4 gap-4">
        {/* Mobile hamburger menu */}
        <MobileNav breadcrumbs={breadcrumbs} homeHref={homeHref} />

        {/* Logo */}
        <Link href={homeHref} className="flex items-center gap-2 font-semibold">
          <div className="w-8 h-8 rounded-md bg-primary flex items-center justify-center text-primary-foreground text-sm font-bold">
            AI
          </div>
          <span className="hidden sm:inline">Video Automation</span>
        </Link>

        {/* Breadcrumbs - hidden on mobile */}
        <div className="hidden md:flex flex-1 items-center">
          {breadcrumbs.length > 0 && (
            <Breadcrumbs items={breadcrumbs} homeHref={homeHref} className="ml-4" />
          )}
        </div>

        {/* Spacer for mobile */}
        <div className="flex-1 md:hidden" />

        {/* Right side actions */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" asChild className="hidden sm:flex">
            <Link href="/settings">
              <Settings className="h-4 w-4" />
              <span className="sr-only">Settings</span>
            </Link>
          </Button>
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
