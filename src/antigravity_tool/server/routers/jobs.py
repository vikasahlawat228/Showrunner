from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sse_starlette.sse import EventSourceResponse

from antigravity_tool.schemas.job import Job, JobCreate
from antigravity_tool.services.job_service import JobService
from antigravity_tool.server.deps import get_pipeline_service
from antigravity_tool.services.pipeline_service import PipelineService

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/", status_code=201)
async def create_job(
    request: JobCreate,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    job = JobService.create_job(job_type=request.job_type, payload=request.payload)

    if request.job_type == "pipeline":
        definition_id = request.payload.get("definition_id")
        initial_payload = request.payload.get("initial_payload", {})
        
        # Start pipeline but wrap its execution context if needed
        # We need the pipeline_service to run, but pipeline_service.start_pipeline also runs asyncio.create_task itself
        # For now, let's just trigger it and wrap the wait task.
        
        async def run_pipeline_task():
            # Trigger pipeline start
            run_id = await pipeline_service.start_pipeline(initial_payload, definition_id=definition_id)
            JobService.update_job(job.id, message=f"Pipeline {definition_id or 'legacy'} started...", result={"run_id": run_id})
            
            # Here we might want to poll or wait for the pipeline to finish 
            # so the job properly completes only when the pipeline does.
            # but since pipeline streaming is separate, we'll mark this job done as soon as it's dispatched for now,
            # or we can tap into pipeline events.
            
            # Realistically, the pipeline IS the background task.
            # Let's attach to the pipeline's event stream or run lifecycle if available.
            # Assuming start_pipeline kicks off the background task, the job represents the wrapper.
            return {"run_id": run_id}

        JobService.run_in_background(job.id, run_pipeline_task())
    else:
        # Unknown job type
        JobService.update_job(job.id, status="failed", error="Unknown job_type")

    return {"job_id": job.id}

@router.get("/stream")
async def stream_jobs():
    """Stream global job updates."""
    return EventSourceResponse(JobService.stream_jobs())

@router.get("/{job_id}")
async def get_job(job_id: str) -> Job:
    job = JobService.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/")
async def list_jobs(active_only: bool = True) -> List[Job]:
    if active_only:
        return JobService.list_active_jobs()
    return JobService.list_all_jobs()
