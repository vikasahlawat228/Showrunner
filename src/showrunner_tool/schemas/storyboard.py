"""Storyboard schemas — Panel and Page models for visual storytelling.

Panels are the atomic unit of the storyboard, belonging to scenes.
Each panel captures a single shot: camera angle, dialogue, action, image.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from showrunner_tool.schemas.base import ShowrunnerBase


class PanelType(str, Enum):
    """Shot types for storyboard panels."""
    DIALOGUE = "dialogue"
    ACTION = "action"
    ESTABLISHING = "establishing"
    CLOSEUP = "closeup"
    TRANSITION = "transition"
    MONTAGE = "montage"


class CameraAngle(str, Enum):
    """Camera angle presets (Storyboarder/FrameForge inspired)."""
    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE = "close"
    EXTREME_CLOSE = "extreme_close"
    OVER_SHOULDER = "over_shoulder"
    BIRDS_EYE = "birds_eye"
    LOW_ANGLE = "low_angle"
    DUTCH = "dutch"
    POV = "pov"


class Panel(ShowrunnerBase):
    """A single storyboard panel — one shot within a scene."""

    container_type: str = "panel"
    scene_id: str = Field(description="ID of the parent scene container")
    panel_number: int = Field(default=0, description="Order within the scene (0-indexed)")
    panel_type: PanelType = Field(default=PanelType.ACTION)
    camera_angle: CameraAngle = Field(default=CameraAngle.MEDIUM)

    # Content
    description: str = Field(default="", description="Visual description of the shot")
    dialogue: str = Field(default="", description="Character dialogue in this panel")
    action_notes: str = Field(default="", description="Stage directions / action description")
    sound_effects: str = Field(default="", description="SFX notes (e.g. 'CRASH', 'footsteps')")

    # Timing
    duration_seconds: float = Field(default=3.0, description="Estimated shot duration")

    # Image
    image_ref: str = Field(default="", description="Path or URL to generated/uploaded image")
    image_prompt: str = Field(default="", description="The prompt used to generate the image")

    # References
    characters: List[str] = Field(default_factory=list, description="Character container IDs in this panel")


class StoryboardPage(ShowrunnerBase):
    """A curated page/view of the storyboard — grouping scenes for export."""

    container_type: str = "storyboard_page"
    name: str = Field(default="Untitled Page")
    scene_ids: List[str] = Field(default_factory=list, description="Ordered scene refs")
    layout: str = Field(default="strip", description="Layout mode: 'strip', 'grid', 'manga'")


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class PanelCreate(BaseModel):
    """POST body for creating a panel."""
    scene_id: str
    panel_number: int = 0
    panel_type: PanelType = PanelType.ACTION
    camera_angle: CameraAngle = CameraAngle.MEDIUM
    description: str = ""
    dialogue: str = ""
    action_notes: str = ""
    sound_effects: str = ""
    duration_seconds: float = 3.0
    characters: List[str] = Field(default_factory=list)


class PanelUpdate(BaseModel):
    """PUT body for updating a panel."""
    panel_type: Optional[PanelType] = None
    camera_angle: Optional[CameraAngle] = None
    description: Optional[str] = None
    dialogue: Optional[str] = None
    action_notes: Optional[str] = None
    sound_effects: Optional[str] = None
    duration_seconds: Optional[float] = None
    image_ref: Optional[str] = None
    image_prompt: Optional[str] = None
    characters: Optional[List[str]] = None


class PanelReorder(BaseModel):
    """POST body for reordering panels within a scene."""
    scene_id: str
    panel_ids: List[str] = Field(description="Panel IDs in desired order")


class PanelResponse(BaseModel):
    """Response model for a panel."""
    id: str
    scene_id: str
    panel_number: int
    panel_type: str
    camera_angle: str
    description: str
    dialogue: str
    action_notes: str
    sound_effects: str
    duration_seconds: float
    image_ref: str
    image_prompt: str
    characters: List[str]
    created_at: str
    updated_at: str


class GeneratePanelsRequest(BaseModel):
    """POST body for AI panel generation."""
    panel_count: int = Field(default=6, ge=2, le=20, description="Number of panels to generate")
    style: str = Field(default="manga", description="Visual style hint: manga, western, cinematic")


class LiveSketchRequest(BaseModel):
    """POST body for live margin storyboarding."""
    recent_prose: str = Field(description="The recently typed prose chunk to visualize.")
    scene_id: Optional[str] = Field(default=None, description="Optional scene boundary.")


class LiveSketchResponse(BaseModel):
    """Returned live sketch panel."""
    panel: PanelResponse = Field(description="The fast, ephemeral sketch panel.")
