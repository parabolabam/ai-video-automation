from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn
import logging
import os
from contextlib import asynccontextmanager

from features.platform.runner import DynamicWorkflowRunner
from features.platform.auth import get_current_user, get_optional_user, verify_user_access, supabase
from features.platform.scheduler import get_scheduler

from fastapi.middleware.cors import CORSMiddleware

# Security scheme for Swagger UI
security = HTTPBearer()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the scheduler
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("Application startup complete")
    yield
    # Shutdown: Stop the scheduler
    scheduler.shutdown()
    logger.info("Application shutdown complete")

app = FastAPI(
    title="AI Video Automation Platform API",
    description="""
    AI Video Automation Platform with workflow execution and cron job scheduling.

    ## Authentication
    All endpoints (except `/health`) require a valid JWT token from Supabase.

    **How to get your token:**
    1. Sign in at http://localhost:3000
    2. Open browser DevTools → Console
    3. Run: `(await window.supabase.auth.getSession()).data.session.access_token`
    4. Copy the token
    5. Click "Authorize" button below and paste: `Bearer <your-token>`
    """,
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
    }
)

# Configure CORS - Update to include production domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://vingine.duckdns.org",
        "http://vingine.duckdns.org"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WorkflowExecutionRequest(BaseModel):
    workflow_id: str
    user_id: str
    input: str

class CronJobCreateRequest(BaseModel):
    job_id: str
    workflow_id: str
    user_id: str
    input: str
    cron_expression: str

class IntervalJobCreateRequest(BaseModel):
    job_id: str
    workflow_id: str
    user_id: str
    input: str
    hours: int = 0
    minutes: int = 0
    seconds: int = 0

class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None

