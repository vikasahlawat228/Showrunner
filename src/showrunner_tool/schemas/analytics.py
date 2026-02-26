"""Analytics dashboard schemas."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from showrunner_tool.schemas.base import ShowrunnerBase


class CharacterStats(BaseModel):
    """Statistics for a single character."""

    name: str = ""
    role: str = ""
    scene_appearances: int = 0
    panel_appearances: int = 0
    dialogue_count: int = 0
    total_words: int = 0


class AnalyticsReport(ShowrunnerBase):
    """Full project analytics report."""

    project_name: str = ""
    total_chapters: int = 0
    total_scenes: int = 0
    total_panels: int = 0
    total_words: int = 0

    # Completion
    chapters_complete: int = 0
    scenes_written: int = 0
    panels_with_images: int = 0
    completion_percentage: float = 0.0

    # Characters
    character_count: int = 0
    character_stats: list[CharacterStats] = Field(default_factory=list)

    # Scene types
    scene_type_distribution: dict[str, int] = Field(default_factory=dict)

    # Reading time
    estimated_reading_time: str = ""
    estimated_reading_seconds: float = 0.0

    # Generation
    images_generated: int = 0
    images_composited: int = 0
