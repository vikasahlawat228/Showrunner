"""Models router — LiteLLM model configuration cascade (Phase F).

Endpoints for listing available models, reading the current project
model config, and updating overrides in antigravity.yaml.
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends

from antigravity_tool.schemas.model_config import (
    ModelConfigUpdate,
    ProjectModelConfig,
)
from antigravity_tool.services.model_config_registry import (
    AGENT_DEFAULT_MODELS,
    ModelConfigRegistry,
)
from antigravity_tool.server.deps import get_model_config_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("/available", response_model=List[str])
async def list_available_models():
    """Return a static list of well-known LiteLLM model identifiers.

    A dynamic LiteLLM ``model_list`` integration can be added later.
    """
    return [
        "gemini/gemini-2.0-flash",
        "gemini/gemini-2.0-pro",
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
    ]


@router.get("/config", response_model=ProjectModelConfig)
async def get_model_config(
    registry: ModelConfigRegistry = Depends(get_model_config_registry),
):
    """Return the current project model cascade configuration."""
    return registry.project_config


@router.put("/config", response_model=ProjectModelConfig)
async def update_model_config(
    body: ModelConfigUpdate,
    registry: ModelConfigRegistry = Depends(get_model_config_registry),
):
    """Update model overrides in antigravity.yaml and reload the registry."""
    return registry.update_config(
        default_model=body.default_model,
        model_overrides=body.model_overrides,
    )


@router.get("/agent-defaults")
async def get_agent_defaults():
    """Return the built-in agent default model mapping."""
    return AGENT_DEFAULT_MODELS
