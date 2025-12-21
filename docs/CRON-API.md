# Cron Job Management API

Complete API documentation for managing scheduled workflow executions using the async scheduler.

---

## Overview

The Cron Job API allows you to:
- Schedule workflows to run automatically at specified times
- List all scheduled jobs
- Trigger jobs manually
- Pause/resume jobs
- Delete jobs

All endpoints require authentication via JWT token.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
│                                                          │
│  Server Actions                                         │
│  └─ scheduleCronJob({ workflow_id, schedule })         │
│  └─ listCronJobs()                                      │
│  └─ triggerCronJob(job_id)                             │
└─────────────────────────────────────────────────────────┘
                         │
                         │ HTTPS + JWT Token
                         ▼
┌─────────────────────────────────────────────────────────┐
│                 Backend FastAPI Server                   │
│                                                          │
│  POST /api/cron/jobs/cron                               │
│  POST /api/cron/jobs/interval                           │
│  GET  /api/cron/jobs                                    │
│  GET  /api/cron/jobs/{job_id}                           │
│  POST /api/cron/jobs/{job_id}/trigger                   │
│  POST /api/cron/jobs/{job_id}/pause                     │
│  POST /api/cron/jobs/{job_id}/resume                    │
│  DELETE /api/cron/jobs/{job_id}                         │
│         │                                                │
│         ▼                                                │
│  SchedulerService (APScheduler)                         │
│  └─ AsyncIOScheduler with CronTrigger                   │
└─────────────────────────────────────────────────────────┘
                         │
                         │ On Schedule
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Workflow Execution                      │
│                                                          │
│  DynamicWorkflowRunner.run(input)                       │
│  └─ Executes workflow automatically                     │
└─────────────────────────────────────────────────────────┘
```

---

## Scheduler Service

The backend uses APScheduler with AsyncIOScheduler for non-blocking job execution.

### Features:
- Cron-based scheduling (e.g., "every 6 hours", "daily at 9 AM")
- Interval-based scheduling (e.g., "every 30 minutes")
- Job persistence across restarts (future enhancement)
- Per-user job isolation
- Automatic cleanup on shutdown

### Startup/Shutdown:
The scheduler starts automatically when the FastAPI server starts and shuts down gracefully on server stop.

---

## API Endpoints

### Authentication

All endpoints require a valid JWT token in the Authorization header:

```bash
Authorization: Bearer <jwt_token>
```

Get your token from the Supabase session after logging in.

---

## 1. Create Cron Job

Create a new cron-based scheduled job.

**Endpoint:** `POST /api/cron/jobs/cron`

**Request Body:**
```json
{
  "job_id": "daily-video-generation",
  "workflow_id": "video-automation-workflow",
  "user_id": "user-uuid",
  "input": "Generate video about tech news",
  "cron_expression": "0 9 * * *"
}
```

**Cron Expression Format:**
```
minute hour day month day_of_week

Examples:
  "0 */6 * * *"     = Every 6 hours
  "0 9 * * *"       = Every day at 9 AM
  "0 9,18 * * *"    = Every day at 9 AM and 6 PM
  "0 9 * * 1-5"     = Every weekday at 9 AM
  "*/15 * * * *"    = Every 15 minutes
  "0 0 1 * *"       = First day of every month at midnight
```

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Cron job daily-video-generation created successfully",
  "job": {
    "job_id": "daily-video-generation",
    "name": "Workflow video-automation-workflow for user user-uuid",
    "workflow_id": "video-automation-workflow",
    "user_id": "user-uuid",
    "input_text": "Generate video about tech news",
    "schedule_type": "cron",
    "schedule": "0 9 * * *",
    "next_run_time": "2025-12-22T09:00:00",
    "paused": false,
    "trigger": "cron[day='*', hour='9', minute='0']"
  }
}
```

**Error Response (400):**
```json
{
  "detail": "Invalid cron expression: 0 9. Expected 5 parts (minute hour day month day_of_week)"
}
```

**Error Response (403):**
```json
{
  "detail": "Unauthorized: You can only run your own workflows."
}
```

**cURL Example:**
```bash
curl -X POST https://vingine.duckdns.org/api/cron/jobs/cron \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "daily-video-generation",
    "workflow_id": "video-automation-workflow",
    "user_id": "user-uuid",
    "input": "Generate video about tech news",
    "cron_expression": "0 9 * * *"
  }'
```

---

## 2. Create Interval Job

Create a new interval-based scheduled job.

**Endpoint:** `POST /api/cron/jobs/interval`

**Request Body:**
```json
{
  "job_id": "hourly-video-check",
  "workflow_id": "video-automation-workflow",
  "user_id": "user-uuid",
  "input": "Check for trending topics",
  "hours": 1,
  "minutes": 30,
  "seconds": 0
}
```

**Parameters:**
- `hours`: Run every N hours (default: 0)
- `minutes`: Run every N minutes (default: 0)
- `seconds`: Run every N seconds (default: 0)

