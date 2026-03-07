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
    limit: int = 1000,
    offset: int = 0,
    svc: EventService = Depends(get_event_service),
) -> Dict[str, Any]:
    """Get paginated events for rendering the visual timeline.

    Query Parameters:
        limit: Maximum number of events to return (default 1000, max 5000)
        offset: Number of events to skip (for pagination)

    Returns:
        {
            "events": List[Dict],
            "count": int (total events in database),
            "limit": int,
            "offset": int
        }
    """
    # Clamp limit to reasonable bounds
    limit = max(1, min(limit, 5000))
    offset = max(0, offset)

    events = svc.get_all_events(limit=limit, offset=offset)

    # Get total count for pagination info
    try:
        cursor = svc.conn.execute("SELECT COUNT(*) as count FROM events")
        row = cursor.fetchone()
        total_count = row['count'] if row else 0
    except Exception:
        total_count = len(events)

    return {
        "events": events,
        "count": total_count,
        "limit": limit,
        "offset": offset,
    }

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

@router.post("/undo")
async def undo(
    branch_id: str = "main",
    svc: EventService = Depends(get_event_service),
) -> Dict[str, Any]:
    """Undo the last action (move branch pointer back one event)."""
    try:
        reverted_to = svc.undo(branch_id)
        if reverted_to is None:
            raise HTTPException(status_code=400, detail="Already at root, cannot undo further")

        stack = svc.get_undo_redo_stack(branch_id)
        return {
            "status": "success",
            "message": "Reverted to previous event",
            "reverted_to": reverted_to,
            "can_undo": stack["can_undo"],
            "can_redo": stack["can_redo"],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/redo")
async def redo(
    branch_id: str = "main",
    svc: EventService = Depends(get_event_service),
) -> Dict[str, Any]:
    """Redo the last undone action (move branch pointer forward one event)."""
    try:
        moved_to = svc.redo(branch_id)
        if moved_to is None:
            raise HTTPException(status_code=400, detail="Already at head, nothing to redo")

        stack = svc.get_undo_redo_stack(branch_id)
        return {
            "status": "success",
            "message": "Reapplied next event",
            "moved_to": moved_to,
            "can_undo": stack["can_undo"],
            "can_redo": stack["can_redo"],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/undo-redo-stack")
async def get_undo_redo_stack(
    branch_id: str = "main",
    svc: EventService = Depends(get_event_service),
) -> Dict[str, Any]:
    """Get the undo/redo stack for the current branch."""
    try:
        return svc.get_undo_redo_stack(branch_id)
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
