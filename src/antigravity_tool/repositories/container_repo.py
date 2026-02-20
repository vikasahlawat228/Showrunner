"""Repositories for Containers and Schemas."""

from pathlib import Path
from typing import List, Optional

from antigravity_tool.repositories.base import YAMLRepository
from antigravity_tool.schemas.container import ContainerSchema, GenericContainer


class SchemaRepository(YAMLRepository[ContainerSchema]):
    """Repository for managing ContainerSchema YAML files."""

    def __init__(self, base_dir: Path):
        super().__init__(base_dir, ContainerSchema)

    def get_by_name(self, name: str) -> Optional[ContainerSchema]:
        """Find a schema by its name."""
        path = self.base_dir / f"{name}.yaml"
        return self._load_file_optional(path)


class ContainerRepository(YAMLRepository[GenericContainer]):
    """Repository for managing GenericContainer YAML files."""

    def __init__(self, base_dir: Path):
        # Note: Generic containers might be stored in subdirectories by their type
        # But for the repository base, we point to the root.
        super().__init__(base_dir, GenericContainer)

    def save_container(self, container: GenericContainer) -> Path:
        """Save a container to its type-specific subdirectory."""
        target_dir = self.base_dir / container.container_type
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"{container.name.lower().replace(' ', '_')}.yaml"
        return self._save_file(path, container)

    def list_by_type(self, container_type: str) -> List[GenericContainer]:
        """List all containers of a specific type."""
        type_dir = self.base_dir / container_type
        if not type_dir.exists():
            return []
        
        # Temporarily change base_dir to list from subdirectory
        original_base = self.base_dir
        self.base_dir = type_dir
        try:
            files = self._list_files()
            return [self._load_file(f) for f in files]
        finally:
            self.base_dir = original_base
