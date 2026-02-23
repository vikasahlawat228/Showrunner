"""Model Configuration schemas for the LiteLLM resolution cascade (Phase F)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Configuration for a single model slot."""

    model: str = Field(description="LiteLLM model string, e.g. 'gemini/gemini-2.5-flash'.")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1)
    fallback_model: Optional[str] = Field(
        default=None,
        description="Fallback LiteLLM model string if the primary model fails.",
    )


class ProjectModelConfig(BaseModel):
    """Project-level model configuration stored in antigravity.yaml."""

    default_model: str = Field(
        default="gemini/gemini-2.0-flash",
        description="Default model for all AI calls in this project.",
    )
    model_overrides: Dict[str, ModelConfig] = Field(
        default_factory=dict,
        description="Per-agent model overrides, keyed by agent_id.",
    )


class ModelConfigUpdate(BaseModel):
    """Request body for updating project model configuration."""

    default_model: Optional[str] = None
    model_overrides: Optional[Dict[str, Dict[str, Any]]] = None
