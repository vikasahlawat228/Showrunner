"""Project router -- project metadata, status, and live SSE event stream."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from showrunner_tool.core.project import Project
from showrunner_tool.core.workflow import WorkflowState
from showrunner_tool.server.api_schemas import ProjectResponse, HealthResponse
from showrunner_tool.server.deps import get_project

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/project", tags=["project"])

# ---------------------------------------------------------------------------
# SSE broadcaster — fan-out to all connected frontends
# ---------------------------------------------------------------------------

_subscribers: List[asyncio.Queue] = []
_lock = asyncio.Lock()


async def _add_subscriber() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    async with _lock:
        _subscribers.append(q)
    return q


async def _remove_subscriber(q: asyncio.Queue) -> None:
    async with _lock:
        try:
            _subscribers.remove(q)
        except ValueError:
            pass


def broadcast_event(data: Dict[str, Any]) -> None:
    """Push a JSON event to every connected SSE client.

    Safe to call from any thread (e.g. the watchdog thread).
    """
    for q in list(_subscribers):
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            logger.warning("SSE subscriber queue full — dropping event")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=ProjectResponse)
async def get_project_info(project: Project = Depends(get_project)):
    wf = WorkflowState(project.path)
    return ProjectResponse(
        name=project.name,
        path=str(project.path),
        variables=project.variables,
        workflow_step=wf.get_current_step(),
    )


@router.get("/health", response_model=HealthResponse)
async def health_check(project: Project = Depends(get_project)):
    return HealthResponse(status="ok", project=project.name)


@router.get("/events")
async def project_events(request: Request):
    """Server-Sent Events (SSE) stream of live project changes.

    The file watcher pushes ``GRAPH_UPDATED`` events here whenever a
    YAML file is created, modified, or deleted on disk.

    Example event payload::

        {"type": "GRAPH_UPDATED", "event": "modified", "path": "containers/character/hero.yaml"}
    """

    queue = await _add_subscriber()

    async def _event_generator():
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": data.get("type", "message"),
                        "data": json.dumps(data),
                    }
                except asyncio.TimeoutError:
                    # Send keepalive comment to prevent proxy/browser timeout
                    yield {"comment": "keepalive"}
        finally:
            await _remove_subscriber(queue)

    return EventSourceResponse(_event_generator())
