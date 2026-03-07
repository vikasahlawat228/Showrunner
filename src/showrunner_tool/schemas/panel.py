"""Panel schema with shot type, camera angle, composition, and image prompt assembly."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from showrunner_tool.schemas.base import ShowrunnerBase


class ShotType(str, Enum):
    EXTREME_WIDE = "extreme_wide"
    WIDE = "wide"
    MEDIUM_WIDE = "medium_wide"
    MEDIUM = "medium"
    MEDIUM_CLOSE = "medium_close"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    TWO_SHOT = "two_shot"
    OVER_SHOULDER = "over_shoulder"


class CameraAngle(str, Enum):
    EYE_LEVEL = "eye_level"
    HIGH_ANGLE = "high_angle"
    LOW_ANGLE = "low_angle"
    BIRDS_EYE = "birds_eye"
    WORMS_EYE = "worms_eye"
    DUTCH_ANGLE = "dutch_angle"
    FRONTAL = "frontal"
    PROFILE = "profile"
    THREE_QUARTER = "three_quarter"


class PanelSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    FULL_WIDTH = "full_width"
    FULL_PAGE = "full_page"
    DOUBLE_PAGE = "double_page"


class PanelWidth(str, Enum):
    """Webtoon-specific panel width control."""
    FULL = "full"
    WIDE = "wide"
    NARROW = "narrow"
    INSET = "inset"


class CharacterInPanel(BaseModel):
    character_id: str
    character_name: str
    expression: str = ""
    pose: str = ""
    position_in_frame: str = ""
    action: Optional[str] = None
    facing: str = "forward"  # forward, profile, back, three-quarter
    expression_detail: Optional[str] = None  # sad, angry, shocked, happy, neutral, etc.


class DialogueBubble(BaseModel):
    character_name: str
    text: str = ""
    bubble_type: str = "speech"
    position_hint: str = "top-left"


class Panel(ShowrunnerBase):
    scene_id: str = ""
    chapter_id: str = ""
    page_number: int = 1
    panel_number: int = 1
    screenplay_beats: list[int] = Field(default_factory=list)

    # Composition
    shot_type: ShotType = ShotType.MEDIUM
    camera_angle: CameraAngle = CameraAngle.EYE_LEVEL
    panel_size: PanelSize = PanelSize.MEDIUM
    panel_width: PanelWidth = PanelWidth.FULL
    composition_notes: str = ""

    # Webtoon-specific
    scroll_gap_before: int = 100
    aspect_ratio: str = "9:16"
    scroll_beat_type: str = "none"  # none, pause, impact, reveal — controls scroll pacing
    scroll_beat_height: int = 0  # px of white space (0 = normal, >0 = pause beat)

    # Content
    characters: list[CharacterInPanel] = Field(default_factory=list)
    background_description: str = ""
    foreground_elements: list[str] = Field(default_factory=list)
    effects: list[str] = Field(default_factory=list)
    lighting: str = ""
    mood: str = ""
    mood_tokens: list[str] = Field(default_factory=list)  # e.g., ["tense", "dark", "claustrophobic", "intimate"]

    # Text
    dialogue_bubbles: list[DialogueBubble] = Field(default_factory=list)
    sound_effects: list[str] = Field(default_factory=list)
    narration_box: Optional[str] = None

    # Image Generation
    image_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    style_tokens: Optional[str] = None
    seed_suggestion: Optional[int] = None
    reference_panel_id: Optional[str] = None

    def compile_image_prompt(
        self,
        character_dna_blocks: dict[str, str],
        style_guide_tokens: str,
    ) -> str:
        """Assemble the final image generation prompt from all panel data."""
        parts: list[str] = []

        # Style first
        parts.append(style_guide_tokens)

        # Characters with their DNA
        for char in self.characters:
            dna_block = character_dna_blocks.get(char.character_id, "")
            if dna_block:
                parts.append(dna_block)
            parts.append(
                f"{char.character_name}: {char.expression}, {char.pose}, "
                f"positioned {char.position_in_frame}"
            )
            if char.action:
                parts.append(f"Action: {char.action}")

        # Composition
        parts.append(f"Shot: {self.shot_type.value}, Angle: {self.camera_angle.value}")
        parts.append(f"Background: {self.background_description}")
        parts.append(f"Lighting: {self.lighting}, Mood: {self.mood}")

        if self.effects:
            parts.append(f"Effects: {', '.join(self.effects)}")
        if self.foreground_elements:
            parts.append(f"Foreground: {', '.join(self.foreground_elements)}")

        self.image_prompt = "\n".join(parts)
        return self.image_prompt
