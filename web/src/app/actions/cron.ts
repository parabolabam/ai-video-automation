'use server'

import { createClient } from '@/lib/supabase-server'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface CronJobParams {
  job_id: string
  workflow_id: string
  user_id: string
  input: string
  cron_expression: string
}

interface IntervalJobParams {
  job_id: string
  workflow_id: string
  user_id: string
  input: string
  hours: number
  minutes: number
  seconds: number
}

export async function listCronJobs() {
  try {
    const supabase = await createClient()
    const { data: { session }, error } = await supabase.auth.getSession()

    if (error || !session) {
      return { success: false, error: 'Not authenticated' }
    }

    const response = await fetch(`${API_URL}/api/cron/jobs`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return { success: false, error: errorData.detail || 'Failed to list cron jobs' }
    }

    const data = await response.json()
    return { success: true, data }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
  }
}

export async function createCronJob(params: CronJobParams) {
  try {
    const supabase = await createClient()
    const { data: { session }, error } = await supabase.auth.getSession()

    if (error || !session) {
      return { success: false, error: 'Not authenticated' }
    }

    if (session.user.id !== params.user_id) {
      return { success: false, error: 'Unauthorized' }
    }

    const response = await fetch(`${API_URL}/api/cron/jobs/cron`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify(params),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return { success: false, error: errorData.detail || 'Failed to create cron job' }
    }

    const data = await response.json()
    return { success: true, data }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
  }
}

export async function createIntervalJob(params: IntervalJobParams) {
  try {
    const supabase = await createClient()
    const { data: { session }, error } = await supabase.auth.getSession()

    if (error || !session) {
      return { success: false, error: 'Not authenticated' }
    }

    if (session.user.id !== params.user_id) {
      return { success: false, error: 'Unauthorized' }
    }

    const response = await fetch(`${API_URL}/api/cron/jobs/interval`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify(params),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return { success: false, error: errorData.detail || 'Failed to create interval job' }
    }

    const data = await response.json()
    return { success: true, data }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
  }
}

export async function triggerCronJob(job_id: string) {
  try {
    const supabase = await createClient()
    const { data: { session }, error } = await supabase.auth.getSession()

    if (error || !session) {
      return { success: false, error: 'Not authenticated' }
    }

    const response = await fetch(`${API_URL}/api/cron/jobs/${job_id}/trigger`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return { success: false, error: errorData.detail || 'Failed to trigger job' }
    }

    const data = await response.json()
    return { success: true, data }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
  }
}

export async function pauseCronJob(job_id: string) {
  try {
    const supabase = await createClient()
    const { data: { session }, error } = await supabase.auth.getSession()

    if (error || !session) {
      return { success: false, error: 'Not authenticated' }
    }

    const response = await fetch(`${API_URL}/api/cron/jobs/${job_id}/pause`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return { success: false, error: errorData.detail || 'Failed to pause job' }
    }

    const data = await response.json()
    return { success: true, data }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
  }
}

export async function resumeCronJob(job_id: string) {
  try {
    const supabase = await createClient()
    const { data: { session }, error } = await supabase.auth.getSession()

    if (error || !session) {
      return { success: false, error: 'Not authenticated' }
    }

    const response = await fetch(`${API_URL}/api/cron/jobs/${job_id}/resume`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return { success: false, error: errorData.detail || 'Failed to resume job' }
    }

    const data = await response.json()
    return { success: true, data }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
  }
}

export async function deleteCronJob(job_id: string) {
  try {
    const supabase = await createClient()
    const { data: { session }, error } = await supabase.auth.getSession()

    if (error || !session) {
      return { success: false, error: 'Not authenticated' }
    }

    const response = await fetch(`${API_URL}/api/cron/jobs/${job_id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return { success: false, error: errorData.detail || 'Failed to delete job' }
    }

    const data = await response.json()
    return { success: true, data }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
  }
}
