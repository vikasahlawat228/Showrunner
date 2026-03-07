"""Repositories for Containers and Schemas."""

from pathlib import Path
from typing import List, Optional

from showrunner_tool.repositories.base import YAMLRepository
from showrunner_tool.schemas.container import ContainerSchema, GenericContainer


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
        """Save a container to its type-specific subdirectory.

        Uses container ID to prevent filename collisions when multiple
        containers have the same name.
        """
        target_dir = self.base_dir / container.container_type
        target_dir.mkdir(parents=True, exist_ok=True)

        # Create slug from name
        slug = container.name.lower().replace(' ', '_').replace('-', '_')

        # Build filename with ID suffix for uniqueness
        # Format: name_slug-id.yaml
        filename = f"{slug}-{container.id}.yaml"
        path = target_dir / filename

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
        """Retrieve a container by its ID using indexed lookup (O(1) instead of O(n))."""
        try:
            # Try to get the path from SQLite index if available
            from showrunner_tool.repositories.sqlite_indexer import SQLiteIndexer
            # Use a default in-memory indexer for quick lookup (caller should manage indexer)
            # For now, fall back to file scan if no indexer is available
            pass
        except ImportError:
            pass

        # Fallback: O(n) file scan (slow but reliable)
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

    def get_by_id_using_index(self, container_id: str, indexer: 'SQLiteIndexer') -> Optional[GenericContainer]:
        """Retrieve a container by its ID using the SQLite indexer for O(1) lookup.

        This is much faster than get_by_id() for large numbers of containers.
        """
        # Use indexer to get the file path (relative to base_dir)
        yaml_path = indexer.get_path_by_id(container_id)
        if not yaml_path:
            return None

        # Construct the full path relative to base_dir
        # yaml_path is stored as "containers/research/name-id.yaml"
        # base_dir is "containers/", so we need to construct properly
        full_path = Path(yaml_path)

        # If the path is absolute or contains the base directory, use it directly
        if full_path.is_absolute():
            try:
                return self._load_file(full_path)
            except Exception:
                return None

        # Otherwise, construct relative to base_dir
        try:
            full_path = self.base_dir / full_path
            return self._load_file(full_path)
        except Exception:
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
        """Find and soft-delete a container YAML file by its ID."""
        if not self.base_dir.exists():
            return False
        for type_dir in self.base_dir.iterdir():
            if type_dir.is_dir():
                for yaml_file in type_dir.glob("*.yaml"):
                    try:
                        container = self._load_file(yaml_file)
                        if container.id == container_id:
                            # Use soft delete instead of permanent deletion
                            self._soft_delete_file(yaml_file, container_id)
                            return True
                    except Exception:
                        continue
        return False
