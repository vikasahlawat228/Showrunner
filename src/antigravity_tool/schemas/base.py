"""Base schema for all Antigravity data objects."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from antigravity_tool.utils.ids import generate_id


class AntigravityBase(BaseModel):
    """Base for all Antigravity data objects with common metadata."""

    id: str = Field(default_factory=generate_id)
    schema_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None

    model_config = {"extra": "allow"}
