import { supabase } from './supabase';

/**
 * Get the current user's JWT access token
 * This token is needed for authenticated API calls
 */
export async function getAccessToken(): Promise<string | null> {
  const { data: { session }, error } = await supabase.auth.getSession();

  if (error) {
    console.error('Error getting session:', error);
    return null;
  }

  return session?.access_token || null;
}

/**
 * Get the full session including user and token
 */
export async function getSession() {
  const { data: { session }, error } = await supabase.auth.getSession();

  if (error) {
    console.error('Error getting session:', error);
    return null;
  }

  return session;
}

/**
 * Get token and format as Authorization header
 */
export async function getAuthHeader(): Promise<{ Authorization: string } | null> {
  const token = await getAccessToken();

  if (!token) {
    return null;
  }

  return {
    Authorization: `Bearer ${token}`
  };
}
