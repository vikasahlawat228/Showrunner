"""Pacing analysis schemas."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from antigravity_tool.schemas.base import AntigravityBase


class PacingMetrics(BaseModel):
    """Computed pacing metrics for a chapter or story."""

    chapter_num: Optional[int] = None
    total_scenes: int = 0
    total_panels: int = 0

    # Density metrics
    dialogue_density: float = 0.0  # ratio of dialogue panels to total
    action_density: float = 0.0  # ratio of action scenes to total
    emotional_density: float = 0.0  # ratio of emotional scenes to total

    # Scene type distribution
    scene_type_distribution: dict[str, int] = Field(default_factory=dict)

    # Tension metrics
    avg_tension: float = 0.0
    min_tension: int = 0
    max_tension: int = 0
    tension_variance: float = 0.0
    tension_progression: list[int] = Field(default_factory=list)

    # Length metrics
    avg_scene_panels: float = 0.0
    scene_length_variance: float = 0.0

    # Beat spacing
    beat_spacing: list[int] = Field(default_factory=list)  # scenes between beats


class PacingIssue(BaseModel):
    """A detected pacing issue."""

    issue_type: str = ""  # e.g. "flat_tension", "scene_type_imbalance"
    description: str = ""
    suggestion: str = ""
    location: str = ""


class PacingReport(AntigravityBase):
    """Full pacing analysis report."""

    chapter_num: Optional[int] = None
    metrics: PacingMetrics = Field(default_factory=PacingMetrics)
    issues: list[PacingIssue] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
