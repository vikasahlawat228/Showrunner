"""Generic YAML-file-backed repository base class."""

from __future__ import annotations

from pathlib import Path
from typing import Generic, TypeVar, Type

from pydantic import BaseModel

from antigravity_tool.errors import EntityNotFoundError, PersistenceError
from antigravity_tool.utils.io import read_yaml, write_yaml

T = TypeVar("T", bound=BaseModel)


class YAMLRepository(Generic[T]):
    """Base class for YAML-file-backed repositories.

    Provides common load/save/list operations with proper error handling.
    Entity-specific repositories inherit from this and add domain logic.
    """

    def __init__(self, base_dir: Path, model_class: Type[T]):
        self.base_dir = base_dir
        self.model_class = model_class

    def _ensure_dir(self) -> None:
        """Create the base directory if it doesn't exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _load_file(self, path: Path) -> T:
        """Load and validate a single YAML file into a model instance."""
        if not path.exists():
            raise EntityNotFoundError(
                self.model_class.__name__, path.stem
            )
        try:
            data = read_yaml(path)
            return self.model_class(**data)
        except EntityNotFoundError:
            raise
        except Exception as e:
            raise PersistenceError(
                f"Failed to load {path}: {e}",
                context={"path": str(path), "model": self.model_class.__name__},
            )

    def _load_file_optional(self, path: Path) -> T | None:
        """Load a YAML file, returning None if it doesn't exist."""
        if not path.exists():
            return None
        try:
            data = read_yaml(path)
            return self.model_class(**data)
        except Exception as e:
            raise PersistenceError(
                f"Failed to load {path}: {e}",
                context={"path": str(path), "model": self.model_class.__name__},
            )

    def _save_file(self, path: Path, entity: T) -> Path:
        """Serialize a model instance to a YAML file."""
        self._ensure_dir()
        try:
            write_yaml(path, entity.model_dump(mode="json"))
            return path
        except Exception as e:
            raise PersistenceError(
                f"Failed to save {path}: {e}",
                context={"path": str(path), "model": self.model_class.__name__},
            )

    def _list_files(self, pattern: str = "*.yaml") -> list[Path]:
        """List YAML files in the base directory, excluding _ prefixed files."""
        if not self.base_dir.exists():
            return []
        return sorted(
            f for f in self.base_dir.glob(pattern)
            if not f.name.startswith("_")
        )
