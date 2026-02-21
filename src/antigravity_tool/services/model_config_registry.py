"""Model Configuration Registry — resolves LLM models via cascade (Phase F).

Resolution order:
  1. Per-Step config (pipeline step's model field)
  2. Per-Bucket preference (container.model_preference)
  3. Per-Agent default (from antigravity.yaml model_overrides)
  4. Project default (from antigravity.yaml default_model)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from antigravity_tool.schemas.model_config import ModelConfig, ProjectModelConfig

logger = logging.getLogger(__name__)

# Agent default models (used when no project override is configured)
AGENT_DEFAULT_MODELS: Dict[str, str] = {
    "research_agent": "gemini/gemini-2.0-pro",
    "brainstorm_agent": "gemini/gemini-2.0-flash",
    "story_architect": "gemini/gemini-2.0-flash",
    "writing_agent": "anthropic/claude-3.5-sonnet",
    "prompt_composer": "openai/gpt-4o",
    "continuity_analyst": "gemini/gemini-2.0-flash",
    "schema_wizard": "gemini/gemini-2.0-flash",
    "pipeline_director": "gemini/gemini-2.0-flash",
}

PROJECT_DEFAULT_MODEL = "gemini/gemini-2.0-flash"


class ModelConfigRegistry:
    """Resolves the correct model for any execution context via cascade."""

    def __init__(self, project_path: Path):
        self._project_path = project_path
        self._project_config = ProjectModelConfig()
        self._load_config()

    def _load_config(self) -> None:
        """Load model configuration from antigravity.yaml."""
        yaml_path = self._project_path / "antigravity.yaml"
        if not yaml_path.exists():
            logger.warning("No antigravity.yaml found at %s — using defaults", self._project_path)
            return

        try:
            from antigravity_tool.utils.io import read_yaml

            data = read_yaml(yaml_path)
            default_model = data.get("default_model", PROJECT_DEFAULT_MODEL)
            raw_overrides = data.get("model_overrides", {})

            overrides: Dict[str, ModelConfig] = {}
            for agent_id, cfg in raw_overrides.items():
                if isinstance(cfg, str):
                    overrides[agent_id] = ModelConfig(model=cfg)
                elif isinstance(cfg, dict):
                    overrides[agent_id] = ModelConfig(**cfg)

            self._project_config = ProjectModelConfig(
                default_model=default_model,
                model_overrides=overrides,
            )
        except Exception as e:
            logger.error("Failed to load model config from antigravity.yaml: %s", e)

    def resolve(
        self,
        step_config: Optional[Dict[str, Any]] = None,
        bucket_model_preference: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> ModelConfig:
        """Resolve the model to use via the cascade.

        Priority:
          1. step_config["model"] if present and non-empty
          2. bucket_model_preference (from GenericContainer.model_preference)
          3. Project-level agent override (antigravity.yaml model_overrides)
          4. Built-in agent default (AGENT_DEFAULT_MODELS)
          5. Project default model
        """
        # 1. Per-Step override
        if step_config and step_config.get("model"):
            return ModelConfig(
                model=step_config["model"],
                temperature=step_config.get("temperature", 0.7),
                max_tokens=step_config.get("max_tokens", 2048),
            )

        # 2. Per-Bucket override
        if bucket_model_preference:
            return ModelConfig(model=bucket_model_preference)

        # 3. Per-Agent override from project config
        if agent_id and agent_id in self._project_config.model_overrides:
            return self._project_config.model_overrides[agent_id]

        # 4. Built-in agent default
        if agent_id and agent_id in AGENT_DEFAULT_MODELS:
            return ModelConfig(model=AGENT_DEFAULT_MODELS[agent_id])

        # 5. Project default
        return ModelConfig(model=self._project_config.default_model)

    @property
    def project_config(self) -> ProjectModelConfig:
        """Return the current project model configuration."""
        return self._project_config

    def update_config(
        self,
        default_model: Optional[str] = None,
        model_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> ProjectModelConfig:
        """Update project model configuration and persist to antigravity.yaml."""
        from antigravity_tool.utils.io import read_yaml, write_yaml

        yaml_path = self._project_path / "antigravity.yaml"
        data = read_yaml(yaml_path) if yaml_path.exists() else {}

        if default_model is not None:
            data["default_model"] = default_model
            self._project_config.default_model = default_model

        if model_overrides is not None:
            data["model_overrides"] = model_overrides
            overrides: Dict[str, ModelConfig] = {}
            for agent_id, cfg in model_overrides.items():
                if isinstance(cfg, str):
                    overrides[agent_id] = ModelConfig(model=cfg)
                elif isinstance(cfg, dict):
                    overrides[agent_id] = ModelConfig(**cfg)
            self._project_config.model_overrides = overrides

        write_yaml(yaml_path, data)
        return self._project_config
