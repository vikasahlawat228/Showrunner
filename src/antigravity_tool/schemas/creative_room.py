"""Creative Room schemas - author-only isolated context.

These schemas define data that MUST NEVER be exposed to story-generation prompts.
Only evaluation and author-only commands access this data.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from antigravity_tool.schemas.base import AntigravityBase


class PlotTwist(BaseModel):
    id: str = ""
    name: str = ""
    description: str = ""
    setup_scenes: list[str] = Field(default_factory=list)
    reveal_scene: Optional[str] = None
    affected_characters: list[str] = Field(default_factory=list)
    reader_learns_at: Optional[str] = None


class CharacterSecret(BaseModel):
    character_id: str
    character_name: str
    secret: str = ""
    known_by: list[str] = Field(default_factory=list)
    revealed_to_reader_at: Optional[str] = None
    dramatic_irony_note: Optional[str] = None


class ForeshadowingEntry(BaseModel):
    id: str = ""
    plant_description: str = ""
    plant_scene_id: str = ""
    payoff_description: str = ""
    payoff_scene_id: Optional[str] = None
    subtlety_level: str = "moderate"
    status: str = "planted"


class TrueMechanic(BaseModel):
    """World rules that the reader does not yet know."""
    name: str = ""
    true_description: str = ""
    apparent_description: str = ""
    reveal_plan: str = ""
    reveal_scene_id: Optional[str] = None


class ReaderKnowledgeState(AntigravityBase):
    """Snapshot of what the reader knows at a specific point in the story.

    This acts as a positive-list filter: rather than blocking secrets,
    it enumerates what the reader knows. Story prompts receive this
    and are constrained to only reference what's listed here.
    """

    chapter_id: str = ""
    scene_id: Optional[str] = None
    position_label: str = ""

    known_characters: list[str] = Field(default_factory=list)
    known_character_traits: dict[str, list[str]] = Field(default_factory=dict)
    known_locations: list[str] = Field(default_factory=list)
    known_world_rules: list[str] = Field(default_factory=list)
    known_relationships: list[str] = Field(default_factory=list)
    revealed_secrets: list[str] = Field(default_factory=list)
    active_questions: list[str] = Field(default_factory=list)
    false_beliefs: list[str] = Field(default_factory=list)


class CreativeRoom(AntigravityBase):
    """The author's private planning space. NEVER exposed to story prompts."""

    plot_twists: list[PlotTwist] = Field(default_factory=list)
    character_secrets: list[CharacterSecret] = Field(default_factory=list)
    foreshadowing_map: list[ForeshadowingEntry] = Field(default_factory=list)
    true_mechanics: list[TrueMechanic] = Field(default_factory=list)
    ending_plans: str = ""
    thematic_threads: list[str] = Field(default_factory=list)
    author_notes: list[str] = Field(default_factory=list)
