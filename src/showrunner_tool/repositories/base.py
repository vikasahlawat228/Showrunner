"""Generic YAML-file-backed repository base class."""

from __future__ import annotations

from pathlib import Path
from typing import Generic, TypeVar, Type, Callable, List, Dict, Any, Optional

from pydantic import BaseModel

from showrunner_tool.errors import EntityNotFoundError, PersistenceError
from showrunner_tool.repositories.mtime_cache import MtimeCache
from showrunner_tool.utils.io import read_yaml, write_yaml

T = TypeVar("T", bound=BaseModel)


class YAMLRepository(Generic[T]):
    """Base class for YAML-file-backed repositories.

    Provides common load/save/list operations with proper error handling.
    Entity-specific repositories inherit from this and add domain logic.

    An optional ``MtimeCache`` can be provided to avoid redundant YAML
    parsing when the underlying file has not changed on disk.
    """

    def __init__(
        self,
        base_dir: Path,
        model_class: Type[T],
        cache: Optional[MtimeCache[T]] = None,
    ):
        self.base_dir = base_dir
        self.model_class = model_class
        self._cache = cache
        self._save_callbacks: List[Callable[[Path, T], None]] = []
        self._delete_callbacks: List[Callable[[Path, str], None]] = []

    def subscribe_save(self, callback: Callable[[Path, T], None]) -> None:
        """Subscribe to save events."""
        self._save_callbacks.append(callback)

    def subscribe_delete(self, callback: Callable[[Path, str], None]) -> None:
        """Subscribe to delete events."""
        self._delete_callbacks.append(callback)

    def _ensure_dir(self) -> None:
        """Create the base directory if it doesn't exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _load_file(self, path: Path) -> T:
        """Load and validate a single YAML file into a model instance."""
        if not path.exists():
            raise EntityNotFoundError(
                self.model_class.__name__, path.stem
            )

        # Check cache first
        if self._cache is not None:
            cached = self._cache.get(path)
            if cached is not None:
                return cached

        try:
            data = read_yaml(path)
            entity = self.model_class(**data)
        except EntityNotFoundError:
            raise
        except Exception as e:
            raise PersistenceError(
                f"Failed to load {path}: {e}",
                context={"path": str(path), "model": self.model_class.__name__},
            )

        # Store in cache after successful parse
        if self._cache is not None:
            self._cache.put(path, entity)

        return entity

    def _load_file_optional(self, path: Path) -> T | None:
        """Load a YAML file, returning None if it doesn't exist."""
        if not path.exists():
            return None

        # Check cache first
        if self._cache is not None:
            cached = self._cache.get(path)
            if cached is not None:
                return cached

        try:
            data = read_yaml(path)
            entity = self.model_class(**data)
        except Exception as e:
            raise PersistenceError(
                f"Failed to load {path}: {e}",
                context={"path": str(path), "model": self.model_class.__name__},
            )

        # Store in cache after successful parse
        if self._cache is not None:
            self._cache.put(path, entity)

        return entity

    def _save_file(self, path: Path, entity: T) -> Path:
        """Serialize a model instance to a YAML file."""
        self._ensure_dir()
        try:
            write_yaml(path, entity.model_dump(mode="json"))
            # Invalidate cache — next read will re-cache with new mtime
            if self._cache is not None:
                self._cache.invalidate(path)
            # Trigger callbacks
            for cb in self._save_callbacks:
                try:
                    cb(path, entity)
                except Exception:
                    # Don't let callback failure break the write
                    pass
            return path
        except Exception as e:
            raise PersistenceError(
                f"Failed to save {path}: {e}",
                context={"path": str(path), "model": self.model_class.__name__},
            )
            
    def delete(self, identifier: str) -> None:
        """Delete a YAML file by its identifier (filename stem)."""
        path = self.base_dir / f"{identifier}.yaml"
        if not path.exists():
            return

        try:
            path.unlink()
            # Invalidate cache entry for deleted file
            if self._cache is not None:
                self._cache.invalidate(path)
            # Trigger callbacks
            for cb in self._delete_callbacks:
                try:
                    cb(path, identifier)
                except Exception:
                    pass
        except Exception as e:
            raise PersistenceError(
                f"Failed to delete {path}: {e}",
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
