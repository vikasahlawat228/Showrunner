"""SQLite indexing layer for Showrunner containers and DAL entities."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from antigravity_tool.errors import PersistenceError


class SQLiteIndexer:
    """Manages a local SQLite index of YAML-backed containers.

    This provides fast relational querying and Knowledge Graph traversal
    while keeping YAML as the source of truth.
    """

    def __init__(self, db_path: Optional[str | Path] = ":memory:"):
        """Initialize the SQLite index. By default, stays in memory."""
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        # WAL mode: readers don't block writers, prevents SQLITE_BUSY
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self._create_tables()

    def _create_tables(self) -> None:
        """Create the indexing tables if they don't exist."""
        with self.conn:
            # Main containers table with JSON1 support + Phase F columns
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS containers (
                    id TEXT PRIMARY KEY,
                    container_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    yaml_path TEXT NOT NULL,
                    attributes_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    parent_id TEXT,
                    sort_order INTEGER DEFAULT 0,
                    tags_json TEXT DEFAULT '[]',
                    model_preference TEXT
                )
            """)

            # Simple relationship table for graph traversal
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    rel_type TEXT NOT NULL,
                    metadata_json TEXT,
                    PRIMARY KEY (source_id, target_id, rel_type),
                    FOREIGN KEY (source_id) REFERENCES containers(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_id) REFERENCES containers(id) ON DELETE CASCADE
                )
            """)

            # Phase K: Entities table — normalised DAL index
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    container_type TEXT,
                    name TEXT NOT NULL,
                    yaml_path TEXT NOT NULL UNIQUE,
                    content_hash TEXT NOT NULL,
                    attributes_json TEXT,
                    parent_id TEXT,
                    sort_order INTEGER DEFAULT 0,
                    tags_json TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_deleted INTEGER DEFAULT 0,
                    deleted_at TEXT
                )
            """)

            # Phase L: Sync failures dead-letter queue
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_failures (
                    yaml_path TEXT PRIMARY KEY,
                    operation TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    attempt_count INTEGER DEFAULT 0,
                    first_failed_at TEXT NOT NULL,
                    last_failed_at TEXT NOT NULL
                )
            """)

            # Phase K/L: Sync metadata for incremental sync + cloud mapping
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    yaml_path TEXT PRIMARY KEY,
                    entity_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    mtime REAL NOT NULL,
                    indexed_at TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    drive_file_id TEXT,
                    sync_status TEXT DEFAULT 'idle'
                )
            """)

        # Run migration for existing databases that lack Phase F columns before creating indexes
        self._migrate_phase_f_columns()

        with self.conn:
            # Indexes for performance
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_container_type ON containers(container_type)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_relationship_type ON relationships(rel_type)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_parent_id ON containers(parent_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sort_order ON containers(sort_order)")

            # Phase K: Entity indexes
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_container_type ON entities(container_type)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_parent ON entities(parent_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_yaml_path ON entities(yaml_path)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sync_mtime ON sync_metadata(mtime)")

    def _migrate_phase_f_columns(self) -> None:
        """Add Phase F columns to existing databases via ALTER TABLE."""
        new_columns = [
            ("parent_id", "TEXT"),
            ("sort_order", "INTEGER DEFAULT 0"),
            ("tags_json", "TEXT DEFAULT '[]'"),
            ("model_preference", "TEXT"),
        ]
        for col_name, col_type in new_columns:
            try:
                self.conn.execute(
                    f"ALTER TABLE containers ADD COLUMN {col_name} {col_type}"
                )
            except sqlite3.OperationalError:
                pass
        
        # Add Cloud Sync columns to sync_metadata if missing
        for col_name, col_type in [("drive_file_id", "TEXT"), ("sync_status", "TEXT DEFAULT 'idle'")]:
            try:
                self.conn.execute(
                    f"ALTER TABLE sync_metadata ADD COLUMN {col_name} {col_type}"
                )
            except sqlite3.OperationalError:
                pass

        # Add soft-delete columns to entities if missing
        for col_name, col_type in [("is_deleted", "INTEGER DEFAULT 0"), ("deleted_at", "TEXT")]:
            try:
                self.conn.execute(
                    f"ALTER TABLE entities ADD COLUMN {col_name} {col_type}"
                )
            except sqlite3.OperationalError:
                pass

    def upsert_container(
        self,
        container_id: str,
        container_type: str,
        name: str,
        yaml_path: str,
        attributes: Dict[str, Any],
        created_at: str,
        updated_at: str,
        parent_id: Optional[str] = None,
        sort_order: int = 0,
        tags: Optional[List[str]] = None,
        model_preference: Optional[str] = None,
    ) -> None:
        """Add or update a container in the index."""
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT OR REPLACE INTO containers
                    (id, container_type, name, yaml_path, attributes_json,
                     created_at, updated_at, parent_id, sort_order, tags_json,
                     model_preference)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    container_id,
                    container_type,
                    name,
                    str(yaml_path),
                    json.dumps(attributes),
                    created_at,
                    updated_at,
                    parent_id,
                    sort_order,
                    json.dumps(tags or []),
                    model_preference,
                ))
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during container upsert: {e}")

    def delete_container(self, container_id: str) -> None:
        """Remove a container from the index."""
        try:
            with self.conn:
                self.conn.execute("DELETE FROM containers WHERE id = ?", (container_id,))
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during container deletion: {e}")

    def query_containers(self, container_type: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query containers with simple filters using JSON1 syntax."""
        query = "SELECT * FROM containers WHERE 1=1"
        params: list = []

        if container_type:
            query += " AND container_type = ?"
            params.append(container_type)

        if filters:
            for key, value in filters.items():
                # Direct column matches for Phase F fields
                if key in ("id", "parent_id", "model_preference"):
                    query += f" AND {key} = ?"
                    params.append(value)
                elif key == "yaml_path":
                    query += " AND yaml_path = ?"
                    params.append(value)
                else:
                    # JSON attribute match
                    query += f" AND json_extract(attributes_json, '$.{key}') = ?"
                    params.append(value)

        try:
            cursor = self.conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during container query: {e}")

    def get_children(self, parent_id: str) -> List[Dict[str, Any]]:
        """Get all containers with the given parent_id, ordered by sort_order."""
        try:
            cursor = self.conn.execute(
                "SELECT * FROM containers WHERE parent_id = ? ORDER BY sort_order ASC",
                (parent_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during get_children: {e}")

    def get_roots(self, container_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get containers with no parent (top-level structural nodes)."""
        query = "SELECT * FROM containers WHERE parent_id IS NULL"
        params: list = []
        if container_types:
            placeholders = ",".join("?" for _ in container_types)
            query += f" AND container_type IN ({placeholders})"
            params.extend(container_types)
        query += " ORDER BY sort_order ASC"
        try:
            cursor = self.conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during get_roots: {e}")

    def add_relationship(self, source_id: str, target_id: str, rel_type: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Link two containers in the Knowledge Graph."""
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT OR REPLACE INTO relationships (source_id, target_id, rel_type, metadata_json)
                    VALUES (?, ?, ?, ?)
                """, (source_id, target_id, rel_type, json.dumps(metadata) if metadata else None))
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during relationship creation: {e}")

    def get_related(self, container_id: str, rel_type: Optional[str] = None, direction: str = "out") -> List[Dict[str, Any]]:
        """Get related containers for a given node."""
        if direction == "out":
            query = "SELECT c.* FROM containers c JOIN relationships r ON c.id = r.target_id WHERE r.source_id = ?"
        else:
            query = "SELECT c.* FROM containers c JOIN relationships r ON c.id = r.source_id WHERE r.target_id = ?"

        params = [container_id]
        if rel_type:
            query += " AND r.rel_type = ?"
            params.append(rel_type)

        try:
            cursor = self.conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during related containers query: {e}")

    def get_all_relationships(self) -> List[Dict[str, Any]]:
        """Get all relationships in the index for graph visualization."""
        try:
            cursor = self.conn.execute("SELECT * FROM relationships")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during get_all_relationships query: {e}")

    # ── Phase K: Entity CRUD ──────────────────────────────────────

    def upsert_entity(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        yaml_path: str,
        content_hash: str,
        attributes_json: str,
        created_at: str,
        updated_at: str,
        container_type: Optional[str] = None,
        parent_id: Optional[str] = None,
        sort_order: int = 0,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Add or update an entity in the entities index."""
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT OR REPLACE INTO entities
                    (id, entity_type, container_type, name, yaml_path, content_hash,
                     attributes_json, parent_id, sort_order, tags_json,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    entity_type,
                    container_type,
                    name,
                    str(yaml_path),
                    content_hash,
                    attributes_json,
                    parent_id,
                    sort_order,
                    json.dumps(tags or []),
                    created_at,
                    updated_at,
                ))
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during entity upsert: {e}")

    def delete_entity(self, entity_id: str) -> None:
        """Soft-delete: mark entity as deleted instead of removing it."""
        try:
            now = datetime.now(timezone.utc).isoformat()
            with self.conn:
                self.conn.execute(
                    "UPDATE entities SET is_deleted = 1, deleted_at = ? WHERE id = ?",
                    (now, entity_id),
                )
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during entity soft-delete: {e}")

    def restore_entity(self, entity_id: str) -> None:
        """Restore a soft-deleted entity."""
        try:
            with self.conn:
                self.conn.execute(
                    "UPDATE entities SET is_deleted = 0, deleted_at = NULL WHERE id = ?",
                    (entity_id,),
                )
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during entity restore: {e}")

    def purge_entity(self, entity_id: str) -> None:
        """Permanently delete an entity (no recovery)."""
        try:
            with self.conn:
                self.conn.execute("DELETE FROM entities WHERE id = ?", (entity_id,))
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during entity purge: {e}")

    def query_deleted_entities(self) -> List[Dict[str, Any]]:
        """Return all soft-deleted entities for the Trash Manager UI."""
        try:
            cursor = self.conn.execute(
                "SELECT * FROM entities WHERE is_deleted = 1 ORDER BY deleted_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error querying deleted entities: {e}")

    def get_content_hash(self, entity_id: str) -> Optional[str]:
        """Return the current content_hash for an entity, used for OCC checks."""
        try:
            cursor = self.conn.execute(
                "SELECT content_hash FROM entities WHERE id = ?", (entity_id,)
            )
            row = cursor.fetchone()
            return row["content_hash"] if row else None
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error fetching content hash: {e}")

    def record_sync_failure(
        self, yaml_path: str, operation: str, error_message: str, attempt_count: int
    ) -> None:
        """Record a sync failure in the dead-letter queue."""
        try:
            now = datetime.now(timezone.utc).isoformat()
            with self.conn:
                self.conn.execute("""
                    INSERT INTO sync_failures (yaml_path, operation, error_message,
                                              attempt_count, first_failed_at, last_failed_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(yaml_path) DO UPDATE SET
                        error_message = excluded.error_message,
                        attempt_count = excluded.attempt_count,
                        last_failed_at = excluded.last_failed_at
                """, (yaml_path, operation, error_message, attempt_count, now, now))
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error recording sync failure: {e}")

    def query_entities(
        self,
        entity_type: Optional[str] = None,
        container_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query entities with optional type filters and JSON attribute filters."""
        query = "SELECT * FROM entities WHERE is_deleted = 0"
        params: list = []

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)

        if container_type:
            query += " AND container_type = ?"
            params.append(container_type)

        if filters:
            for key, value in filters.items():
                if key in ("id", "parent_id", "yaml_path", "content_hash"):
                    query += f" AND {key} = ?"
                    params.append(value)
                else:
                    # JSON attribute match
                    query += f" AND json_extract(attributes_json, '$.{key}') = ?"
                    params.append(value)

        try:
            cursor = self.conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during entity query: {e}")

    def get_entity_by_path(self, yaml_path: str) -> Optional[Dict[str, Any]]:
        """O(1) lookup of an entity by its YAML file path (UNIQUE index)."""
        try:
            cursor = self.conn.execute(
                "SELECT * FROM entities WHERE yaml_path = ?", (str(yaml_path),)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during entity path lookup: {e}")

    # ── Phase K: Sync Metadata CRUD ────────────────────────────────

    def upsert_sync_metadata(
        self,
        yaml_path: str,
        entity_id: str,
        entity_type: str,
        content_hash: str,
        mtime: float,
        file_size: int,
    ) -> None:
        """Add or update sync metadata for a YAML file."""
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT OR REPLACE INTO sync_metadata
                    (yaml_path, entity_id, entity_type, content_hash, mtime, indexed_at, file_size, drive_file_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(yaml_path),
                    entity_id,
                    entity_type,
                    content_hash,
                    mtime,
                    datetime.now(timezone.utc).isoformat(),
                    file_size,
                    None, # Initial upsert from UoW doesn't have Drive ID yet
                ))
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during sync metadata upsert: {e}")

    def get_sync_metadata(self, yaml_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sync metadata. Returns one entry if yaml_path given, all if None."""
        try:
            if yaml_path:
                cursor = self.conn.execute(
                    "SELECT * FROM sync_metadata WHERE yaml_path = ?",
                    (str(yaml_path),),
                )
            else:
                cursor = self.conn.execute("SELECT * FROM sync_metadata")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during sync metadata query: {e}")

    def delete_sync_metadata(self, yaml_path: str) -> None:
        """Remove sync metadata for a YAML file."""
        try:
            with self.conn:
                self.conn.execute(
                    "DELETE FROM sync_metadata WHERE yaml_path = ?",
                    (str(yaml_path),),
                )
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during sync metadata deletion: {e}")

    def update_sync_drive_id(self, yaml_path: str, drive_file_id: str) -> None:
        """Update the cloud mapping for a YAML file."""
        try:
            with self.conn:
                self.conn.execute(
                    "UPDATE sync_metadata SET drive_file_id = ?, sync_status = 'idle' WHERE yaml_path = ?",
                    (drive_file_id, str(yaml_path)),
                )
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during sync metadata update: {e}")

    # ── Phase K: Aggregation & Migration ───────────────────────────

    def get_entity_count_by_type(self) -> Dict[str, int]:
        """Return a mapping of entity_type → count from the entities table."""
        try:
            cursor = self.conn.execute(
                "SELECT entity_type, COUNT(*) as cnt FROM entities GROUP BY entity_type"
            )
            return {row["entity_type"]: row["cnt"] for row in cursor.fetchall()}
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during entity count: {e}")

    def migrate_containers_to_entities(self) -> int:
        """Copy data from the containers table into the entities table.

        This is a one-time migration helper for moving from the legacy
        containers index to the normalised entities index.  Existing
        entities with the same id are overwritten (INSERT OR REPLACE).

        Returns the number of rows migrated.
        """
        try:
            cursor = self.conn.execute("SELECT * FROM containers")
            rows = cursor.fetchall()
            count = 0
            for row in rows:
                row_dict = dict(row)
                self.upsert_entity(
                    entity_id=row_dict["id"],
                    entity_type=row_dict["container_type"],
                    name=row_dict["name"],
                    yaml_path=row_dict["yaml_path"],
                    content_hash="migrated",  # No hash in legacy table
                    attributes_json=row_dict.get("attributes_json", "{}"),
                    created_at=row_dict["created_at"],
                    updated_at=row_dict["updated_at"],
                    container_type=row_dict["container_type"],
                    parent_id=row_dict.get("parent_id"),
                    sort_order=row_dict.get("sort_order", 0),
                    tags=json.loads(row_dict.get("tags_json", "[]")),
                )
                count += 1
            return count
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during container→entity migration: {e}")

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
