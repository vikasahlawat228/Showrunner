"""Screenplay schema with sequential beats for dialogue, action, and narration."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from antigravity_tool.schemas.base import AntigravityBase


class BeatType(str, Enum):
    ACTION = "action"
    DIALOGUE = "dialogue"
    INTERNAL = "internal_monologue"
    NARRATION = "narration"
    SFX = "sound_effect"
    TRANSITION = "transition"


class ScreenplayBeat(BaseModel):
    beat_number: int
    type: BeatType
    character_id: Optional[str] = None
    character_name: Optional[str] = None
    content: str = ""
    emotion: Optional[str] = None
    action_description: Optional[str] = None
    parenthetical: Optional[str] = None
    panel_hint: Optional[str] = None


class Screenplay(AntigravityBase):
    scene_id: str = ""
    chapter_id: str = ""
    scene_title: str = ""
    setting_line: str = ""
    beats: list[ScreenplayBeat] = Field(default_factory=list)
    estimated_panels: int = 0
    pacing_note: str = ""
