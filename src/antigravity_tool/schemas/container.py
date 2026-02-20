"""Generic Container and Schema models for Showrunner."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Field, create_model

from antigravity_tool.schemas.base import AntigravityBase


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


class FieldDefinition(AntigravityBase):
    """Definition of a single field within a Schema."""

    name: str
    field_type: FieldType = FieldType.STRING
    description: Optional[str] = None
    default: Any = None
    required: bool = False
    options: Optional[List[str]] = None  # For ENUM fields
    target_type: Optional[str] = None  # For REFERENCE fields


class ContainerSchema(AntigravityBase):
    """Template for a specific type of container (e.g., 'Character', 'Spell')."""

    name: str  # e.g., "Character"
    display_name: str
    description: Optional[str] = None
    fields: List[FieldDefinition] = Field(default_factory=list)

    def to_pydantic_model(self) -> type[AntigravityBase]:
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

        # Create the dynamic model, inheriting from AntigravityBase
        return create_model(
            self.name,
            __base__=AntigravityBase,
            **field_definitions
        )


class GenericContainer(AntigravityBase):
    """A polymorphic container instance that holds dynamic attributes."""

    container_type: str  # References a ContainerSchema.name
    name: str  # Display name for this specific instance
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    # Relationships can be handled as a special attribute or a separate table
    # For now, let's keep it in attributes or a list of IDs
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
