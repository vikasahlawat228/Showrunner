"""Director router -- AI director task execution."""

from fastapi import APIRouter, Depends

from antigravity_tool.server.api_schemas import DirectorActRequest, DirectorResultResponse
from antigravity_tool.server.deps import get_director_service
from antigravity_tool.services.director_service import DirectorService

router = APIRouter(prefix="/api/v1/director", tags=["director"])


@router.post("/act", response_model=DirectorResultResponse)
async def director_act(
    req: DirectorActRequest = DirectorActRequest(),
    svc: DirectorService = Depends(get_director_service),
):
    result = svc.act(step_override=req.step_override)
    return DirectorResultResponse(
        step_executed=result.step_executed,
        status=result.status,
        files_created=result.files_created,
        files_modified=result.files_modified,
        next_step=result.next_step,
        message=result.message,
    )


@router.get("/status")
async def director_status(svc: DirectorService = Depends(get_director_service)):
    return {"current_step": svc.get_current_step()}
