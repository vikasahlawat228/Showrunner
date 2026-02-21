from fastapi import APIRouter, Depends, HTTPException
from antigravity_tool.server.api_schemas import ReadingSimResult
from antigravity_tool.server.deps import get_reader_sim_service
from antigravity_tool.services.reader_sim_service import ReaderSimService

router = APIRouter(prefix="/api/v1/preview", tags=["preview"])

@router.get("/scene/{scene_id}", response_model=ReadingSimResult)
async def get_preview_scene(
    scene_id: str,
    svc: ReaderSimService = Depends(get_reader_sim_service),
):
    try:
        return svc.simulate_reading(scene_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
@router.get("/chapter/{chapter}", response_model=list[ReadingSimResult])
async def get_preview_chapter(
    chapter: int,
    svc: ReaderSimService = Depends(get_reader_sim_service),
):
    return svc.simulate_chapter_reading(chapter)
