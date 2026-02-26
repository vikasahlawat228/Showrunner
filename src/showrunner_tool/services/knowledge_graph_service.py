"""Knowledge Graph Service for Showrunner."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from showrunner_tool.repositories.container_repo import ContainerRepository, SchemaRepository
from showrunner_tool.repositories.sqlite_indexer import SQLiteIndexer
from showrunner_tool.schemas.container import GenericContainer, ContainerSchema

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Orchestrates the Knowledge Graph indexing and query logic.

    This service synchronizes YAML-backed containers with the SQLite index
    and provides high-level relational query methods.  When a ChromaIndexer
    is provided, it also maintains a parallel vector store for RAG-style
    semantic retrieval.
    """

    def __init__(
        self,
        container_repo: ContainerRepository,
        schema_repo: SchemaRepository,
        indexer: Optional[SQLiteIndexer] = None,
        chroma_indexer: Optional["ChromaIndexer"] = None,
    ):
        self.container_repo = container_repo
        self.schema_repo = schema_repo
        self.indexer = indexer or SQLiteIndexer()
        self.chroma_indexer = chroma_indexer

        # Subscribe to repository events to keep index in sync
        self.container_repo.subscribe_save(self._on_container_save)
        self.container_repo.subscribe_delete(self._on_container_delete)

    # ------------------------------------------------------------------
    # Internal callbacks
    # ------------------------------------------------------------------

    def _container_to_document(self, container: GenericContainer) -> str:
        """Serialize a container into a single text document for embedding."""
        parts = [container.name]
        if container.attributes:
            parts.append(json.dumps(container.attributes, default=str))
        return " ".join(parts)

    def _on_container_save(self, path: Path, container: GenericContainer) -> None:
        """Callback triggered when a container is saved."""
        self.indexer.upsert_container(
            container_id=container.id,
            container_type=container.container_type,
            name=container.name,
            yaml_path=str(path),
            attributes=container.attributes,
            created_at=container.created_at.isoformat(),
            updated_at=container.updated_at.isoformat(),
            parent_id=getattr(container, "parent_id", None),
            sort_order=getattr(container, "sort_order", 0),
            tags=getattr(container, "tags", None),
            model_preference=getattr(container, "model_preference", None),
            era_id=getattr(container, "era_id", None),
            parent_version_id=getattr(container, "parent_version_id", None),
        )

        # Handle relationships if they are embedded in the container
        for rel in container.relationships:
            self.indexer.add_relationship(
                source_id=container.id,
                target_id=rel["target_id"],
                rel_type=rel["type"],
                metadata=rel.get("metadata")
            )

        # --- Vector store sync (Phase H: LiteLLM embeddings) ---
        if self.chroma_indexer is not None:
            try:
                self.chroma_indexer.upsert_embedding(
                    container_id=container.id,
                    text=self._container_to_document(container),
                    metadata={
                        "container_type": container.container_type,
                        "name": container.name,
                    },
                )
            except Exception as exc:
                logger.warning("ChromaDB upsert failed for %s: %s", container.id, exc)

    def _on_container_delete(self, path: Path, identifier: str) -> None:
        """Callback triggered when a container is deleted."""
        # Note: Identifier here is the filename stem, but the index uses UUID.
        # We might need to look up the ID by path first.
        results = self.indexer.query_containers(filters={"yaml_path": str(path)})
        for res in results:
            self.indexer.delete_container(res["id"])

            # --- Vector store cleanup ---
            if self.chroma_indexer is not None:
                try:
                    self.chroma_indexer.delete(res["id"])
                except Exception as exc:
                    logger.warning("ChromaDB delete failed for %s: %s", res["id"], exc)

    # ------------------------------------------------------------------
    # Full sync
    # ------------------------------------------------------------------

    def sync_all(self, base_dir: Path) -> None:
        """Perform a full crawl of the project directory to populate the index."""
        # 1. Sync Schemas
        for schema_file in self.schema_repo._list_files():
            schema = self.schema_repo._load_file(schema_file)
            # Schema indexing could be added if needed, but primarily we index instances

        # 2. Sync Containers (recursive search for YAMLs)
        synced = 0
        for yaml_file in base_dir.rglob("*.yaml"):
            if yaml_file.name.startswith("_") or "prompts" in str(yaml_file):
                continue

            try:
                container = self.container_repo._load_file(yaml_file)
                self._on_container_save(yaml_file, container)
                synced += 1
            except Exception:
                # Skip invalid files during crawl
                continue

        logger.info("sync_all finished: %d containers indexed", synced)

    # ------------------------------------------------------------------
    # Relational queries (existing)
    # ------------------------------------------------------------------

    def find_containers(self, container_type: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query the Knowledge Graph."""
        return self.indexer.query_containers(container_type, filters)

    def get_neighbors(self, container_id: str, rel_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get related nodes in the Knowledge Graph."""
        return self.indexer.get_related(container_id, rel_type)

    def get_all_relationships(self) -> List[Dict[str, Any]]:
        """Get all relationships in the Knowledge Graph."""
        return self.indexer.get_all_relationships()

    # ------------------------------------------------------------------
    # Era Versioning (Phase J)
    # ------------------------------------------------------------------

    def get_entity_at_era(self, entity_id: str, era_id: str) -> Optional[Dict[str, Any]]:
        """Get the version of an entity for a specific era.
        
        If a version with the specific era_id exists, return it.
        Otherwise, fall back to the global version (era_id=None).
        """
        # Search for a fork where parent_version_id == entity_id AND era_id == era_id
        forks = self.find_containers(filters={"parent_version_id": entity_id, "era_id": era_id})
        if forks:
            return forks[0]
            
        # Also check if the requested era_id is the base entity's era
        bases = self.find_containers(filters={"id": entity_id})
        if not bases:
            return None
            
        base_entity = bases[0]
        if base_entity.get("era_id") == era_id:
            return base_entity
            
        # Fall back to base entity
        return base_entity

    def create_era_fork(self, entity_id: str, new_era_id: str) -> GenericContainer:
        """Clone an existing container to a new era."""
        base_container = self.container_repo.get_by_id(entity_id)
        if not base_container:
            raise ValueError(f"Container {entity_id} not found")
            
        import uuid
        import copy
        
        # Clone it
        fork = copy.deepcopy(base_container)
        fork.id = str(uuid.uuid4())
        fork.era_id = new_era_id
        fork.parent_version_id = entity_id
        
        self.container_repo.save_container(fork)
        return fork

    def get_unresolved_threads(self, era_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query unresolved relationships."""
        all_rels = self.get_all_relationships()
        unresolved = []
        for r in all_rels:
            metadata = {}
            if r.get("metadata_json"):
                metadata = json.loads(r["metadata_json"])
                
            is_resolved = metadata.get("resolved", False)
            if is_resolved:
                continue
                
            created_in = metadata.get("created_in_era")
            
            source = self.find_containers(filters={"id": r["source_id"]})
            target = self.find_containers(filters={"id": r["target_id"]})
            source_name = source[0].get("name", r["source_id"]) if source else r["source_id"]
            target_name = target[0].get("name", r["target_id"]) if target else r["target_id"]
            
            edge_id = f"{r['source_id']}::::{r['target_id']}::::{r['rel_type']}"
            
            unresolved.append({
                "edge_id": edge_id,
                "source": source_name,
                "target": target_name,
                "relationship": r["rel_type"],
                "created_in": created_in,
                "description": metadata.get("description", "")
            })
            
        return unresolved

    def resolve_thread(self, edge_id: str, resolved_in_era: str) -> None:
        """Mark a thread as resolved by extracting source, target, type from edge_id."""
        parts = edge_id.split("::::")
        if len(parts) != 3:
            return
            
        source_id, target_id, rel_type = parts
        container = self.container_repo.get_by_id(source_id)
        if not container:
            return
            
        changed = False
        for rel in container.relationships:
            if rel.get("target_id") == target_id and rel.get("type") == rel_type:
                if "metadata" not in rel or not isinstance(rel["metadata"], dict):
                    rel["metadata"] = {}
                rel["metadata"]["resolved"] = True
                rel["metadata"]["resolved_in_era"] = resolved_in_era
                changed = True
        
        if changed:
            self.container_repo.save_container(container)

    # ------------------------------------------------------------------
    # Hierarchical queries (Phase F)
    # ------------------------------------------------------------------

    def get_children(self, parent_id: str) -> List[Dict[str, Any]]:
        """Get direct children of a container, ordered by sort_order."""
        return self.indexer.get_children(parent_id)

    def get_structure_tree(self, project_id: str) -> List[Dict[str, Any]]:
        """Build the recursive structure tree for a project.

        Returns a list of root nodes, each with a nested ``children`` list.
        Structural container types: season, arc, act, chapter, scene.
        """
        structural_types = ["season", "arc", "act", "chapter", "scene"]
        roots = self.indexer.get_roots(container_types=structural_types)

        def _build_subtree(node: Dict[str, Any]) -> Dict[str, Any]:
            children = self.indexer.get_children(node["id"])
            return {
                "id": node["id"],
                "name": node["name"],
                "container_type": node["container_type"],
                "sort_order": node.get("sort_order", 0),
                "children": [_build_subtree(c) for c in children],
            }

        return [_build_subtree(r) for r in roots]

    # ------------------------------------------------------------------
    # Semantic search (RAG)
    # ------------------------------------------------------------------

    def semantic_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search containers by semantic similarity using the vector store.

        Returns a list of container dicts enriched with a ``score`` field
        (ordinal rank — 0 = best match).

        Uses the LiteLLM-powered ``semantic_search`` on ChromaIndexer
        (Phase H) and enriches results from SQLite.

        Falls back to an empty list when the vector store is not configured.
        """
        if self.chroma_indexer is None:
            logger.warning("semantic_search called but no ChromaIndexer configured")
            return []

        # Phase H: use LiteLLM-powered semantic_search (returns IDs)
        container_ids = self.chroma_indexer.semantic_search(query, limit=limit)
        results: List[Dict[str, Any]] = []

        for rank, cid in enumerate(container_ids):
            rows = self.indexer.query_containers(filters={"id": cid})
            if rows:
                row = dict(rows[0])
                if "attributes_json" in row:
                    if isinstance(row["attributes_json"], str):
                        row["attributes"] = json.loads(row["attributes_json"])
                    del row["attributes_json"]
                row["score"] = rank
                results.append(row)
            else:
                # Container in Chroma but not in SQLite — return minimal hit
                results.append({
                    "id": cid,
                    "score": rank,
                })

        return results

    def hybrid_search(
        self,
        query: str,
        container_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Combine vector similarity with optional SQLite type filtering.

        1. Run ``semantic_search`` to get the top container IDs by vector
           similarity.
        2. Look up full container rows from SQLite.
        3. Optionally filter by *container_type*.
        4. Return enriched results with a ``score`` field.
        """
        if self.chroma_indexer is None:
            # No vector store — fall back to relational query
            return self.find_containers(container_type=container_type)

        # Step 1: vector IDs
        candidate_ids = self.chroma_indexer.semantic_search(query, limit=limit * 2)

        # Step 2 + 3: enrich from SQLite and optionally filter
        results: List[Dict[str, Any]] = []
        for rank, cid in enumerate(candidate_ids):
            rows = self.indexer.query_containers(filters={"id": cid})
            if not rows:
                continue
            row = dict(rows[0])
            # Deserialize attributes_json
            if "attributes_json" in row:
                if isinstance(row["attributes_json"], str):
                    row["attributes"] = json.loads(row["attributes_json"])
                del row["attributes_json"]
            # Apply type filter
            if container_type and row.get("container_type") != container_type:
                continue
            row["score"] = rank  # ordinal rank (0 = best)
            results.append(row)
            if len(results) >= limit:
                break

        return results
