"""Story structure schemas for beat sheets, arcs, and acts."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from antigravity_tool.schemas.base import AntigravityBase


class StructureType(str, Enum):
    SAVE_THE_CAT = "save_the_cat"
    HEROS_JOURNEY = "heros_journey"
    STORY_CIRCLE = "story_circle"
    THREE_ACT = "three_act"
    KISHOTENKETSU = "kishotenketsu"
    CUSTOM = "custom"


class StoryBeat(BaseModel):
    beat_name: str
    beat_number: int
    act: str = ""
    description: str = ""
    content: str = ""
    target_percentage: float = 0.0
    chapter_ids: list[str] = Field(default_factory=list)
    scene_ids: list[str] = Field(default_factory=list)
    status: str = "planned"


class CharacterArcBeat(BaseModel):
    character_id: str
    character_name: str
    beat_name: str = ""
    description: str = ""
    story_beat_ref: Optional[str] = None


class SubArcType(str, Enum):
    TRAINING = "training"
    TOURNAMENT = "tournament"
    FLASHBACK = "flashback"
    ROMANCE = "romance"
    INVESTIGATION = "investigation"
    QUEST = "quest"
    REVELATION = "revelation"
    CUSTOM = "custom"


class SubArc(AntigravityBase):
    """A nested story arc within the main structure."""

    name: str = ""
    arc_type: SubArcType = SubArcType.CUSTOM
    description: str = ""
    focus_character_ids: list[str] = Field(default_factory=list)
    chapter_start: Optional[int] = None
    chapter_end: Optional[int] = None
    beats: list[StoryBeat] = Field(default_factory=list)
    parent_beat_ref: Optional[str] = None
    status: str = "planned"


class StoryStructure(AntigravityBase):
    structure_type: StructureType = StructureType.SAVE_THE_CAT
    title: str = ""
    logline: str = ""
    premise: str = ""
    beats: list[StoryBeat] = Field(default_factory=list)
    character_arcs: list[CharacterArcBeat] = Field(default_factory=list)
    act_summaries: dict[str, str] = Field(default_factory=dict)
    total_chapters_planned: int = 0
    sub_arcs: list[SubArc] = Field(default_factory=list)
