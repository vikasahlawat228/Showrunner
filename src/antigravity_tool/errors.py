"""Unified error hierarchy for Antigravity.

All domain-specific exceptions inherit from AntigravityError.
This module is the single source of truth for error types used
across CLI commands, API endpoints, services, and repositories.
"""

from __future__ import annotations


class AntigravityError(Exception):
    """Base for all Antigravity errors."""

    def __init__(self, message: str, *, context: dict | None = None):
        super().__init__(message)
        self.context = context or {}


class ProjectError(AntigravityError):
    """Project not found, invalid manifest, or misconfigured project."""


class EntityNotFoundError(AntigravityError):
    """Requested entity (character, scene, panel, etc.) does not exist."""

    def __init__(self, entity_type: str, identifier: str, **kwargs):
        super().__init__(f"{entity_type} '{identifier}' not found", **kwargs)
        self.entity_type = entity_type
        self.identifier = identifier


class SchemaValidationError(AntigravityError):
    """Pydantic or domain validation failed."""

    def __init__(self, message: str, *, errors: list[dict] | None = None, **kwargs):
        super().__init__(message, **kwargs)
        self.errors = errors or []


class WorkflowError(AntigravityError):
    """Invalid workflow state transition (e.g., skipping steps, going backwards)."""


class ContextIsolationError(AntigravityError):
    """Attempted to access creative room data from a story-level context.

    This is a critical security boundary -- creative room data must never
    leak into story-level prompts, or the AI will reveal plot twists.
    """


class TemplateError(AntigravityError):
    """Template not found or rendering failure."""


class PersistenceError(AntigravityError):
    """File I/O failure during load or save."""


class LLMError(AntigravityError):
    """LLM generation or parsing failure."""


class DirectorError(AntigravityError):
    """Director agent execution failure."""
