"""Genre preset schema for auto-configuring project style from genre selection."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GenrePreset(BaseModel):
    """A pre-built genre configuration bundle."""

    genre_id: str
    display_name: str
    description: str = ""
    narrative_defaults: dict[str, Any] = Field(default_factory=dict)
    visual_defaults: dict[str, Any] = Field(default_factory=dict)
    suggested_structure: str = "save_the_cat"
    mood_lighting_overrides: dict[str, str] = Field(default_factory=dict)
    common_tropes: list[str] = Field(default_factory=list)
    anti_tropes: list[str] = Field(default_factory=list)
    reference_works: list[str] = Field(default_factory=list)
    panel_style_hints: dict[str, str] = Field(default_factory=dict)
