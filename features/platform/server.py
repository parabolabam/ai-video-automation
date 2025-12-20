from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
import logging
import os

from features.platform.runner import DynamicWorkflowRunner

from fastapi.middleware.cors import CORSMiddleware

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Video Automation Platform API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WorkflowExecutionRequest(BaseModel):
    workflow_id: str
    user_id: str
    input: str

from fastapi.responses import StreamingResponse
import json

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/run")
async def run_workflow(request: WorkflowExecutionRequest):
    """
    Execute a workflow (legacy JSON response).
    """
    # ... legacy code or redirect ...
    # For now keeping as is for backward compatibility if needed, 
    # but strictly speaking the UI uses this.
    # Let's switch it to streaming effectively if possible, or use a new endpoint.
    # Given the user request for visualization, let's make /api/run a stream 
    # but we need to change how frontend consumes it. 
    # Or create /api/run_stream
    pass 

@app.post("/api/run_stream")
async def run_workflow_stream(request: WorkflowExecutionRequest):
    """
    Stream workflow execution events (NDJSON).
    """
    logger.info(f"Received STREAM execution request: workflow={request.workflow_id}")

    async def event_generator():
        try:
            runner = DynamicWorkflowRunner(request.workflow_id, request.user_id)
            async for event in runner.run_stream(request.input):
                yield json.dumps(event) + "\n"
        except Exception as e:
            logger.error(f"Stream Error: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.post("/api/run")
async def run_workflow(request: WorkflowExecutionRequest):
     # Keep legacy for simple checks
    runner = DynamicWorkflowRunner(request.workflow_id, request.user_id)
    result = await runner.run(request.input)
    return {"status": "success", "data": result}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
