import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'
import { cookies } from 'next/headers'

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')

  // Use NEXT_PUBLIC_SITE_URL for redirects to avoid reverse proxy issues
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || requestUrl.origin

  if (code) {
    const cookieStore = await cookies()

    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll() {
            return cookieStore.getAll()
          },
          setAll(cookiesToSet: { name: string; value: string; options: Record<string, unknown> }[]) {
            cookiesToSet.forEach(({ name, value, options }) => {
              cookieStore.set({
                name,
                value,
                ...options,
              })
            })
          },
        },
      }
    )

    const { data, error } = await supabase.auth.exchangeCodeForSession(code)

    if (!error && data?.session?.user) {
      // Redirect to user dashboard
      return NextResponse.redirect(
        new URL(`/user/${data.session.user.id}`, siteUrl)
      )
    }
  }

  // Fallback: redirect to home page
  return NextResponse.redirect(siteUrl)
}
