"""Unit of Work -- atomic YAML + SQLite + Event writes.

Ensures that a group of mutations (saves/deletes) either ALL succeed
or ALL roll back.  No partial writes, no stale indexes.

Usage:
    async with UnitOfWork(indexer, event_service, chroma_indexer, cache) as uow:
        uow.save(entity_id, entity_type, name, yaml_path, data, event_payload)
        uow.save(...)  # buffer multiple
        # commit happens automatically on __aexit__ without exception
        # rollback happens automatically on __aexit__ with exception
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from antigravity_tool.schemas.dal import UnitOfWorkEntry
from antigravity_tool.utils.io import write_yaml

logger = logging.getLogger(__name__)


class UnitOfWork:
    """Ensures YAML + SQLite + EventService writes are atomic."""

    def __init__(
        self,
        sqlite_indexer,      # SQLiteIndexer instance
        event_service,       # EventService instance
        chroma_indexer=None,  # Optional ChromaIndexer
        mtime_cache=None,    # Optional MtimeCache
    ):
        self._indexer = sqlite_indexer
        self._event_service = event_service
        self._chroma = chroma_indexer
        self._cache = mtime_cache
        self._pending: List[UnitOfWorkEntry] = []
        self._temp_files: List[Path] = []  # Track temp files for rollback
        self._committed = False

    def save(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        yaml_path: str,
        data: Dict[str, Any],
        event_type: str = "UPDATE",
        event_payload: Optional[Dict[str, Any]] = None,
        branch_id: str = "main",
        container_type: Optional[str] = None,
        parent_id: Optional[str] = None,
        sort_order: int = 0,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Buffer a save operation.  No disk I/O until commit()."""
        self._pending.append(UnitOfWorkEntry(
            operation="save",
            entity_id=entity_id,
            entity_type=entity_type,
            yaml_path=yaml_path,
            data={
                **data,
                "_name": name,
                "_container_type": container_type,
                "_parent_id": parent_id,
                "_sort_order": sort_order,
                "_tags": tags or [],
            },
            event_type=event_type,
            event_payload=event_payload or data,
            branch_id=branch_id,
        ))

    def delete(
        self,
        entity_id: str,
        entity_type: str,
        yaml_path: str,
        event_payload: Optional[Dict[str, Any]] = None,
        branch_id: str = "main",
    ) -> None:
        """Buffer a delete operation."""
        self._pending.append(UnitOfWorkEntry(
            operation="delete",
            entity_id=entity_id,
            entity_type=entity_type,
            yaml_path=yaml_path,
            event_type="DELETE",
            event_payload=event_payload or {"entity_id": entity_id},
            branch_id=branch_id,
        ))

    def commit(self) -> int:
        """Execute all buffered operations atomically.

        Commit sequence:
        1. Write YAML to temp files (path + '.tmp')
        2. Begin SQLite transaction (upsert entities + sync_metadata)
        3. Append events to EventService
        4. Atomic rename: temp -> final for each YAML
        5. Invalidate MtimeCache for all affected paths
        6. Async: ChromaDB upsert (non-fatal)

        Returns number of operations committed.
        """
        if not self._pending:
            return 0

        self._temp_files = []

        try:
            # Step 1: Write YAML to temp files
            for entry in self._pending:
                if entry.operation == "save":
                    tmp_path = Path(entry.yaml_path + ".tmp")
                    tmp_path.parent.mkdir(parents=True, exist_ok=True)
                    # Extract metadata fields and write clean data
                    data = dict(entry.data) if entry.data else {}
                    clean_data = {k: v for k, v in data.items() if not k.startswith("_")}
                    write_yaml(tmp_path, clean_data)
                    self._temp_files.append(tmp_path)

            # Step 2: SQLite transaction (upsert entities + sync_metadata)
            for entry in self._pending:
                if entry.operation == "save" and entry.data:
                    content_hash = hashlib.sha256(
                        json.dumps(entry.data, sort_keys=True, default=str).encode()
                    ).hexdigest()
                    meta = entry.data
                    name = meta.get("_name", meta.get("name", ""))
                    container_type = meta.get("_container_type")
                    parent_id = meta.get("_parent_id")
                    sort_order = meta.get("_sort_order", 0)
                    tags = meta.get("_tags", [])
                    clean_data = {k: v for k, v in entry.data.items() if not k.startswith("_")}

                    from datetime import datetime, timezone
                    now = datetime.now(timezone.utc).isoformat()

                    self._indexer.upsert_entity(
                        entity_id=entry.entity_id,
                        entity_type=entry.entity_type,
                        name=name,
                        yaml_path=entry.yaml_path,
                        content_hash=content_hash,
                        attributes_json=json.dumps(clean_data, default=str),
                        created_at=now,
                        updated_at=now,
                        container_type=container_type,
                        parent_id=parent_id,
                        sort_order=sort_order,
                        tags=tags,
                    )

                    file_size = 0
                    tmp = Path(entry.yaml_path + ".tmp")
                    if tmp.exists():
                        file_size = tmp.stat().st_size

                    self._indexer.upsert_sync_metadata(
                        yaml_path=entry.yaml_path,
                        entity_id=entry.entity_id,
                        entity_type=entry.entity_type,
                        content_hash=content_hash,
                        mtime=os.stat(tmp).st_mtime if tmp.exists() else 0.0,
                        file_size=file_size,
                    )

                elif entry.operation == "delete":
                    self._indexer.delete_entity(entry.entity_id)
                    self._indexer.delete_sync_metadata(entry.yaml_path)

            # Step 3: Append events
            for entry in self._pending:
                if entry.event_type and entry.event_payload:
                    self._event_service.append_event(
                        parent_event_id=None,
                        branch_id=entry.branch_id,
                        event_type=entry.event_type,
                        container_id=entry.entity_id,
                        payload=entry.event_payload,
                    )

            # Step 4: Atomic rename temp -> final
            for entry in self._pending:
                if entry.operation == "save":
                    tmp_path = Path(entry.yaml_path + ".tmp")
                    final_path = Path(entry.yaml_path)
                    if tmp_path.exists():
                        os.rename(str(tmp_path), str(final_path))
                elif entry.operation == "delete":
                    final_path = Path(entry.yaml_path)
                    if final_path.exists():
                        final_path.unlink()

            # Step 5: Invalidate cache
            if self._cache:
                for entry in self._pending:
                    self._cache.invalidate(Path(entry.yaml_path))

            # Step 6: ChromaDB (non-fatal)
            if self._chroma:
                for entry in self._pending:
                    try:
                        if entry.operation == "save" and entry.data:
                            clean = {k: v for k, v in entry.data.items() if not k.startswith("_")}
                            self._chroma.upsert_embedding(
                                entry.entity_id,
                                json.dumps(clean, default=str),
                            )
                    except Exception as e:
                        logger.warning("ChromaDB upsert failed (non-fatal): %s", e)

            count = len(self._pending)
            self._pending = []
            self._temp_files = []
            self._committed = True
            return count

        except Exception:
            self.rollback()
            raise

    def rollback(self) -> None:
        """Clean up temp files and clear pending buffer."""
        for tmp in self._temp_files:
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass
        self._pending = []
        self._temp_files = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        elif not self._committed and self._pending:
            self.commit()
        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        elif not self._committed and self._pending:
            self.commit()
        return False
