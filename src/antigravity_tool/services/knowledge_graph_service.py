"""Knowledge Graph Service for Showrunner."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from antigravity_tool.repositories.container_repo import ContainerRepository, SchemaRepository
from antigravity_tool.repositories.sqlite_indexer import SQLiteIndexer
from antigravity_tool.schemas.container import GenericContainer, ContainerSchema


class KnowledgeGraphService:
    """Orchestrates the Knowledge Graph indexing and query logic.
    
    This service synchronizes YAML-backed containers with the SQLite index
    and provides high-level relational query methods.
    """

    def __init__(
        self,
        container_repo: ContainerRepository,
        schema_repo: SchemaRepository,
        indexer: Optional[SQLiteIndexer] = None
    ):
        self.container_repo = container_repo
        self.schema_repo = schema_repo
        self.indexer = indexer or SQLiteIndexer()
        
        # Subscribe to repository events to keep index in sync
        self.container_repo.subscribe_save(self._on_container_save)
        self.container_repo.subscribe_delete(self._on_container_delete)

    def _on_container_save(self, path: Path, container: GenericContainer) -> None:
        """Callback triggered when a container is saved."""
        self.indexer.upsert_container(
            container_id=container.id,
            container_type=container.container_type,
            name=container.name,
            yaml_path=str(path),
            attributes=container.attributes,
            created_at=container.created_at.isoformat(),
            updated_at=container.updated_at.isoformat()
        )
        
        # Handle relationships if they are embedded in the container
        for rel in container.relationships:
            self.indexer.add_relationship(
                source_id=container.id,
                target_id=rel["target_id"],
                rel_type=rel["type"],
                metadata=rel.get("metadata")
            )

    def _on_container_delete(self, path: Path, identifier: str) -> None:
        """Callback triggered when a container is deleted."""
        # Note: Identifier here is the filename stem, but the index uses UUID.
        # We might need to look up the ID by path first.
        results = self.indexer.query_containers(filters={"yaml_path": str(path)})
        for res in results:
            self.indexer.delete_container(res["id"])

    def sync_all(self, base_dir: Path) -> None:
        """Perform a full crawl of the project directory to populate the index."""
        # 1. Sync Schemas
        for schema_file in self.schema_repo._list_files():
            schema = self.schema_repo._load_file(schema_file)
            # Schema indexing could be added if needed, but primarily we index instances
            
        # 2. Sync Containers (recursive search for YAMLs)
        for yaml_file in base_dir.rglob("*.yaml"):
            if yaml_file.name.startswith("_") or "prompts" in str(yaml_file):
                continue
                
            try:
                container = self.container_repo._load_file(yaml_file)
                self._on_container_save(yaml_file, container)
            except Exception:
                # Skip invalid files during crawl
                continue

    def find_containers(self, container_type: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query the Knowledge Graph."""
        return self.indexer.query_containers(container_type, filters)

    def get_neighbors(self, container_id: str, rel_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get related nodes in the Knowledge Graph."""
        return self.indexer.get_related(container_id, rel_type)

    def get_all_relationships(self) -> List[Dict[str, Any]]:
        """Get all relationships in the Knowledge Graph."""
        return self.indexer.get_all_relationships()