At least one must be greater than 0.

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Interval job hourly-video-check created successfully",
  "job": {
    "job_id": "hourly-video-check",
    "name": "Workflow video-automation-workflow for user user-uuid",
    "workflow_id": "video-automation-workflow",
    "user_id": "user-uuid",
    "input_text": "Check for trending topics",
    "schedule_type": "interval",
    "schedule": "1h 30m",
    "next_run_time": "2025-12-21T15:30:00",
    "paused": false,
    "trigger": "interval[1:30:00]"
  }
}
```

**cURL Example:**
```bash
curl -X POST https://vingine.duckdns.org/api/cron/jobs/interval \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "hourly-video-check",
    "workflow_id": "video-automation-workflow",
    "user_id": "user-uuid",
    "input": "Check for trending topics",
    "hours": 1,
    "minutes": 30
  }'
```

---

## 3. List User's Cron Jobs

Get all cron jobs for the authenticated user.

**Endpoint:** `GET /api/cron/jobs`

**Success Response (200):**
```json
{
  "status": "success",
  "user_id": "user-uuid",
  "total_jobs": 2,
  "jobs": [
    {
      "job_id": "daily-video-generation",
      "name": "Workflow video-automation-workflow for user user-uuid",
      "workflow_id": "video-automation-workflow",
      "user_id": "user-uuid",
      "input_text": "Generate video about tech news",
      "schedule_type": "cron",
      "schedule": "0 9 * * *",
      "next_run_time": "2025-12-22T09:00:00",
      "paused": false,
      "trigger": "cron[day='*', hour='9', minute='0']"
    },
    {
      "job_id": "hourly-video-check",
      "name": "Workflow video-automation-workflow for user user-uuid",
      "workflow_id": "video-automation-workflow",
      "user_id": "user-uuid",
      "input_text": "Check for trending topics",
      "schedule_type": "interval",
      "schedule": "1h 30m",
      "next_run_time": "2025-12-21T15:30:00",
      "paused": false,
      "trigger": "interval[1:30:00]"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X GET https://vingine.duckdns.org/api/cron/jobs \
  -H "Authorization: Bearer <token>"
```

---

## 4. List All Cron Jobs

Get all cron jobs in the system (admin endpoint).

**Endpoint:** `GET /api/cron/jobs/all`

**Success Response (200):**
```json
{
  "status": "success",
  "total_jobs": 5,
  "jobs": [...]
}
```

**Note:** Currently returns all jobs. Add admin role check if needed.

**cURL Example:**
```bash
curl -X GET https://vingine.duckdns.org/api/cron/jobs/all \
  -H "Authorization: Bearer <token>"
```

---

## 5. Get Specific Cron Job

Get information about a specific cron job.

**Endpoint:** `GET /api/cron/jobs/{job_id}`

**Success Response (200):**
```json
{
  "status": "success",
  "job": {
    "job_id": "daily-video-generation",
    "name": "Workflow video-automation-workflow for user user-uuid",
    "workflow_id": "video-automation-workflow",
    "user_id": "user-uuid",
    "input_text": "Generate video about tech news",
    "schedule_type": "cron",
    "schedule": "0 9 * * *",
    "next_run_time": "2025-12-22T09:00:00",
    "paused": false,
    "trigger": "cron[day='*', hour='9', minute='0']"
  }
}
```

**Error Response (404):**
```json
{
  "detail": "Job daily-video-generation not found"
}
```

**Error Response (403):**
```json
{
  "detail": "You don't have permission to access this job"
}
```

**cURL Example:**
```bash
curl -X GET https://vingine.duckdns.org/api/cron/jobs/daily-video-generation \
  -H "Authorization: Bearer <token>"
```

---

## 6. Trigger Cron Job Manually

Manually trigger a cron job to run immediately. This does not affect the regular schedule.

**Endpoint:** `POST /api/cron/jobs/{job_id}/trigger`

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Job daily-video-generation triggered successfully",
  "job_id": "daily-video-generation"
}
```

**Error Response (404):**
```json
{
  "detail": "Job daily-video-generation not found"
}
```

**Error Response (403):**
```json
{
  "detail": "You don't have permission to trigger this job"
}
```

**cURL Example:**
```bash
curl -X POST https://vingine.duckdns.org/api/cron/jobs/daily-video-generation/trigger \
  -H "Authorization: Bearer <token>"
```

---

## 7. Pause Cron Job

Pause a cron job (stops it from running but keeps it in the scheduler).

**Endpoint:** `POST /api/cron/jobs/{job_id}/pause`

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Job daily-video-generation paused successfully",
  "job_id": "daily-video-generation"
}
```

**cURL Example:**
```bash
curl -X POST https://vingine.duckdns.org/api/cron/jobs/daily-video-generation/pause \
  -H "Authorization: Bearer <token>"
```

---

## 8. Resume Cron Job

Resume a paused cron job.

**Endpoint:** `POST /api/cron/jobs/{job_id}/resume`

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Job daily-video-generation resumed successfully",
  "job_id": "daily-video-generation"
}
```

**cURL Example:**
```bash
curl -X POST https://vingine.duckdns.org/api/cron/jobs/daily-video-generation/resume \
  -H "Authorization: Bearer <token>"
```

---

## 9. Delete Cron Job

Delete a cron job (removes it completely from the scheduler).

**Endpoint:** `DELETE /api/cron/jobs/{job_id}`

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Job daily-video-generation deleted successfully",
  "job_id": "daily-video-generation"
}
```

**Error Response (404):**
```json
{
  "detail": "Job daily-video-generation not found"
}
```

**Error Response (403):**
```json
{
  "detail": "You don't have permission to delete this job"
}
```

**cURL Example:**
```bash
curl -X DELETE https://vingine.duckdns.org/api/cron/jobs/daily-video-generation \
  -H "Authorization: Bearer <token>"
```

---

## Next.js Server Actions Integration

Create Server Actions to securely call the cron job API:

### `app/actions/cron.ts`

```typescript
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
      return { success: false, error: 'Failed to list cron jobs' }
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
```

---

## Usage Examples

### Example 1: Daily Video Generation

```typescript
'use client'

import { createCronJob } from '@/app/actions/cron'
import { useTransition } from 'react'

export function ScheduleButton({ workflowId, userId }) {
  const [isPending, startTransition] = useTransition()

  const handleSchedule = () => {
    startTransition(async () => {
      const result = await createCronJob({
        job_id: 'daily-video',
        workflow_id: workflowId,
        user_id: userId,
        input: 'Generate daily tech news video',
        cron_expression: '0 9 * * *', // 9 AM daily
      })

      if (result.success) {
        alert('Job scheduled successfully!')
      } else {
        alert(`Error: ${result.error}`)
      }
    })
  }

  return (
    <button onClick={handleSchedule} disabled={isPending}>
      {isPending ? 'Scheduling...' : 'Schedule Daily at 9 AM'}
    </button>
  )
}
```

### Example 2: List Scheduled Jobs

```typescript
'use client'

import { listCronJobs } from '@/app/actions/cron'
import { useEffect, useState } from 'react'

export function CronJobsList() {
  const [jobs, setJobs] = useState([])

  useEffect(() => {
    const fetchJobs = async () => {
      const result = await listCronJobs()
      if (result.success) {
        setJobs(result.data.jobs)
      }
    }
    fetchJobs()
  }, [])

  return (
    <div>
      <h2>Scheduled Jobs</h2>
      {jobs.map(job => (
        <div key={job.job_id}>
          <p>Job: {job.job_id}</p>
          <p>Schedule: {job.schedule}</p>
          <p>Next Run: {job.next_run_time}</p>
        </div>
      ))}
    </div>
  )
}
```

---

## Security

1. All endpoints require JWT authentication
2. Users can only create/manage their own jobs
3. Job ownership verified on every operation
4. Tokens never exposed to client (via Server Actions)
5. Input validation on all endpoints

---

## Best Practices

1. **Use unique job IDs**: Include user ID and timestamp in job IDs
   ```javascript
   const job_id = `${userId}-daily-video-${Date.now()}`
   ```

2. **Handle job replacement**: By default, creating a job with an existing ID replaces the old job
   ```javascript
   // This replaces the previous "daily-video" job
   await createCronJob({ job_id: 'daily-video', ... })
   ```

3. **Monitor job execution**: Check backend logs for job execution results
   ```bash
   docker logs ai-video-backend --tail 50 -f
   ```

4. **Use appropriate schedules**: Don't schedule too frequently
   ```javascript
   // ❌ BAD: Every second
   cron_expression: '* * * * * *'

   // ✅ GOOD: Every 6 hours
   cron_expression: '0 */6 * * *'
   ```

5. **Clean up old jobs**: Delete jobs that are no longer needed
   ```javascript
   await deleteCronJob('old-job-id')
   ```

---

## Troubleshooting

### Job not executing

1. Check if scheduler is running:
   ```bash
   curl https://vingine.duckdns.org/health
   ```

2. Check backend logs:
   ```bash
   docker logs ai-video-backend --tail 50
   ```

3. Verify job exists:
   ```bash
   curl -H "Authorization: Bearer <token>" \
     https://vingine.duckdns.org/api/cron/jobs/your-job-id
   ```

### Job paused

If `next_run_time` is `null`, the job is paused:
```bash
curl -X POST -H "Authorization: Bearer <token>" \
  https://vingine.duckdns.org/api/cron/jobs/your-job-id/resume
```

### Invalid cron expression

Use the cron format: `minute hour day month day_of_week`

Test your cron expression at https://crontab.guru/

---

## Summary

The Cron Job API provides complete control over scheduled workflow execution:

- ✅ Cron-based and interval-based scheduling
- ✅ Full CRUD operations (Create, Read, Update via replace, Delete)
- ✅ Manual triggering
- ✅ Pause/resume functionality
- ✅ Per-user job isolation
- ✅ JWT authentication
- ✅ Next.js Server Actions integration

All jobs run automatically in the background, with full logging and error handling.
