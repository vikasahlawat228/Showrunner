import asyncio
import logging
import time
import json
import ulid
from typing import Dict, List, Optional, Any, Callable, Coroutine
from antigravity_tool.schemas.job import Job, JobCreate, JobStatus

logger = logging.getLogger(__name__)

class JobService:
    """Manages long-running asynchronous background jobs."""
    _jobs: Dict[str, Job] = {}
    _events: Dict[str, asyncio.Event] = {}
    _global_update_event = asyncio.Event()

    @classmethod
    def create_job(cls, job_type: str, payload: dict) -> Job:
        job_id = str(ulid.ULID())
        now = time.time()
        job = Job(
            id=job_id,
            job_type=job_type,
            status=JobStatus.PENDING,
            message="Initializing...",
            created_at=now,
            updated_at=now,
        )
        cls._jobs[job_id] = job
        cls._events[job_id] = asyncio.Event()
        cls._trigger_global_update()
        return job

    @classmethod
    def update_job(cls, job_id: str, status: Optional[JobStatus] = None, progress: Optional[int] = None, message: Optional[str] = None, result: Optional[dict] = None, error: Optional[str] = None):
        job = cls._jobs.get(job_id)
        if not job:
            return

        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = progress
        if message is not None:
            job.message = message
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error
        
        job.updated_at = time.time()
        
        ev = cls._events.get(job_id)
        if ev:
            ev.set()
            ev.clear()
        
        cls._trigger_global_update()

    @classmethod
    def get_job(cls, job_id: str) -> Optional[Job]:
        return cls._jobs.get(job_id)

    @classmethod
    def list_active_jobs(cls) -> List[Job]:
        return [j for j in cls._jobs.values() if j.status in (JobStatus.PENDING, JobStatus.RUNNING)]

    @classmethod
    def list_all_jobs(cls) -> List[Job]:
        return list(cls._jobs.values())

    @classmethod
    def run_in_background(cls, job_id: str, coro: Coroutine):
        """Wraps a coroutine to run in the background and update job status automatically."""
        async def wrapper():
            cls.update_job(job_id, status=JobStatus.RUNNING, message="Running...")
            try:
                result = await coro
                cls.update_job(job_id, status=JobStatus.COMPLETED, progress=100, message="Completed successfully", result=result)
            except Exception as e:
                logger.error(f"Background job {job_id} failed: {e}", exc_info=True)
                cls.update_job(job_id, status=JobStatus.FAILED, message="Failed", error=str(e))
        
        asyncio.create_task(wrapper())

    @classmethod
    def _trigger_global_update(cls):
        cls._global_update_event.set()
        cls._global_update_event.clear()

    @classmethod
    async def stream_jobs(cls):
        """SSE stream for global background job updates."""
        try:
            # Yield initial state
            jobs = [j.model_dump() for j in cls.list_active_jobs()]
            yield {"event": "jobs_update", "data": json.dumps(jobs)}

            while True:
                await cls._global_update_event.wait()
                jobs = [j.model_dump() for j in cls.list_active_jobs()]
                yield {"event": "jobs_update", "data": json.dumps(jobs)}
        except asyncio.CancelledError:
            pass
