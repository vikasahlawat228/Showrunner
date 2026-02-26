"""Timeline router -- Event Sourcing log manipulation."""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from showrunner_tool.server.deps import get_event_service
from showrunner_tool.repositories.event_sourcing_repo import EventService

router = APIRouter(prefix="/api/v1/timeline", tags=["timeline"])

class CheckoutRequest(BaseModel):
    event_id: str
    branch_name: Optional[str] = None

@router.get("/events")
async def get_all_events(
    svc: EventService = Depends(get_event_service),
) -> List[Dict[str, Any]]:
    """Get all events for rendering the visual timeline."""
    return svc.get_all_events()

@router.post("/checkout")
async def checkout_event(
    req: CheckoutRequest,
    svc: EventService = Depends(get_event_service),
):
    """Checkout a historical event, optionally creating a new branch."""
    if req.branch_name:
        try:
            svc.branch(source_branch_id="", new_branch_name=req.branch_name, checkout_event_id=req.event_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    # This is a stub for the full checkout side-effect capability
    return {"status": "success", "event_id": req.event_id, "branch": req.branch_name}

class BranchCreateRequest(BaseModel):
    branch_name: str
    parent_event_id: str
    source_branch_id: Optional[str] = None

@router.get("/branches")
async def get_branches(
    svc: EventService = Depends(get_event_service),
) -> List[Dict[str, Any]]:
    """List all timeline branches."""
    return svc.get_branches()

@router.post("/branch")
async def create_branch(
    req: BranchCreateRequest,
    svc: EventService = Depends(get_event_service),
):
    """Create a new alternate timeline branch from a historical event."""
    try:
        svc.branch(
            source_branch_id=req.source_branch_id or "",
            new_branch_name=req.branch_name,
            checkout_event_id=req.parent_event_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"status": "created", "branch_name": req.branch_name, "parent_event_id": req.parent_event_id}

@router.get("/branch/{branch_id}/events")
async def get_branch_events(
    branch_id: str,
    svc: EventService = Depends(get_event_service),
) -> List[Dict[str, Any]]:
    """Get all events for a specific branch."""
    return svc.get_events_for_branch(branch_id)

@router.get("/compare")
async def compare_branches(
    branch_a: str,
    branch_b: str,
    svc: EventService = Depends(get_event_service),
) -> Dict[str, Any]:
    """Compare two branches and return their diffs."""
    try:
        return svc.compare_branches(branch_a, branch_b)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/stream")
async def stream_timeline_events(
    request: Request,
    svc: EventService = Depends(get_event_service),
):
    """SSE endpoint for real-time timeline event streaming."""
    from starlette.responses import StreamingResponse
    import asyncio

    last_count = len(svc.get_all_events())

    async def event_generator():
        nonlocal last_count
        while True:
            if await request.is_disconnected():
                break
            events = svc.get_all_events()
            if len(events) > last_count:
                new_events = events[last_count:]
                for evt in new_events:
                    yield f"data: {json.dumps(evt)}\n\n"
                last_count = len(events)
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
