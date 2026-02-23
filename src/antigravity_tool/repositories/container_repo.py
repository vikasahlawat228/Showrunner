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

    def get_by_id(self, container_id: str) -> Optional[GenericContainer]:
        """Search all type subdirectories for a container with this ID."""
        if not self.base_dir.exists():
            return None
        for type_dir in self.base_dir.iterdir():
            if type_dir.is_dir():
                for yaml_file in type_dir.glob("*.yaml"):
                    try:
                        container = self._load_file(yaml_file)
                        if container.id == container_id:
                            return container
                    except Exception:
                        continue
        return None

    def list_all(self) -> List[GenericContainer]:
        """List all containers across all type subdirectories."""
        results: List[GenericContainer] = []
        if not self.base_dir.exists():
            return results
        for type_dir in self.base_dir.iterdir():
            if type_dir.is_dir() and not type_dir.name.startswith((".","_")):
                for yaml_file in type_dir.glob("*.yaml"):
                    try:
                        results.append(self._load_file(yaml_file))
                    except Exception:
                        continue
        return results

    def delete_by_id(self, container_id: str) -> bool:
        """Find and delete a container YAML file by its ID."""
        if not self.base_dir.exists():
            return False
        for type_dir in self.base_dir.iterdir():
            if type_dir.is_dir():
                for yaml_file in type_dir.glob("*.yaml"):
                    try:
                        container = self._load_file(yaml_file)
                        if container.id == container_id:
                            yaml_file.unlink()
                            return True
                    except Exception:
                        continue
        return False
