'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Menu, Home, Settings, LogOut } from 'lucide-react';
import { BreadcrumbItem } from './breadcrumbs';

interface MobileNavProps {
  breadcrumbs?: BreadcrumbItem[];
  homeHref?: string;
}

export function MobileNav({ breadcrumbs = [], homeHref = '/' }: MobileNavProps) {
  const [open, setOpen] = useState(false);
  const { user, signOut } = useAuth();

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-72">
        <SheetHeader>
          <SheetTitle>Navigation</SheetTitle>
        </SheetHeader>
        <nav className="flex flex-col gap-2 mt-4">
          <Link
            href={homeHref}
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-2 py-2 rounded-md hover:bg-accent"
          >
            <Home className="h-4 w-4" />
            Home
          </Link>

          {breadcrumbs.map((item, index) => (
            item.href && (
              <Link
                key={index}
                href={item.href}
                onClick={() => setOpen(false)}
                className="flex items-center gap-2 px-2 py-2 rounded-md hover:bg-accent pl-6"
              >
                {item.label}
              </Link>
            )
          ))}

          <div className="border-t my-2" />

          <Link
            href="/settings"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-2 py-2 rounded-md hover:bg-accent"
          >
            <Settings className="h-4 w-4" />
            Settings
          </Link>

          {user && (
            <button
              onClick={() => {
                signOut();
                setOpen(false);
              }}
              className="flex items-center gap-2 px-2 py-2 rounded-md hover:bg-accent text-destructive"
            >
              <LogOut className="h-4 w-4" />
              Sign Out
            </button>
          )}
        </nav>
      </SheetContent>
    </Sheet>
  );
}
