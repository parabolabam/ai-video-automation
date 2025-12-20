'use server'

import { createClient } from '@/lib/supabase-server'
import { revalidatePath } from 'next/cache'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface RunWorkflowParams {
  workflowId: string
  userId: string
  input: string
}

interface WorkflowResult {
  success: boolean
  data?: any
  error?: string
}

/**
 * Server Action to run a workflow
 * Handles authentication server-side to keep tokens secure
 */
export async function runWorkflow(params: RunWorkflowParams): Promise<WorkflowResult> {
  try {
    // Get server-side Supabase client with user session
    const supabase = await createClient()

    // Get the current user's session
    const { data: { session }, error: sessionError } = await supabase.auth.getSession()

    if (sessionError || !session) {
      return {
        success: false,
        error: 'Not authenticated. Please sign in.',
      }
    }

    // Verify the user is accessing their own workflow
    if (session.user.id !== params.userId) {
      return {
        success: false,
        error: 'Unauthorized: You can only run your own workflows.',
      }
    }

    // Call backend API with access token (server-side only)
    const response = await fetch(`${API_URL}/api/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        workflow_id: params.workflowId,
        user_id: params.userId,
        input: params.input,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return {
        success: false,
        error: errorData.detail || `HTTP error ${response.status}`,
      }
    }

    const data = await response.json()

    // Revalidate the workflows list
    revalidatePath(`/user/${params.userId}`)

    return {
      success: true,
      data,
    }
  } catch (error) {
    console.error('Server Action Error:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to run workflow',
    }
  }
}

/**
 * Server Action to stream workflow execution
 * Returns stream URL with authorization token
 */
export async function getStreamUrl(params: RunWorkflowParams): Promise<{
  success: boolean
  streamUrl?: string
  accessToken?: string
  error?: string
}> {
  try {
    // Get server-side Supabase client with user session
    const supabase = await createClient()

    // Get the current user's session
    const { data: { session }, error: sessionError } = await supabase.auth.getSession()

    if (sessionError || !session) {
      return {
        success: false,
        error: 'Not authenticated. Please sign in.',
      }
    }

    // Verify the user is accessing their own workflow
    if (session.user.id !== params.userId) {
      return {
        success: false,
        error: 'Unauthorized: You can only run your own workflows.',
      }
    }

    // Return stream URL and access token for client-side streaming
    // Token is only exposed to the authenticated user's browser
    return {
      success: true,
      streamUrl: `${API_URL}/api/run_stream`,
      accessToken: session.access_token,
    }

  } catch (error) {
    console.error('Server Action Stream Error:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get stream URL',
    }
  }
}

/**
 * Server Action to get current user info
 */
export async function getCurrentUser() {
  try {
    const supabase = await createClient()
    const { data: { session }, error } = await supabase.auth.getSession()

    if (error || !session) {
      return null
    }

    return {
      id: session.user.id,
      email: session.user.email,
      user_metadata: session.user.user_metadata,
    }
  } catch (error) {
    console.error('Get current user error:', error)
    return null
  }
}
