"""Project management schemas for multi-project isolation (Phase F)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from antigravity_tool.schemas.base import AntigravityBase


class ProjectCreate(BaseModel):
    """Request body for creating a new project."""

    name: str = Field(description="Human-readable project name.")
    description: Optional[str] = Field(
        default=None, description="Optional project description."
    )
    default_model: str = Field(
        default="gemini/gemini-2.0-flash",
        description="Default LiteLLM model string for this project.",
    )


class ProjectSummary(BaseModel):
    """Lightweight project representation for listing."""

    id: str
    name: str
    path: str
    description: Optional[str] = None
    default_model: str = "gemini/gemini-2.0-flash"
    container_count: int = 0


class ProjectSettings(BaseModel):
    """Full project settings stored in antigravity.yaml."""

    name: str
    version: str = "0.1.0"
    description: Optional[str] = None
    default_model: str = "gemini/gemini-2.0-flash"
    model_overrides: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)


class ProjectSettingsUpdate(BaseModel):
    """Partial update for project settings."""

    name: Optional[str] = None
    description: Optional[str] = None
    default_model: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None


class StructureTreeNode(BaseModel):
    """A single node in the recursive story structure tree."""

    id: str
    name: str
    container_type: str
    sort_order: int = 0
    children: List["StructureTreeNode"] = Field(default_factory=list)


class StructureTree(BaseModel):
    """The complete hierarchical structure of a project (Season → Scene)."""

    project_id: str
    roots: List[StructureTreeNode] = Field(default_factory=list)
