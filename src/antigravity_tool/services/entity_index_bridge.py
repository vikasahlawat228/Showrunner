"""Bridge between typed YAMLRepositories and the universal SQLite entity index.

Registers save/delete callbacks on each typed repo so that entity mutations
flow through to the `entities` table automatically.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Tuple

logger = logging.getLogger(__name__)

# Maps repo class name -> entity_type for the entities table
REPO_ENTITY_TYPE_MAP = {
    "CharacterRepository": "character",
    "WorldRepository": "world_settings",
    "StoryRepository": "story_structure",
    "ChapterRepository": "chapter",
    "StyleRepository": "style_guide",
    "CreativeRoomRepository": "creative_room",
}


class EntityIndexBridge:
    """Registers callbacks on typed repos to sync with SQLite entities table."""

    def __init__(self, sqlite_indexer):
        self._indexer = sqlite_indexer
        self._registered: List[str] = []

    def register(self, repo, entity_type: str = "") -> None:
        """Register save/delete callbacks on a typed repository.

        The repo must support ``subscribe_save`` and ``subscribe_delete``
        (i.e. it should be a :class:`YAMLRepository` subclass).  If the
        repo does not expose these hooks the call is silently skipped and
        a debug-level log message is emitted.

        Args:
            repo: A YAMLRepository subclass instance.
            entity_type: Override entity type.  If empty, inferred from
                the repo class name via ``REPO_ENTITY_TYPE_MAP``.
        """
        if not entity_type:
            entity_type = REPO_ENTITY_TYPE_MAP.get(
                repo.__class__.__name__, repo.__class__.__name__.lower()
            )

        # Guard: only repos with the callback API can be wired up.
        if not (hasattr(repo, "subscribe_save") and hasattr(repo, "subscribe_delete")):
            logger.debug(
                "EntityIndexBridge: %s lacks subscribe hooks, skipping",
                repo.__class__.__name__,
            )
            return

        def on_save(path: Path, entity: Any) -> None:
            try:
                data = entity.model_dump(mode="json") if hasattr(entity, "model_dump") else {}
                content = path.read_bytes() if path.exists() else b""
                content_hash = hashlib.sha256(content).hexdigest()
                now = datetime.now(timezone.utc).isoformat()

                self._indexer.upsert_entity(
                    entity_id=data.get("id", path.stem),
                    entity_type=entity_type,
                    name=data.get("name", path.stem),
                    yaml_path=str(path),
                    content_hash=content_hash,
                    attributes_json=json.dumps(data, default=str),
                    created_at=data.get("created_at", now),
                    updated_at=now,
                    parent_id=data.get("parent_id"),
                    sort_order=data.get("sort_order", 0),
                    tags=data.get("tags", []),
                )
            except Exception as e:
                logger.warning("EntityIndexBridge save callback failed for %s: %s", path, e)

        def on_delete(path: Path, identifier: str) -> None:
            try:
                self._indexer.delete_entity(identifier)
            except Exception as e:
                logger.warning("EntityIndexBridge delete callback failed for %s: %s", identifier, e)

        repo.subscribe_save(on_save)
        repo.subscribe_delete(on_delete)
        self._registered.append(f"{entity_type} ({repo.__class__.__name__})")
        logger.info("EntityIndexBridge: registered %s -> entities table", entity_type)

    def register_all(self, repos: List[Tuple[Any, str]]) -> None:
        """Register multiple repos at once.

        Args:
            repos: List of ``(repo_instance, entity_type)`` tuples.
        """
        for repo, etype in repos:
            self.register(repo, etype)

    @property
    def registered_types(self) -> List[str]:
        return list(self._registered)
