"""FastAPI router for the State Machine Pipeline."""

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from antigravity_tool.schemas.pipeline import PipelineRunCreate, PipelineResume
from antigravity_tool.services.pipeline_service import PipelineService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

@router.post("/run", status_code=201)
async def start_pipeline_run(request: PipelineRunCreate):
    """Initialize a new pipeline run sequence and execute in background."""
    run_id = await PipelineService.start_pipeline(request.initial_payload)
    return {"run_id": run_id}

@router.get("/{run_id}/stream")
async def stream_pipeline_run(run_id: str):
    """Stream Server-Sent Events (SSE) representing pipeline state changes."""
    return EventSourceResponse(PipelineService.stream_pipeline(run_id))

@router.post("/{run_id}/resume")
async def resume_pipeline_run(run_id: str, request: PipelineResume):
    """Resume a paused pipeline run with user edits/updates."""
    try:
        await PipelineService.resume_pipeline(run_id, request.payload)
        return {"status": "resumed", "run_id": run_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
