"""Scene schema with setting, mood, lighting, and narrative details."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import Field

from showrunner_tool.schemas.base import ShowrunnerBase


class TimeOfDay(str, Enum):
    DAWN = "dawn"
    MORNING = "morning"
    MIDDAY = "midday"
    AFTERNOON = "afternoon"
    DUSK = "dusk"
    EVENING = "evening"
    NIGHT = "night"
    LATE_NIGHT = "late_night"


class Weather(str, Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    SNOW = "snow"
    FOG = "fog"
    WIND = "wind"


class SceneType(str, Enum):
    ACTION = "action"
    DIALOGUE = "dialogue"
    FLASHBACK = "flashback"
    MONTAGE = "montage"
    TRAINING = "training"
    REVEAL = "reveal"
    CONFRONTATION = "confrontation"
    CHASE = "chase"
    CALM = "calm_before_storm"
    TRANSITION = "transition"
    EMOTIONAL = "emotional"
    WORLDBUILDING = "worldbuilding"
    CUSTOM = "custom"


class Scene(ShowrunnerBase):
    chapter_id: str = ""
    scene_number: int = 1
    title: str = ""
    summary: str = ""
    purpose: str = ""
    beat_reference: Optional[str] = None
    scene_type: SceneType = SceneType.CUSTOM
    sub_arc_id: Optional[str] = None
    tension_level: int = 5
    pacing: str = "normal"
    estimated_panels: Optional[int] = None

    # Character state snapshots
    character_states_start: list[dict] = Field(default_factory=list)
    character_states_end: list[dict] = Field(default_factory=list)

    # Branching (Phase 4)
    branch_id: Optional[str] = None
    branch_parent_scene_id: Optional[str] = None
    branch_label: str = ""
    is_canonical: bool = True

    # Setting
    location_id: Optional[str] = None
    location_name: str = ""
    location_description: str = ""
    time_of_day: TimeOfDay = TimeOfDay.MORNING
    weather: Optional[Weather] = None
    mood: str = ""
    lighting: str = ""
    ambient_sounds: list[str] = Field(default_factory=list)

    # Characters
    characters_present: list[str] = Field(default_factory=list)
    pov_character_id: Optional[str] = None
    character_goals_in_scene: dict[str, str] = Field(default_factory=dict)

    # Narrative
    opening_hook: str = ""
    key_events: list[str] = Field(default_factory=list)
    emotional_arc: str = ""
    closing_state: str = ""
    cliffhanger: Optional[str] = None

    # Connections
    leads_to_scene_id: Optional[str] = None
    follows_scene_id: Optional[str] = None
    reveals: list[str] = Field(default_factory=list)
    plants: list[str] = Field(default_factory=list)

    tags: list[str] = Field(default_factory=list)
