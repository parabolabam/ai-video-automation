'use client';

import { useAuth } from '@/lib/auth-context';
import { ConnectAccounts } from '@/components/ConnectAccounts';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import Link from 'next/link';

export default function SettingsPage() {
  const { user, loading, signInWithGoogle, signOut } = useAuth();

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-6">
        <Link href="/" className="text-blue-600 hover:underline">
          &larr; Back to Dashboard
        </Link>
      </div>

      <h1 className="text-3xl font-bold mb-8">Settings</h1>

      <div className="space-y-6">
        {/* Account Section */}
        <Card>
          <CardHeader>
            <CardTitle>Account</CardTitle>
            <CardDescription>Manage your account settings</CardDescription>
          </CardHeader>
          <CardContent>
            {user ? (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {user.user_metadata?.avatar_url && (
                    <img
                      src={user.user_metadata.avatar_url}
                      alt="Profile"
                      className="w-12 h-12 rounded-full"
                    />
                  )}
                  <div>
                    <div className="font-medium">
                      {user.user_metadata?.full_name || user.email}
                    </div>
                    <div className="text-sm text-gray-500">{user.email}</div>
                  </div>
                </div>
                <Button variant="outline" onClick={() => signOut()}>
                  Sign Out
                </Button>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-gray-600 mb-4">Sign in to access your settings</p>
                <Button onClick={() => signInWithGoogle()}>Sign in with Google</Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Connected Accounts Section */}
        <ConnectAccounts />

        {/* Publishing Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Publishing Settings</CardTitle>
            <CardDescription>Configure default publishing options</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 text-gray-500">
              <p>Default publishing settings coming soon...</p>
              <ul className="list-disc list-inside text-sm">
                <li>Default privacy settings</li>
                <li>Auto-generated hashtags</li>
                <li>Default posting schedule</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