from fastapi.responses import StreamingResponse
import json

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/run_stream")
async def run_workflow_stream(
    request: WorkflowExecutionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Stream workflow execution events (NDJSON).
    Requires authentication.
    """
    logger.info(f"Received STREAM execution request: workflow={request.workflow_id}, user={current_user['email']}")

    # Verify user can only access their own workflows
    verify_user_access(request.user_id, current_user)

    async def event_generator():
        try:
            runner = DynamicWorkflowRunner(request.workflow_id, request.user_id)
            async for event in runner.run_stream(request.input):
                yield json.dumps(event) + "\n"
        except Exception as e:
            logger.error(f"Stream Error: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.post("/api/run/stream")
async def run_workflow_stream_sse(
    request: WorkflowExecutionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Stream workflow execution events via SSE (Server-Sent Events).
    This is the endpoint used by the frontend workflow visualizer.
    Requires authentication.
    """
    logger.info(f"Received SSE stream request: workflow={request.workflow_id}, user={current_user['email']}")

    # Verify user can only access their own workflows
    verify_user_access(request.user_id, current_user)

    async def event_generator():
        try:
            runner = DynamicWorkflowRunner(request.workflow_id, request.user_id)
            async for event in runner.run_stream(request.input):
                # SSE format: data: {json}\n\n
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.error(f"SSE Stream Error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/run")
async def run_workflow(
    request: WorkflowExecutionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Execute a workflow (legacy JSON response).
    Requires authentication.
    """
    logger.info(f"Received execution request: workflow={request.workflow_id}, user={current_user['email']}")

    # Verify user can only access their own workflows
    verify_user_access(request.user_id, current_user)

    runner = DynamicWorkflowRunner(request.workflow_id, request.user_id)
    result = await runner.run(request.input)
    return {"status": "success", "data": result}

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    Requires authentication.
    """
    return current_user

# ============================================================================
# CRON JOB MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/cron/jobs")
async def list_cron_jobs(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List all cron jobs for the authenticated user.
    Requires authentication.
    """
    scheduler = get_scheduler()
    user_id = current_user['id']

    jobs = scheduler.get_jobs_for_user(user_id)

    return {
        "status": "success",
        "user_id": user_id,
        "total_jobs": len(jobs),
        "jobs": jobs
    }

@app.get("/api/cron/jobs/all")
async def list_all_cron_jobs(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List ALL cron jobs in the system (admin only).
    Requires authentication.

    Note: Currently returns all jobs. Add admin check if needed.
    """
    scheduler = get_scheduler()
    jobs = scheduler.get_all_jobs()

    return {
        "status": "success",
        "total_jobs": len(jobs),
        "jobs": jobs
    }

@app.get("/api/cron/jobs/{job_id}")
async def get_cron_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get information about a specific cron job.
    Requires authentication and job ownership.
    """
    scheduler = get_scheduler()
    job = scheduler.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Verify user owns this job
    if job.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="You don't have permission to access this job")

    return {
        "status": "success",
        "job": job
    }

@app.post("/api/cron/jobs/cron")
async def create_cron_job(
    request: CronJobCreateRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new cron-based scheduled job.
    Requires authentication.

    Cron expression format: "minute hour day month day_of_week"
    Examples:
      - "0 */6 * * *" = Every 6 hours
      - "0 9 * * *" = Every day at 9 AM
      - "0 9,18 * * *" = Every day at 9 AM and 6 PM
      - "0 9 * * 1-5" = Every weekday at 9 AM
    """
    # Verify user can only create jobs for themselves
    verify_user_access(request.user_id, current_user)

    scheduler = get_scheduler()

    try:
        job = scheduler.add_cron_job(
            job_id=request.job_id,
            workflow_id=request.workflow_id,
            user_id=request.user_id,
            input_text=request.input,
            cron_expression=request.cron_expression,
            replace_existing=True
        )

        return {
            "status": "success",
            "message": f"Cron job {request.job_id} created successfully",
            "job": scheduler._job_to_dict(job)
        }
    except Exception as e:
        logger.error(f"Failed to create cron job: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/cron/jobs/interval")
async def create_interval_job(
    request: IntervalJobCreateRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new interval-based scheduled job.
    Requires authentication.

    Examples:
      - hours=6 = Every 6 hours
      - hours=1, minutes=30 = Every 1.5 hours
      - minutes=15 = Every 15 minutes
    """
    # Verify user can only create jobs for themselves
    verify_user_access(request.user_id, current_user)

    scheduler = get_scheduler()

    try:
        job = scheduler.add_interval_job(
            job_id=request.job_id,
            workflow_id=request.workflow_id,
            user_id=request.user_id,
            input_text=request.input,
            hours=request.hours,
            minutes=request.minutes,
            seconds=request.seconds,
            replace_existing=True
        )

        return {
            "status": "success",
            "message": f"Interval job {request.job_id} created successfully",
            "job": scheduler._job_to_dict(job)
        }
    except Exception as e:
        logger.error(f"Failed to create interval job: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/cron/jobs/{job_id}/trigger")
async def trigger_cron_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Manually trigger a cron job to run immediately.
    This does not affect the job's regular schedule.
    Requires authentication and job ownership.
    """
    scheduler = get_scheduler()

    # Verify job exists and user owns it
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="You don't have permission to trigger this job")

    success = scheduler.trigger_job(job_id)

    if success:
        return {
            "status": "success",
            "message": f"Job {job_id} triggered successfully",
            "job_id": job_id
        }
    else:
        raise HTTPException(status_code=500, detail=f"Failed to trigger job {job_id}")

@app.post("/api/cron/jobs/{job_id}/pause")
async def pause_cron_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Pause a cron job (stops it from running but keeps it in the scheduler).
    Requires authentication and job ownership.
    """
    scheduler = get_scheduler()

    # Verify job exists and user owns it
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="You don't have permission to pause this job")

    success = scheduler.pause_job(job_id)

    if success:
        return {
            "status": "success",
            "message": f"Job {job_id} paused successfully",
            "job_id": job_id
        }
    else:
        raise HTTPException(status_code=500, detail=f"Failed to pause job {job_id}")

@app.post("/api/cron/jobs/{job_id}/resume")
async def resume_cron_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Resume a paused cron job.
    Requires authentication and job ownership.
    """
    scheduler = get_scheduler()

    # Verify job exists and user owns it
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="You don't have permission to resume this job")

    success = scheduler.resume_job(job_id)

    if success:
        return {
            "status": "success",
            "message": f"Job {job_id} resumed successfully",
            "job_id": job_id
        }
    else:
        raise HTTPException(status_code=500, detail=f"Failed to resume job {job_id}")

@app.delete("/api/cron/jobs/{job_id}")
async def delete_cron_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete a cron job (removes it completely from the scheduler).
    Requires authentication and job ownership.
    """
    scheduler = get_scheduler()

    # Verify job exists and user owns it
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this job")

    success = scheduler.remove_job(job_id)

    if success:
        return {
            "status": "success",
            "message": f"Job {job_id} deleted successfully",
            "job_id": job_id
        }
    else:
        raise HTTPException(status_code=500, detail=f"Failed to delete job {job_id}")

# ==================== WORKFLOW MANAGEMENT ENDPOINTS ====================

@app.post("/api/workflows")
async def create_workflow(
    request: WorkflowCreateRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new workflow for the authenticated user.
    """
    from uuid import uuid4

    if not supabase:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        # Ensure user profile exists (for existing users who don't have profiles yet)
        profile_check = supabase.table("profiles").select("id").eq("id", current_user["id"]).execute()

        if not profile_check.data:
            # Create profile for this user
            profile_data = {
                "id": current_user["id"],
                "full_name": current_user.get("user_metadata", {}).get("full_name"),
                "avatar_url": current_user.get("user_metadata", {}).get("avatar_url")
            }
            supabase.table("profiles").insert(profile_data).execute()
            logger.info(f"Created profile for user {current_user['id']}")

        # Match the actual database schema from platform_migration.sql
        # workflows table has: id, user_id, name, description, is_active, created_at, updated_at
        workflow_data = {
            "user_id": current_user["id"],
            "name": request.name,
            "description": request.description
            # id, is_active, created_at, updated_at are handled by database defaults
        }

        result = supabase.table("workflows").insert(workflow_data).execute()

        return {
            "status": "success",
            "message": "Workflow created successfully",
            "workflow": result.data[0] if result.data else workflow_data
        }
    except Exception as e:
        logger.error(f"Error creating workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")

@app.get("/api/workflows")
async def list_workflows(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List all workflows for the authenticated user.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        result = supabase.table("workflows").select("*").eq("user_id", current_user["id"]).execute()

        return {
            "status": "success",
            "workflows": result.data or []
        }
    except Exception as e:
        logger.error(f"Error listing workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")

@app.get("/api/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a specific workflow by ID.
    Requires authentication and workflow ownership.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        result = supabase.table("workflows").select("*").eq("id", workflow_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

        workflow = result.data[0]

        # Verify ownership
        if workflow["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="You don't have permission to access this workflow")

        return {
            "status": "success",
            "workflow": workflow
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow: {str(e)}")

@app.put("/api/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    request: WorkflowCreateRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update an existing workflow.
    Requires authentication and workflow ownership.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        # Verify workflow exists and user owns it
        existing = supabase.table("workflows").select("*").eq("id", workflow_id).execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

        if existing.data[0]["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="You don't have permission to update this workflow")

        # Update workflow
        update_data = {
            "name": request.name,
            "description": request.description,
        }

        if request.definition is not None:
            update_data["definition"] = request.definition

        result = supabase.table("workflows").update(update_data).eq("id", workflow_id).execute()

        return {
            "status": "success",
            "message": "Workflow updated successfully",
            "workflow": result.data[0] if result.data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update workflow: {str(e)}")

@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete a workflow.
    Requires authentication and workflow ownership.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        # Verify workflow exists and user owns it
        existing = supabase.table("workflows").select("*").eq("id", workflow_id).execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

        if existing.data[0]["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="You don't have permission to delete this workflow")

        # Delete workflow
        supabase.table("workflows").delete().eq("id", workflow_id).execute()

        return {
            "status": "success",
            "message": f"Workflow {workflow_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {str(e)}")

# ============================================================================
# AGENT ENDPOINTS
# ============================================================================

class AgentCreateRequest(BaseModel):
    id: Optional[str] = None
    workflow_id: str
    name: str
    role: str
    model: str = "gpt-4o"
    system_instructions: str
    tools: Optional[List[str]] = []

@app.post("/api/agents")
async def create_or_update_agent(
    request: AgentCreateRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create or update an agent in a workflow."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        # Verify user owns the workflow
        workflow = supabase.table("workflows").select("user_id").eq("id", request.workflow_id).execute()
        if not workflow.data or workflow.data[0]["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        agent_data = {
            "workflow_id": request.workflow_id,
            "name": request.name,
            "role": request.role,
            "model": request.model,
            "system_instructions": request.system_instructions,
            "tools": request.tools or []
        }

        if request.id:
            # Update existing agent
            agent_data["id"] = request.id
            result = supabase.table("agents").upsert(agent_data).execute()
        else:
            # Create new agent
            result = supabase.table("agents").insert(agent_data).execute()

        return {
            "status": "success",
            "agent": result.data[0] if result.data else agent_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating/updating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save agent: {str(e)}")

@app.delete("/api/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Delete an agent."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        # Verify ownership through workflow
        agent = supabase.table("agents").select("workflow_id").eq("id", agent_id).execute()
        if not agent.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        workflow = supabase.table("workflows").select("user_id").eq("id", agent.data[0]["workflow_id"]).execute()
        if not workflow.data or workflow.data[0]["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        supabase.table("agents").delete().eq("id", agent_id).execute()
        return {"status": "success", "message": "Agent deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")

# ============================================================================
# CONNECTION ENDPOINTS
# ============================================================================

class ConnectionCreateRequest(BaseModel):
    workflow_id: str
    from_agent_id: Optional[str] = None
    to_agent_id: str
    description: Optional[str] = ""

@app.post("/api/connections")
async def create_connection(
    request: ConnectionCreateRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a connection between agents."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        # Verify user owns the workflow
        workflow = supabase.table("workflows").select("user_id").eq("id", request.workflow_id).execute()
        if not workflow.data or workflow.data[0]["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        connection_data = {
            "workflow_id": request.workflow_id,
            "from_agent_id": request.from_agent_id,
            "to_agent_id": request.to_agent_id,
            "description": request.description
        }

        result = supabase.table("workflow_connections").insert(connection_data).execute()

        return {
            "status": "success",
            "connection": result.data[0] if result.data else connection_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create connection: {str(e)}")

@app.delete("/api/connections/{connection_id}")
async def delete_connection(
    connection_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Delete a connection."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        # Verify ownership through workflow
        conn = supabase.table("workflow_connections").select("workflow_id").eq("id", connection_id).execute()
        if not conn.data:
            raise HTTPException(status_code=404, detail="Connection not found")

        workflow = supabase.table("workflows").select("user_id").eq("id", conn.data[0]["workflow_id"]).execute()
        if not workflow.data or workflow.data[0]["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        supabase.table("workflow_connections").delete().eq("id", connection_id).execute()
        return {"status": "success", "message": "Connection deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete connection: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
