'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface ConnectedAccount {
  id: string;
  platform: string;
  account_name: string;
  account_image_url?: string;
  connected_at: string;
  is_active: boolean;
}

export function ConnectAccounts() {
  const { session, user } = useAuth();
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    if (user) {
      fetchAccounts();
    }
  }, [user]);

  // Check for OAuth callback parameters
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const connected = params.get('connected');
    const errorParam = params.get('error');

    if (connected) {
      // Clear URL params and refresh
      window.history.replaceState({}, '', window.location.pathname);
      fetchAccounts();
    }

    if (errorParam) {
      setError(`Failed to connect: ${errorParam}`);
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  const fetchAccounts = async () => {
    if (!user) return;

    try {
      setLoading(true);
      const resp = await fetch(
        `${apiUrl}/api/oauth/accounts?user_id=${user.id}`,
        {
          headers: session?.access_token
            ? { Authorization: `Bearer ${session.access_token}` }
            : {},
        }
      );
      const data = await resp.json();
      setAccounts(data.accounts || []);
      setError(null);
    } catch (e) {
      console.error('Failed to fetch accounts', e);
      setError('Failed to load connected accounts');
    } finally {
      setLoading(false);
    }
  };

  const connect = (platform: string) => {
    if (!user) return;
    window.location.href = `${apiUrl}/api/oauth/${platform}/authorize?user_id=${user.id}`;
  };

  const disconnect = async (accountId: string) => {
    if (!user) return;

    try {
      await fetch(`${apiUrl}/api/oauth/accounts/${accountId}?user_id=${user.id}`, {
        method: 'DELETE',
        headers: session?.access_token
          ? { Authorization: `Bearer ${session.access_token}` }
          : {},
      });
      fetchAccounts();
    } catch (e) {
      console.error('Failed to disconnect', e);
      setError('Failed to disconnect account');
    }
  };

  const getAccountsForPlatform = (platform: string) =>
    accounts.filter((a) => a.platform === platform);

  if (!user) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Connected Accounts</CardTitle>
          <CardDescription>Sign in to manage your connected accounts</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Connected Accounts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const youtubeAccounts = getAccountsForPlatform('youtube');

  return (
    <Card>
      <CardHeader>
        <CardTitle>Connected Accounts</CardTitle>
        <CardDescription>
          Connect your social media accounts to publish videos directly
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <div className="p-3 text-sm text-red-600 bg-red-50 rounded-md">{error}</div>
        )}

        {/* YouTube */}
        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-red-600 rounded-full flex items-center justify-center text-white font-bold">
                YT
              </div>
              <div>
                <div className="font-medium">YouTube</div>
                {youtubeAccounts.length > 0 ? (
                  <div className="text-sm text-green-600">
                    {youtubeAccounts.length} account(s) connected
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">Not connected</div>
                )}
              </div>
            </div>
            <Button
              onClick={() => connect('youtube')}
              variant={youtubeAccounts.length > 0 ? 'outline' : 'default'}
              className={youtubeAccounts.length > 0 ? '' : 'bg-red-600 hover:bg-red-700'}
            >
              {youtubeAccounts.length > 0 ? 'Add Another' : 'Connect YouTube'}
            </Button>
          </div>

          {/* List connected YouTube accounts */}
          {youtubeAccounts.length > 0 && (
            <div className="mt-4 space-y-2">
              {youtubeAccounts.map((account) => (
                <div
                  key={account.id}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded"
                >
                  <div className="flex items-center gap-2">
                    {account.account_image_url ? (
                      <img
                        src={account.account_image_url}
                        alt={account.account_name}
                        className="w-8 h-8 rounded-full"
                      />
                    ) : (
                      <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
                    )}
                    <span className="font-medium">{account.account_name}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => disconnect(account.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    Disconnect
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Instagram - Coming Soon */}
        <div className="border rounded-lg p-4 opacity-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold">
                IG
              </div>
              <div>
                <div className="font-medium">Instagram</div>
                <div className="text-sm text-gray-500">Coming soon</div>
              </div>
            </div>
            <Button disabled variant="outline">
              Connect Instagram
            </Button>
          </div>
        </div>

        {/* TikTok - Coming Soon */}
        <div className="border rounded-lg p-4 opacity-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-black rounded-full flex items-center justify-center text-white font-bold">
                TT
              </div>
              <div>
                <div className="font-medium">TikTok</div>
                <div className="text-sm text-gray-500">Coming soon</div>
              </div>
            </div>
            <Button disabled variant="outline">
              Connect TikTok
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
