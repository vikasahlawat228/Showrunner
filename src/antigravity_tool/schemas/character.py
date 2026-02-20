"""Character schema with Character DNA for image generation consistency."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from antigravity_tool.schemas.base import AntigravityBase


class CharacterRole(str, Enum):
    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    DEUTERAGONIST = "deuteragonist"
    SUPPORTING = "supporting"
    MINOR = "minor"
    MENTOR = "mentor"


class FacialFeatures(BaseModel):
    face_shape: str = ""
    jaw: str = ""
    eyes: str = ""
    eye_color: str = ""
    nose: str = ""
    mouth: str = ""
    skin_tone: str = ""
    distinguishing_marks: list[str] = Field(default_factory=list)
    eyebrows: Optional[str] = None
    ears: Optional[str] = None


class HairDescription(BaseModel):
    style: str = ""
    length: str = ""
    color: str = ""
    texture: str = ""
    hairline: Optional[str] = None
    notable_details: Optional[str] = None


class BodyDescription(BaseModel):
    height: str = ""
    build: str = ""
    posture: str = ""
    notable_features: list[str] = Field(default_factory=list)


class OutfitCanon(BaseModel):
    """A character's signature outfit configuration."""

    name: str = "default"
    description: str = ""
    colors: list[str] = Field(default_factory=list)
    key_items: list[str] = Field(default_factory=list)
    prompt_tokens: str = ""


class CharacterDNA(BaseModel):
    """Immutable identity block for image generation consistency.

    Once written, this block should remain stable across all image prompts
    featuring this character to maintain visual consistency.
    """

    face: FacialFeatures = Field(default_factory=FacialFeatures)
    hair: HairDescription = Field(default_factory=HairDescription)
    body: BodyDescription = Field(default_factory=BodyDescription)
    default_outfit: OutfitCanon = Field(default_factory=OutfitCanon)
    additional_outfits: list[OutfitCanon] = Field(default_factory=list)
    age_appearance: str = ""
    gender_presentation: str = ""
    species: str = "human"

    def to_prompt_block(self) -> str:
        """Render as a stable text block for image generation prompts."""
        lines = [
            f"[CHARACTER DNA: {self.age_appearance} {self.gender_presentation} {self.species}]",
            f"Face: {self.face.face_shape} face, {self.face.jaw}, {self.face.eyes}, "
            f"{self.face.nose}, {self.face.mouth}, {self.face.skin_tone}",
        ]
        if self.face.distinguishing_marks:
            lines.append(f"Marks: {', '.join(self.face.distinguishing_marks)}")
        lines.append(
            f"Hair: {self.hair.color} {self.hair.texture} {self.hair.style}, "
            f"{self.hair.length}"
        )
        lines.append(f"Body: {self.body.height}, {self.body.build}, {self.body.posture}")
        lines.append(f"Outfit: {self.default_outfit.prompt_tokens}")
        return "\n".join(lines)


class Personality(BaseModel):
    traits: list[str] = Field(default_factory=list)
    fears: list[str] = Field(default_factory=list)
    desires: list[str] = Field(default_factory=list)
    speech_pattern: str = ""
    verbal_tics: list[str] = Field(default_factory=list)
    internal_conflict: str = ""


class CharacterArc(BaseModel):
    starting_state: str = ""
    catalyst: str = ""
    progression: list[str] = Field(default_factory=list)
    ending_state: str = ""
    arc_type: str = "positive_change"


class Relationship(BaseModel):
    target_character_id: str
    target_character_name: str
    relationship_type: str = ""
    description: str = ""
    dynamic: str = ""
    known_to_reader: bool = True


class CharacterState(BaseModel):
    """Snapshot of a character's state at a specific scene."""

    character_id: str = ""
    character_name: str = ""
    scene_id: str = ""
    chapter_id: str = ""
    emotional_state: str = ""
    physical_state: str = ""
    current_outfit: str = "default"
    injuries: list[str] = Field(default_factory=list)
    items_held: list[str] = Field(default_factory=list)
    knowledge_gained: list[str] = Field(default_factory=list)
    relationship_changes: list[str] = Field(default_factory=list)
    power_level_note: str = ""
    location: str = ""


class RelationshipEdge(BaseModel):
    """A single directed relationship edge in the character graph."""

    source_id: str = ""
    source_name: str = ""
    target_id: str = ""
    target_name: str = ""
    relationship_type: str = ""
    label: str = ""
    dynamic: str = ""
    intensity: int = 5
    known_to_reader: bool = True
    chapter_established: Optional[int] = None


class RelationshipEvolution(BaseModel):
    """How a relationship changed at a specific point."""

    source_name: str = ""
    target_name: str = ""
    chapter: int = 0
    scene: Optional[int] = None
    change_description: str = ""
    new_dynamic: str = ""
    trigger_event: str = ""


class RelationshipGraph(AntigravityBase):
    """The full character relationship graph for the project."""

    edges: list[RelationshipEdge] = Field(default_factory=list)
    evolution: list[RelationshipEvolution] = Field(default_factory=list)


class Character(AntigravityBase):
    """Complete character definition with DNA block for image consistency."""

    name: str
    aliases: list[str] = Field(default_factory=list)
    role: CharacterRole = CharacterRole.SUPPORTING
    one_line: str = ""
    backstory: str = ""
    personality: Personality = Field(default_factory=Personality)
    dna: CharacterDNA = Field(default_factory=CharacterDNA)
    arc: Optional[CharacterArc] = None
    relationships: list[Relationship] = Field(default_factory=list)
    first_appearance: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
