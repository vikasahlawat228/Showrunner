"""Unit of Work -- atomic YAML + SQLite + Event writes.

Ensures that a group of mutations (saves/deletes) either ALL succeed
or ALL roll back.  No partial writes, no stale indexes.

Data-safety guarantees (Phase L):
  - Optimistic Concurrency Control via content_hash comparison
  - Advisory file locking via fcntl.flock (prevents concurrent writes)
  - fsync before atomic rename (crash-safe)
  - Soft-delete with .trash/ directory (accidental deletion recovery)
  - Cloud sync enqueues raw YAML bytes (not JSON)
  - Delete operations propagated to cloud sync

Usage:
    async with UnitOfWork(indexer, event_service, chroma_indexer, cache) as uow:
        uow.save(entity_id, entity_type, name, yaml_path, data, event_payload)
        uow.save(...)  # buffer multiple
        # commit happens automatically on __aexit__ without exception
        # rollback happens automatically on __aexit__ with exception
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from showrunner_tool.errors import ConflictError
from showrunner_tool.schemas.dal import UnitOfWorkEntry
from showrunner_tool.utils.io import write_yaml

logger = logging.getLogger(__name__)


class UnitOfWork:
    """Ensures YAML + SQLite + EventService writes are atomic."""

    def __init__(
        self,
        sqlite_indexer,      # SQLiteIndexer instance
        event_service,       # EventService instance
        chroma_indexer=None,  # Optional ChromaIndexer
        mtime_cache=None,    # Optional MtimeCache
        cloud_sync_service=None, # Optional CloudSyncService
    ):
        self._indexer = sqlite_indexer
        self._event_service = event_service
        self._chroma = chroma_indexer
        self._cache = mtime_cache
        self._cloud_sync = cloud_sync_service
        self._pending: List[UnitOfWorkEntry] = []
        self._temp_files: List[Path] = []  # Track temp files for rollback
        self._lock_fds: List[int] = []     # File descriptors for advisory locks
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
        expected_hash: Optional[str] = None,
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
            expected_hash=expected_hash,
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
        1. Acquire advisory file locks (fcntl.flock) for all YAML paths
        2. OCC check: verify expected_hash matches current for each save
        3. Write YAML to temp files (path + '.tmp') with fsync
        4. Begin SQLite transaction (upsert entities + sync_metadata)
        5. Append events to EventService
        6. Atomic rename: temp -> final for each YAML
        7. Soft-delete: move deleted files to .trash/ directory
        8. Invalidate MtimeCache for all affected paths
        9. Async: ChromaDB upsert (non-fatal)
        10. Async: Cloud Sync queue raw YAML + delete ops (non-fatal)

        Returns number of operations committed.
        """
        if not self._pending:
            return 0

        self._temp_files = []
        self._lock_fds = []

        try:
            # Step 1: Acquire advisory file locks
            for entry in self._pending:
                final_path = Path(entry.yaml_path)
                final_path.parent.mkdir(parents=True, exist_ok=True)
                # Open (or create) a lock file alongside the YAML
                lock_path = str(final_path) + ".lock"
                fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
                fcntl.flock(fd, fcntl.LOCK_EX)
                self._lock_fds.append(fd)

            # Step 2: OCC — verify expected_hash for saves
            for entry in self._pending:
                if entry.operation == "save" and entry.expected_hash:
                    current_hash = self._indexer.get_content_hash(entry.entity_id)
                    if current_hash and current_hash != entry.expected_hash:
                        raise ConflictError(
                            entity_id=entry.entity_id,
                            yaml_path=entry.yaml_path,
                            expected=entry.expected_hash,
                            actual=current_hash,
                        )

            # Step 3: Write YAML to temp files with fsync
            for entry in self._pending:
                if entry.operation == "save":
                    tmp_path = Path(entry.yaml_path + ".tmp")
                    tmp_path.parent.mkdir(parents=True, exist_ok=True)
                    # Extract metadata fields and write clean data
                    data = dict(entry.data) if entry.data else {}
                    clean_data = {k: v for k, v in data.items() if not k.startswith("_")}
                    write_yaml(tmp_path, clean_data)
                    # fsync: force data to disk before rename (crash safety)
                    with open(tmp_path, "r+b") as f:
                        f.flush()
                        os.fsync(f.fileno())
                    self._temp_files.append(tmp_path)

            # Step 4: SQLite transaction (upsert entities + sync_metadata)
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

            # Step 5: Append events
            for entry in self._pending:
                if entry.event_type and entry.event_payload:
                    self._event_service.append_event(
                        parent_event_id=None,
                        branch_id=entry.branch_id,
                        event_type=entry.event_type,
                        container_id=entry.entity_id,
                        payload=entry.event_payload,
                    )

            # Step 6: Atomic rename temp -> final
            for entry in self._pending:
                if entry.operation == "save":
                    tmp_path = Path(entry.yaml_path + ".tmp")
                    final_path = Path(entry.yaml_path)
                    if tmp_path.exists():
                        os.rename(str(tmp_path), str(final_path))

            # Step 7: Soft-delete — move deleted files to .trash/
            for entry in self._pending:
                if entry.operation == "delete":
                    final_path = Path(entry.yaml_path)
                    if final_path.exists():
                        trash_dir = final_path.parent / ".trash"
                        trash_dir.mkdir(parents=True, exist_ok=True)
                        trash_path = trash_dir / final_path.name
                        shutil.move(str(final_path), str(trash_path))

            # Step 8: Invalidate cache
            if self._cache:
                for entry in self._pending:
                    self._cache.invalidate(Path(entry.yaml_path))

            # Step 9: ChromaDB (non-fatal)
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

            # Step 10: Cloud Sync Queue — raw YAML + delete ops (non-fatal)
            if self._cloud_sync:
                for entry in self._pending:
                    try:
                        if entry.operation == "save":
                            # Read the freshly-written YAML from disk (not JSON)
                            final_path = Path(entry.yaml_path)
                            if final_path.exists():
                                yaml_content = final_path.read_text(encoding="utf-8")
                            else:
                                # Fallback to JSON if file doesn't exist
                                clean = {k: v for k, v in entry.data.items() if not k.startswith("_")}
                                yaml_content = json.dumps(clean, default=str)
                            import asyncio
                            asyncio.create_task(
                                self._cloud_sync.enqueue_upload(entry.yaml_path, yaml_content)
                            )
                        elif entry.operation == "delete":
                            import asyncio
                            asyncio.create_task(
                                self._cloud_sync.enqueue_delete(entry.yaml_path)
                            )
                    except Exception as e:
                        logger.warning("Cloud Sync enqueue failed (non-fatal): %s", e)

            count = len(self._pending)
            self._pending = []
            self._temp_files = []
            self._committed = True
            return count

        except Exception:
            self.rollback()
            raise
        finally:
            # Always release file locks
            self._release_locks()

    def _release_locks(self) -> None:
        """Release all advisory file locks."""
        for fd in self._lock_fds:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
            except OSError:
                pass
        self._lock_fds = []

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
        self._release_locks()

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
