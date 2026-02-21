"""Prompt template schemas for structured prompt assembly.

Opal-style templates with named slots that auto-fill from bucket context.
"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field

from antigravity_tool.schemas.base import AntigravityBase


class PromptSlot(BaseModel):
    """A named slot in a prompt template that gets filled with context."""

    name: str = Field(description="Slot name used in {{name}} template syntax")
    slot_type: str = Field(
        default="string",
        description="Type: 'reference', 'string', 'enum', 'text'",
    )
    target_type: Optional[str] = Field(
        default=None,
        description="For reference slots: the container type to pull from (character, scene, etc.)",
    )
    required: bool = Field(default=True)
    auto_fill: Optional[str] = Field(
        default=None,
        description="Auto-fill rule, e.g. 'characters_in_scene', 'world_rules'",
    )
    default: Optional[Any] = Field(default=None)
    description: Optional[str] = Field(default=None)


class PromptTemplate(AntigravityBase):
    """A reusable prompt template with structured slots.

    Templates use Handlebars-style syntax: {{slot_name}} for slot references.
    They are stored as YAML containers.
    """

    container_type: str = "prompt_template"
    name: str = Field(description="Template display name")
    description: str = Field(default="", description="What this template produces")
    category: str = Field(
        default="general",
        description="Template category: 'scene_writing', 'character_dev', 'dialogue', 'image_prompt', etc.",
    )
    slots: List[PromptSlot] = Field(default_factory=list)
    template: str = Field(
        description="The prompt template text with {{slot_name}} placeholders"
    )

    def render(self, slot_values: dict[str, Any]) -> str:
        """Render the template by replacing {{slot_name}} with values."""
        result = self.template
        for slot in self.slots:
            placeholder = "{{" + slot.name + "}}"
            value = slot_values.get(slot.name)
            if value is None:
                value = slot.default or f"[{slot.name} not provided]"
            result = result.replace(placeholder, str(value))
        return result


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------


class PromptTemplateCreate(BaseModel):
    """POST body for creating a prompt template."""

    name: str
    description: str = ""
    category: str = "general"
    slots: List[PromptSlot] = Field(default_factory=list)
    template: str


class PromptTemplateResponse(BaseModel):
    """Response model for a prompt template."""

    id: str
    name: str
    description: str
    category: str
    slots: List[PromptSlot]
    template: str
