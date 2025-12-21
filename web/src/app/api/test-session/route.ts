import { NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase-server';

export async function GET() {
  const supabase = await createClient();
  const { data: { session }, error } = await supabase.auth.getSession();

  return NextResponse.json({
    hasSession: !!session,
    userId: session?.user?.id,
    error: error?.message,
    cookies: session ? 'Session cookies present' : 'No session cookies found'
  });
}
