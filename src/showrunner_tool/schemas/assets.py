"""Reference image and asset management schemas."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from showrunner_tool.schemas.base import ShowrunnerBase


class ReferenceType(str, Enum):
    CHARACTER = "character"
    LOCATION = "location"
    OUTFIT = "outfit"
    MOOD_BOARD = "mood_board"
    STYLE = "style"
    PROP = "prop"
    EFFECT = "effect"


class ReferenceImage(ShowrunnerBase):
    """A reference image with metadata."""

    filename: str = ""
    reference_type: ReferenceType = ReferenceType.STYLE
    linked_entity_name: str = ""  # character name, location name, etc.
    linked_entity_id: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    source: str = ""  # "generated", "uploaded", "external"


class ReferenceLibrary(ShowrunnerBase):
    """Collection of all reference images for the project."""

    references: list[ReferenceImage] = Field(default_factory=list)

    def get_for_entity(self, name: str) -> list[ReferenceImage]:
        """Get all references linked to a specific entity."""
        return [r for r in self.references if r.linked_entity_name == name]

    def get_by_type(self, ref_type: ReferenceType) -> list[ReferenceImage]:
        """Get all references of a specific type."""
        return [r for r in self.references if r.reference_type == ref_type]
