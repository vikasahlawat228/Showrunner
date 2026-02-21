"""SQLite indexing layer for Showrunner containers."""

from __future__ import annotations

import json
import sqlite3
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

        # Run migration for existing databases that lack Phase F columns before creating indexes
        self._migrate_phase_f_columns()

        with self.conn:
            # Indexes for performance
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_container_type ON containers(container_type)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_relationship_type ON relationships(rel_type)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_parent_id ON containers(parent_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sort_order ON containers(sort_order)")

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
                # Column already exists — safe to ignore
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

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
