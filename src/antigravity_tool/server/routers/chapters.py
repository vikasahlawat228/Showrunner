"""Chapters router -- scenes, screenplays, and panels within chapters."""

from fastapi import APIRouter, Depends

from antigravity_tool.server.api_schemas import (
    SceneSummary,
    SceneDetail,
    PromptResponse,
    WriteSceneRequest,
    CompileScreenplayRequest,
    DividePanelsRequest,
    UpdateSceneRequest,
)
from antigravity_tool.server.deps import get_scene_service, get_panel_service
from antigravity_tool.services.scene_service import SceneService
from antigravity_tool.services.panel_service import PanelService

router = APIRouter(prefix="/api/v1/chapters", tags=["chapters"])


@router.get("/{chapter_num}/scenes", response_model=list[SceneSummary])
async def list_scenes(
    chapter_num: int,
    svc: SceneService = Depends(get_scene_service),
):
    scenes = svc.list_scenes(chapter_num)
    return [
        SceneSummary(
            id=s.id,
            title=s.title,
            chapter=chapter_num,
            scene_number=s.scene_number,
            scene_type=s.scene_type.value if hasattr(s.scene_type, "value") else str(s.scene_type),
            tension_level=s.tension_level,
            characters_present=s.characters_present,
        )
        for s in scenes
    ]


def _scene_to_detail(s, chapter_num: int) -> SceneDetail:
    return SceneDetail(
        id=s.id,
        title=s.title,
        chapter=chapter_num,
        scene_number=s.scene_number,
        scene_type=s.scene_type.value if hasattr(s.scene_type, "value") else str(s.scene_type),
        tension_level=s.tension_level,
        characters_present=s.characters_present,
        pov_character_id=s.pov_character_id,
        location_name=s.location_name,
        mood=s.mood,
        summary=s.summary,
    )


@router.get("/{chapter_num}/scenes/{scene_num}", response_model=SceneDetail)
async def get_scene(
    chapter_num: int,
    scene_num: int,
    svc: SceneService = Depends(get_scene_service),
):
    scene = svc.get_scene(chapter_num, scene_num)
    return _scene_to_detail(scene, chapter_num)


@router.patch("/{chapter_num}/scenes/{scene_num}", response_model=SceneDetail)
async def update_scene(
    chapter_num: int,
    scene_num: int,
    req: UpdateSceneRequest,
    svc: SceneService = Depends(get_scene_service),
):
    updates = req.model_dump(exclude_unset=True)
    updated = svc.update_scene(chapter_num, scene_num, updates)
    return _scene_to_detail(updated, chapter_num)


@router.post("/{chapter_num}/scenes/write/prompt", response_model=PromptResponse)
async def compile_write_scene_prompt(
    chapter_num: int,
    req: WriteSceneRequest,
    svc: SceneService = Depends(get_scene_service),
):
    result = svc.compile_write_prompt(
        chapter_num, req.scene,
        beat_reference=req.beat_reference,
        scene_type=req.scene_type,
    )
    return PromptResponse(
        prompt_text=result.prompt_text,
        step=result.step,
        template_used=result.template_used,
        context_keys=result.context_keys,
    )


@router.post("/{chapter_num}/screenplay/prompt", response_model=PromptResponse)
async def compile_screenplay_prompt(
    chapter_num: int,
    req: CompileScreenplayRequest,
    svc: SceneService = Depends(get_scene_service),
):
    result = svc.compile_screenplay_prompt(chapter_num, req.scene)
    return PromptResponse(
        prompt_text=result.prompt_text,
        step=result.step,
        template_used=result.template_used,
        context_keys=result.context_keys,
    )


@router.get("/{chapter_num}/panels")
async def list_panels(
    chapter_num: int,
    svc: PanelService = Depends(get_panel_service),
):
    panels = svc.list_panels(chapter_num)
    return [p.model_dump(mode="json") for p in panels]


@router.post("/{chapter_num}/panels/divide/prompt", response_model=PromptResponse)
async def compile_divide_prompt(
    chapter_num: int,
    req: DividePanelsRequest,
    svc: PanelService = Depends(get_panel_service),
):
    result = svc.compile_divide_prompt(chapter_num, req.scene)
    return PromptResponse(
        prompt_text=result.prompt_text,
        step=result.step,
        template_used=result.template_used,
        context_keys=result.context_keys,
    )
