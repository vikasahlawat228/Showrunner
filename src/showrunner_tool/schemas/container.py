"""Generic Container and Schema models for Showrunner."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Field, create_model

from showrunner_tool.schemas.base import ShowrunnerBase


class FieldType(str, Enum):
    """Supported primitive types for custom schema fields."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST_STRING = "list[string]"
    JSON = "json"
    ENUM = "enum"
    REFERENCE = "reference"


class FieldDefinition(ShowrunnerBase):
    """Definition of a single field within a Schema."""

    name: str
    field_type: FieldType = FieldType.STRING
    description: Optional[str] = None
    default: Any = None
    required: bool = False
    options: Optional[List[str]] = None  # For ENUM fields
    target_type: Optional[str] = None  # For REFERENCE fields


class ContainerSchema(ShowrunnerBase):
    """Template for a specific type of container (e.g., 'Character', 'Spell')."""

    name: str  # e.g., "Character"
    display_name: str
    description: Optional[str] = None
    fields: List[FieldDefinition] = Field(default_factory=list)

    def to_pydantic_model(self) -> type[ShowrunnerBase]:
        """Dynamically generate a Pydantic model class for this schema."""
        field_definitions: Dict[str, Any] = {}

        type_mapping = {
            FieldType.STRING: str,
            FieldType.INTEGER: int,
            FieldType.FLOAT: float,
            FieldType.BOOLEAN: bool,
            FieldType.LIST_STRING: List[str],
            FieldType.JSON: Dict[str, Any],
            FieldType.REFERENCE: str,  # Stored as UUID string
        }

        for field in self.fields:
            if field.field_type == FieldType.ENUM and field.options:
                python_type = Literal[tuple(field.options)]
            else:
                python_type = type_mapping.get(field.field_type, Any)

            if not field.required:
                python_type = Optional[python_type]

            field_definitions[field.name] = (python_type, field.default)

        # Create the dynamic model, inheriting from ShowrunnerBase
        return create_model(
            self.name,
            __base__=ShowrunnerBase,
            **field_definitions
        )


class GenericContainer(ShowrunnerBase):
    """A polymorphic container instance that holds dynamic attributes."""

    container_type: str  # References a ContainerSchema.name
    name: str  # Display name for this specific instance
    attributes: Dict[str, Any] = Field(default_factory=dict)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)

    # ── Phase F additions ─────────────────────────────────────────
    context_window: Optional[str] = Field(
        default=None,
        description="LLM-friendly auto-summary of this container's content.",
    )
    timeline_positions: List[str] = Field(
        default_factory=list,
        description="Story positions, e.g. ['S1.Arc1.Act2.Ch3.Sc5'].",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Free-form labels, e.g. ['#act1', '#subplot-revenge'].",
    )
    model_preference: Optional[str] = Field(
        default=None,
        description="LiteLLM model override for AI calls involving this container.",
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="Hierarchical parent container ID (e.g. Chapter → Act).",
    )
    sort_order: int = Field(
        default=0,
        description="Position among sibling containers under the same parent.",
    )

    # ── Phase J additions (Entity Versioning) ─────────────────────
    era_id: Optional[str] = Field(
        default=None,
        description="Version identifier for eras (e.g., 'season_1', 'season_2'). None means global.",
    )
    parent_version_id: Optional[str] = Field(
        default=None,
        description="ID of the entity version this was forked from.",
    )
