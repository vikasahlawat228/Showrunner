"""Unified error hierarchy for Showrunner.

All domain-specific exceptions inherit from ShowrunnerError.
This module is the single source of truth for error types used
across CLI commands, API endpoints, services, and repositories.
"""

from __future__ import annotations


class ShowrunnerError(Exception):
    """Base for all Showrunner errors."""

    def __init__(self, message: str, *, context: dict | None = None):
        super().__init__(message)
        self.context = context or {}


class ProjectError(ShowrunnerError):
    """Project not found, invalid manifest, or misconfigured project."""


class EntityNotFoundError(ShowrunnerError):
    """Requested entity (character, scene, panel, etc.) does not exist."""

    def __init__(self, entity_type: str, identifier: str, **kwargs):
        super().__init__(f"{entity_type} '{identifier}' not found", **kwargs)
        self.entity_type = entity_type
        self.identifier = identifier


class SchemaValidationError(ShowrunnerError):
    """Pydantic or domain validation failed."""

    def __init__(self, message: str, *, errors: list[dict] | None = None, **kwargs):
        super().__init__(message, **kwargs)
        self.errors = errors or []


class WorkflowError(ShowrunnerError):
    """Invalid workflow state transition (e.g., skipping steps, going backwards)."""


class ContextIsolationError(ShowrunnerError):
    """Attempted to access creative room data from a story-level context.

    This is a critical security boundary -- creative room data must never
    leak into story-level prompts, or the AI will reveal plot twists.
    """


class TemplateError(ShowrunnerError):
    """Template not found or rendering failure."""


class PersistenceError(ShowrunnerError):
    """File I/O failure during load or save."""


class ConflictError(ShowrunnerError):
    """Optimistic concurrency conflict — data changed since last read.

    Raised when a UnitOfWork commit detects that another session modified
    the entity between the time it was read and the time the save was
    attempted (content_hash mismatch).
    """

    def __init__(self, entity_id: str, yaml_path: str, expected: str, actual: str):
        super().__init__(
            f"Conflict on '{yaml_path}': expected hash {expected[:8]}… "
            f"but found {actual[:8]}…",
            context={
                "entity_id": entity_id,
                "yaml_path": yaml_path,
                "expected_hash": expected,
                "actual_hash": actual,
            },
        )
        self.entity_id = entity_id
        self.yaml_path = yaml_path
        self.expected_hash = expected
        self.actual_hash = actual


class LLMError(ShowrunnerError):
    """LLM generation or parsing failure."""


class DirectorError(ShowrunnerError):
    """Director agent execution failure."""
