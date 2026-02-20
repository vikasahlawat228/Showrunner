"""Style guide schemas for visual and narrative consistency."""

from __future__ import annotations

from pydantic import Field

from antigravity_tool.schemas.base import AntigravityBase


class VisualStyleGuide(AntigravityBase):
    art_style: str = "manhwa"
    sub_style: str = ""
    genre_preset: str = ""
    genre_tags: list[str] = Field(default_factory=list)
    line_weight: str = "clean thin lines"
    color_palette: list[str] = Field(default_factory=list)
    color_mode: str = "full color"
    shading_style: str = "cel shading"
    background_detail: str = "detailed"
    character_proportions: str = "realistic with slightly stylized features"
    visual_motifs: list[str] = Field(default_factory=list)
    reference_artists: list[str] = Field(default_factory=list)
    prompt_style_tokens: str = ""

    # Webtoon defaults
    default_aspect_ratio: str = "9:16"
    panel_format: str = "vertical_scroll"

    # Mood lighting presets
    mood_lighting_presets: dict[str, str] = Field(default_factory=lambda: {
        "tense": "high contrast, deep shadows, cool blue undertones",
        "romantic": "soft warm light, golden hour glow, gentle lens flare",
        "action": "dramatic lighting, motion blur accents, high saturation",
        "melancholic": "muted tones, overcast diffused light, desaturated",
        "mysterious": "rim lighting, deep shadows, single light source",
        "peaceful": "even natural light, warm palette, soft shadows",
    })


class NarrativeStyleGuide(AntigravityBase):
    tone: str = ""
    pov_default: str = "third person limited"
    genre_preset: str = ""
    genre_tags: list[str] = Field(default_factory=list)
    prose_style: str = ""
    dialogue_style: str = ""
    pacing_preference: str = ""
    themes: list[str] = Field(default_factory=list)
    taboos: list[str] = Field(default_factory=list)
    inspirations: list[str] = Field(default_factory=list)
