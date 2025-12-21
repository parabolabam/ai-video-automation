# Main Pipeline Cron Job

## Overview

The `main_v2.py` pipeline is automatically registered as a cron job when the backend starts. This is the **primary constraint** for the video automation system - it ensures the main pipeline runs every 5 hours without manual intervention.

## How It Works

### Auto-Registration on Backend Startup

When the FastAPI backend starts (in `features/platform/server.py`), it:
1. Initializes the APScheduler service
2. Calls `scheduler.start()`
3. Auto-registers the main pipeline job via `register_main_pipeline_job()`

### Job Configuration

- **Job ID**: `main_pipeline_v2`
- **Schedule**: Every 5 hours (interval-based)
- **Runs**: `main_v2.py` script
- **User**: `system` (not tied to a specific user)
- **Workflow ID**: `main_pipeline` (special identifier)

### Implementation Details

**Location**: `features/platform/scheduler.py`

**Key Methods**:

```python
async def _run_main_pipeline(self, **kwargs):
    """Execute the main_v2.py pipeline as a scheduled job"""
    # Runs main_v2.py using subprocess
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "main_v2.py",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
```

```python
def register_main_pipeline_job(self):
    """Register main_v2.py to run every 5 hours"""
    job_id = "main_pipeline_v2"
    trigger = IntervalTrigger(hours=5)

    job = self.scheduler.add_job(
        self._run_main_pipeline,
        trigger=trigger,
        id=job_id,
        name="Main Video Pipeline (main_v2.py)",
        ...
    )
```

## Verification

### Check Backend Logs

After backend startup, you should see:

```
INFO:apscheduler.scheduler:Added job "Main Video Pipeline (main_v2.py)" to job store "default"
INFO:features.platform.scheduler:✅ Main pipeline job registered successfully: main_pipeline_v2 (runs every 5 hours)
```

### Check via Cron Jobs Dashboard

1. Navigate to: `http://localhost:3000/user/{userId}/cron-jobs`
2. You should see a job with:
   - **Job ID**: `main_pipeline_v2`
   - **Name**: Main Video Pipeline (main_v2.py)
   - **Schedule**: 5h
   - **User ID**: system
   - **Workflow ID**: main_pipeline

### Manual Trigger (Optional)

You can manually trigger the pipeline to run immediately via the API:

```bash
# Get your access token first (see docs/TOKEN-RETRIEVAL.md)
TOKEN="your_access_token_here"

# Trigger the job
curl -X POST http://localhost:8000/api/cron/jobs/main_pipeline_v2/trigger \
  -H "Authorization: Bearer $TOKEN"
```

## Deployment Behavior

### Docker Container Deployment

- ✅ **Runs on every container restart** - Job is re-registered each time
- ✅ **Survives hot-reloads** - Development mode preserves jobs
- ❌ **Does NOT persist across container removals** - In-memory scheduler

### Production Deployment (Digital Ocean)

When you deploy to production:
1. Backend container starts
2. Scheduler initializes
3. Main pipeline job auto-registers
4. Job runs every 5 hours as long as container is running

**Important**: If the container is stopped/removed, the job schedule is lost. On container restart, it re-registers and starts fresh.

## Modifying the Schedule

To change the 5-hour interval, edit `features/platform/scheduler.py`:

```python
def register_main_pipeline_job(self):
    # Change this line:
    trigger = IntervalTrigger(hours=5)  # Change to hours=X
```

Or use a cron expression instead:

```python
# Run at specific times
trigger = CronTrigger(hour='*/5')  # Every 5 hours on the hour
trigger = CronTrigger(hour='0,6,12,18')  # At midnight, 6am, noon, 6pm
```

## Monitoring Pipeline Execution

### Check Logs

```bash
# Docker local
docker-compose logs -f backend | grep "main_v2"

# Production
ssh user@droplet_ip
docker logs -f ai-video-backend | grep "main_v2"
```

### Expected Log Output

**Job Start**:
```
INFO:features.platform.scheduler:🎬 Running main_v2.py pipeline...
```

**Job Success**:
```
INFO:features.platform.scheduler:✅ main_v2.py pipeline completed successfully
INFO:features.platform.scheduler:Output: [pipeline output]
```

**Job Failure**:
```
ERROR:features.platform.scheduler:❌ main_v2.py pipeline failed with code 1
ERROR:features.platform.scheduler:Error: [error details]
```

## Troubleshooting

### Job Not Registered

**Symptom**: No log message about job registration on startup

**Solutions**:
1. Check scheduler started: `docker-compose logs backend | grep "Scheduler started"`
2. Check for startup errors: `docker-compose logs backend | grep ERROR`
3. Restart backend: `docker-compose restart backend`

### Job Not Running

**Symptom**: Job registered but doesn't execute

**Solutions**:
1. Check next run time: View in cron jobs dashboard
2. Check for execution errors in logs
3. Manually trigger to test: `POST /api/cron/jobs/main_pipeline_v2/trigger`

### Pipeline Execution Fails

**Symptom**: Job runs but main_v2.py fails

**Solutions**:
1. Test manually: `docker-compose exec backend python main_v2.py`
2. Check environment variables are set
3. Check API keys are valid
4. Review stderr in logs for specific errors

## Alternative: System Cron (Not Recommended for Docker)

If you need the job to persist across container restarts without re-registration, you could use system cron on the droplet instead:

```bash
# SSH to droplet
ssh user@droplet_ip

# Add to crontab
crontab -e

# Add this line (runs every 5 hours)
0 */5 * * * docker exec ai-video-backend python main_v2.py >> /var/log/main_pipeline.log 2>&1
```

**However**, the current approach (APScheduler auto-registration) is preferred because:
- ✅ Managed entirely in code
- ✅ Visible in cron jobs dashboard
- ✅ Can be triggered/paused via API
- ✅ Better logging integration
- ✅ Works in development and production

## Related Files

- `features/platform/scheduler.py` - Job registration and execution
- `features/platform/server.py` - Scheduler startup
- `main_v2.py` - The pipeline script itself
- `features/app/run_pipeline_v2.py` - Pipeline implementation
- `docs/CRON-API.md` - Cron API documentation
