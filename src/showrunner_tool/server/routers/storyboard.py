"""FastAPI router for Storyboard — panel CRUD, reordering, and AI generation."""

from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException

from showrunner_tool.schemas.storyboard import (
    Panel,
    PanelCreate,
    PanelUpdate,
    PanelReorder,
    PanelResponse,
    GeneratePanelsRequest,
    LiveSketchRequest,
    LiveSketchResponse,
)
from showrunner_tool.services.storyboard_service import StoryboardService
from showrunner_tool.server.deps import get_storyboard_service

router = APIRouter(prefix="/api/v1/storyboard", tags=["storyboard"])


def _panel_to_response(p: Panel) -> PanelResponse:
    return PanelResponse(
        id=p.id,
        scene_id=p.scene_id,
        panel_number=p.panel_number,
        panel_type=p.panel_type.value,
        camera_angle=p.camera_angle.value,
        description=p.description,
        dialogue=p.dialogue,
        action_notes=p.action_notes,
        sound_effects=p.sound_effects,
        duration_seconds=p.duration_seconds,
        image_ref=p.image_ref,
        image_prompt=p.image_prompt,
        characters=p.characters,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


@router.get("/scenes/{scene_id}/panels")
async def list_panels(
    scene_id: str,
    svc: StoryboardService = Depends(get_storyboard_service),
) -> List[PanelResponse]:
    """Get all panels for a scene, ordered by panel_number."""
    panels = svc.get_panels_for_scene(scene_id)
    return [_panel_to_response(p) for p in panels]


@router.post("/panels", status_code=201)
async def create_panel(
    body: PanelCreate,
    svc: StoryboardService = Depends(get_storyboard_service),
) -> PanelResponse:
    """Create a new panel."""
    panel = Panel(
        scene_id=body.scene_id,
        panel_number=body.panel_number,
        panel_type=body.panel_type,
        camera_angle=body.camera_angle,
        description=body.description,
        dialogue=body.dialogue,
        action_notes=body.action_notes,
        sound_effects=body.sound_effects,
        duration_seconds=body.duration_seconds,
        characters=body.characters,
    )
    saved = svc.save_panel(panel)
    return _panel_to_response(saved)


@router.put("/panels/{panel_id}")
async def update_panel(
    panel_id: str,
    body: PanelUpdate,
    svc: StoryboardService = Depends(get_storyboard_service),
) -> PanelResponse:
    """Update an existing panel."""
    panel = svc.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    update_data = body.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(panel, key, value)

    saved = svc.save_panel(panel)
    return _panel_to_response(saved)


@router.delete("/panels/{panel_id}")
async def delete_panel(
    panel_id: str,
    svc: StoryboardService = Depends(get_storyboard_service),
):
    """Delete a panel."""
    if not svc.delete_panel(panel_id):
        raise HTTPException(status_code=404, detail="Panel not found")
    return {"status": "deleted", "id": panel_id}


@router.post("/panels/reorder")
async def reorder_panels(
    body: PanelReorder,
    svc: StoryboardService = Depends(get_storyboard_service),
) -> List[PanelResponse]:
    """Reorder panels within a scene."""
    panels = svc.reorder_panels(body.scene_id, body.panel_ids)
    return [_panel_to_response(p) for p in panels]


@router.post("/scenes/{scene_id}/generate", status_code=201)
async def generate_panels(
    scene_id: str,
    body: GeneratePanelsRequest | None = None,
    svc: StoryboardService = Depends(get_storyboard_service),
) -> List[PanelResponse]:
    """AI-generate panel breakdown for a scene.

    Uses the scene text (from the container) to generate panels with
    descriptions, camera angles, dialogue, and action notes.
    """
    panel_count = body.panel_count if body else 6
    style = body.style if body else "manga"

    # For now, use scene_id as context — in production, we'd load the scene container
    scene_name = f"Scene {scene_id[:8]}"
    scene_text = "A scene is being storyboarded. Use the scene context to generate dynamic, visually interesting panel compositions."

    panels = await svc.generate_panels_for_scene(
        scene_id=scene_id,
        scene_text=scene_text,
        scene_name=scene_name,
        panel_count=panel_count,
        style=style,
    )
    return [_panel_to_response(p) for p in panels]


@router.post("/scenes/{scene_id}/suggest-layout")
async def suggest_layout(
    scene_id: str,
    svc: StoryboardService = Depends(get_storyboard_service),
) -> dict:
    """AI-suggested panel layout based on narrative beat analysis."""
    # Find scene container for context
    scene_container = svc.container_repo.get_container(scene_id)
    scene_name = scene_container.name if scene_container else f"Scene {scene_id[:8]}"
    scene_text = ""
    if scene_container and scene_container.attributes:
        scene_text = scene_container.attributes.get("summary", "") or scene_container.attributes.get("text", "")
        
    if not scene_text:
        scene_text = "A key scene taking place in the story. Analyze it for dynamic visual action."

    return await svc.suggest_layout(scene_id, scene_text, scene_name)


@router.post("/live-sketch", response_model=LiveSketchResponse)
async def live_sketch(
    body: LiveSketchRequest,
    svc: StoryboardService = Depends(get_storyboard_service),
):
    """Generate ephemeral storyboard panel for recent prose."""
    panel = await svc.generate_live_sketch(body.recent_prose, body.scene_id)
    return LiveSketchResponse(panel=_panel_to_response(panel))


@router.post("/voice-to-scene")
async def voice_to_scene(
    scene_text: str = Form(...),
    scene_name: str = Form("Voice Scene"),
    panel_count: int = Form(6),
    style: str = Form("manga"),
    svc: StoryboardService = Depends(get_storyboard_service),
):
    """
    Generate storyboard panels from dictated text.
    The frontend handles speech-to-text via Web Speech API.
    This endpoint receives the transcribed text and generates panels.
    """
    # First suggest a layout based on the text
    layout = await svc.suggest_layout(
        scene_id="voice_scene",
        scene_text=scene_text,
        scene_name=scene_name,
    )

    # Then generate panels
    panels = await svc.generate_panels_for_scene(
        scene_id="voice_scene",
        scene_text=scene_text,
        scene_name=scene_name,
        panel_count=layout.get("suggested_panel_count", panel_count),
        style=style,
    )

    return {
        "layout_suggestion": layout,
        "panels": [_panel_to_response(p).model_dump() if hasattr(_panel_to_response(p), "model_dump") else getattr(_panel_to_response(p), "dict")() for p in panels],
        "scene_text": scene_text,
    }
