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
            # Main containers table with JSON1 support
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS containers (
                    id TEXT PRIMARY KEY,
                    container_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    yaml_path TEXT NOT NULL,
                    attributes_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
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
            
            # Indexes for performance
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_container_type ON containers(container_type)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_relationship_type ON relationships(rel_type)")

    def upsert_container(self, container_id: str, container_type: str, name: str, yaml_path: str, attributes: Dict[str, Any], created_at: str, updated_at: str) -> None:
        """Add or update a container in the index."""
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT OR REPLACE INTO containers 
                    (id, container_type, name, yaml_path, attributes_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    container_id,
                    container_type,
                    name,
                    str(yaml_path),
                    json.dumps(attributes),
                    created_at,
                    updated_at
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
        params = []
        
        if container_type:
            query += " AND container_type = ?"
            params.append(container_type)
            
        if filters:
            for key, value in filters.items():
                # Simple exact match in JSON attributes
                # Note: This is a basic implementation of JSON1 querying
                query += f" AND json_extract(attributes_json, '$.{key}') = ?"
                params.append(value)
                
        try:
            cursor = self.conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during container query: {e}")

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
