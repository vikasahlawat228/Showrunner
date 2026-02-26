"""ProjectSnapshotFactory — batch-loads project data for context assembly.

Uses SQLite index for entity resolution + MtimeCache for read caching.
Loads all needed entities in a single pass instead of N individual reads.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from showrunner_tool.schemas.dal import ContextScope, ProjectSnapshot
from showrunner_tool.utils.io import read_yaml

logger = logging.getLogger(__name__)

# Maps workflow step -> list of entity types needed for that step
STEP_ENTITY_MAP: Dict[str, List[str]] = {
    "world_building": ["world_settings"],
    "character_creation": ["world_settings", "character"],
    "story_outline": ["world_settings", "character", "story_structure"],
    "scene_writing": ["world_settings", "character", "story_structure", "scene", "style_guide"],
    "screenplay": ["character", "scene", "screenplay"],
    "panel_composition": ["character", "scene", "screenplay", "panel", "style_guide"],
    "evaluation": ["world_settings", "character", "story_structure", "scene", "style_guide", "creative_room"],
    "brainstorm": ["world_settings", "character", "story_structure"],
    "research": ["world_settings"],
}


class ProjectSnapshotFactory:
    """Batch-loads project data for a given context scope in a single pass.

    1. Query SQLite for all entity IDs matching the scope
    2. Batch-resolve YAML paths from SQLite (no directory scanning)
    3. Batch-load from MtimeCache (returns cached for unchanged files)
    4. Hydrate from YAML only for cache misses
    5. Route loaded entities into ProjectSnapshot fields
    """

    def __init__(self, sqlite_indexer, mtime_cache=None):
        self._indexer = sqlite_indexer
        self._cache = mtime_cache

    def load(self, scope: ContextScope) -> ProjectSnapshot:
        """Load all entities needed for the given scope."""
        start = time.monotonic()

        # Determine which entity types we need
        needed_types = STEP_ENTITY_MAP.get(
            scope.step, ["world_settings", "character", "scene"]
        )

        # Query SQLite for matching entities
        all_entities: List[Dict[str, Any]] = []
        for entity_type in needed_types:
            filters: Optional[Dict[str, Any]] = None

            # Apply scope filters for scene-specific types
            if entity_type == "scene" and scope.chapter is not None:
                filters = {"chapter": scope.chapter}
                if scope.scene is not None:
                    filters["scene_number"] = scope.scene
            elif entity_type == "character" and scope.character_name:
                filters = {"name": scope.character_name}

            rows = self._indexer.query_entities(
                entity_type=entity_type, filters=filters
            )
            all_entities.extend(rows)

        # Batch-load YAML content with caching
        cache_hits = 0
        cache_misses = 0
        loaded: List[Dict[str, Any]] = []

        for row in all_entities:
            yaml_path = Path(row.get("yaml_path", ""))
            entity_data = None

            # Try cache first
            if self._cache and yaml_path.exists():
                cached = self._cache.get(yaml_path)
                if cached is not None:
                    if isinstance(cached, dict):
                        entity_data = cached
                    elif hasattr(cached, "model_dump"):
                        entity_data = cached.model_dump()
                    else:
                        entity_data = {"_raw": cached}
                    cache_hits += 1

            # Cache miss -- read from disk
            if entity_data is None and yaml_path.exists():
                try:
                    entity_data = read_yaml(yaml_path)
                    # Put in cache for next time
                    if self._cache:
                        self._cache.put(yaml_path, entity_data)
                    cache_misses += 1
                except Exception as e:
                    logger.warning("Failed to read %s: %s", yaml_path, e)
                    # Fall back to attributes_json from SQLite
                    attrs = row.get("attributes_json", "{}")
                    entity_data = (
                        json.loads(attrs) if isinstance(attrs, str) else attrs
                    )
                    cache_misses += 1
            elif entity_data is None:
                # File doesn't exist -- use SQLite attributes
                attrs = row.get("attributes_json", "{}")
                entity_data = (
                    json.loads(attrs) if isinstance(attrs, str) else attrs
                )
                cache_misses += 1

            # Tag with metadata from SQLite
            entity_data["_entity_type"] = row.get("entity_type", "")
            entity_data["_entity_id"] = row.get("id", "")
            entity_data["_yaml_path"] = str(yaml_path)
            loaded.append(entity_data)

        # Route into snapshot fields
        snapshot = self._route_to_snapshot(loaded, scope)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        snapshot.load_time_ms = elapsed_ms
        snapshot.entities_loaded = len(loaded)
        snapshot.cache_hits = cache_hits
        snapshot.cache_misses = cache_misses

        return snapshot

    def _route_to_snapshot(
        self, entities: List[Dict[str, Any]], scope: ContextScope
    ) -> ProjectSnapshot:
        """Route loaded entity dicts into the appropriate ProjectSnapshot fields."""
        snapshot = ProjectSnapshot()

        for entity in entities:
            etype = entity.get("_entity_type", "")
            clean = {k: v for k, v in entity.items() if not k.startswith("_")}

            if etype == "world_settings":
                snapshot.world = clean
            elif etype == "character":
                snapshot.characters.append(clean)
            elif etype == "story_structure":
                snapshot.story_structure = clean
            elif etype == "scene":
                snapshot.scenes.append(clean)
            elif etype == "screenplay":
                snapshot.screenplays.append(clean)
            elif etype == "panel":
                snapshot.panels.append(clean)
            elif etype == "style_guide":
                snapshot.style_guides = clean
            elif etype == "creative_room" and scope.access_level == "author":
                snapshot.creative_room = clean

        return snapshot
