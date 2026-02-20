"""Timeline router -- Event Sourcing log manipulation."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from antigravity_tool.server.deps import get_event_service
from antigravity_tool.repositories.event_sourcing_repo import EventService

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
            
    # Typically, checkout would manipulate the Knowledge Graph to reflect the new state
    # This is a stub for the full checkout side-effect capability
    return {"status": "success", "event_id": req.event_id, "branch": req.branch_name}
