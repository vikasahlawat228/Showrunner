"""Schemas for the Zen Mode writing surface."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from antigravity_tool.schemas.base import AntigravityBase


class WritingFragment(AntigravityBase):
    """A piece of writing produced in Zen Mode.

    Persisted as a container of type 'fragment' and auto-routed
    to associated buckets via entity detection.
    """

    container_type: str = "fragment"
    text: str = Field(description="The raw prose / notes the writer typed.")
    title: Optional[str] = Field(default=None, description="Optional title for this fragment.")
    scene_id: Optional[str] = Field(default=None, description="Associated scene container ID.")
    chapter: Optional[int] = Field(default=None, description="Chapter number, if applicable.")
    branch_id: str = Field(default="main", description="Timeline branch this fragment belongs to.")
    associated_containers: List[str] = Field(
        default_factory=list,
        description="IDs of containers detected / manually linked to this fragment.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata (word count, mood, tags, etc.).",
    )


# ---------------------------------------------------------------------------
# Request / Response models for the writing router
# ---------------------------------------------------------------------------


class FragmentCreateRequest(BaseModel):
    """POST body for saving a writing fragment."""

    text: str
    title: Optional[str] = None
    scene_id: Optional[str] = None
    chapter: Optional[int] = None
    branch_id: str = "main"
    associated_containers: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FragmentResponse(BaseModel):
    """Returned when a fragment is saved successfully."""

    id: str
    text: str
    title: Optional[str] = None
    associated_containers: List[str] = Field(default_factory=list)
    detected_entities: List["EntityDetection"] = Field(default_factory=list)
    word_count: int = Field(default=0)


class EntityDetectionRequest(BaseModel):
    """POST body for entity detection."""

    text: str
    auto_link: bool = Field(
        default=False,
        description="If true, automatically saves detected entities as relationships.",
    )


class EntityDetection(BaseModel):
    """A single entity mention detected in text."""

    mention: str = Field(description="The text span that matched.")
    container_id: str = Field(description="The matched container UUID.")
    container_type: str = Field(description="Type of the matched container (character, location, …).")
    container_name: str = Field(description="Display name of the matched container.")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence (0–1).")


class EntityDetectionResponse(BaseModel):
    """Response from the entity detection endpoint."""

    entities: List[EntityDetection] = Field(default_factory=list)


class ContainerContextResponse(BaseModel):
    """Formatted context summary for a container, used by @-mention popover."""

    container_id: str
    container_type: str
    name: str
    context_text: str = Field(description="Formatted prose summary of the container for LLM context.")
    attributes: Dict[str, Any] = Field(default_factory=dict)
    related_count: int = Field(default=0, description="Number of related containers.")
