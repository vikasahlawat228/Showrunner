"""Event Sourcing layer for Git-style Undo Tree and Alternative Timelines."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from antigravity_tool.errors import PersistenceError


class EventService:
    """Manages an append-only event log for CQRS state management.
    
    Provides capabilities for branching timelines, undo functionality,
    and rebuilding application state linearly from historical diffs.
    """

    def __init__(self, db_path: str | Path = ":memory:"):
        """Initialize the event log Database."""
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.setup()

    def setup(self) -> None:
        """Create the indexing tables if they don't exist."""
        with self.conn:
            # Events table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    parent_event_id TEXT,
                    branch_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    container_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY (parent_event_id) REFERENCES events(id) ON DELETE CASCADE
                )
            """)
            
            # Branches table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS branches (
                    id TEXT PRIMARY KEY,
                    head_event_id TEXT,
                    FOREIGN KEY (head_event_id) REFERENCES events(id) ON DELETE SET NULL
                )
            """)
            
            # Indexes for querying event history
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_events_branch ON events(branch_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_events_container ON events(container_id)")
            
            # Bootstrapping the default main branch
            self.conn.execute("""
                INSERT OR IGNORE INTO branches (id, head_event_id)
                VALUES ('main', NULL)
            """)

    def append_event(self, parent_event_id: Optional[str], branch_id: str, event_type: str, container_id: str, payload: Dict[str, Any]) -> str:
        """Safely inserts a new event into the log and updates the branch's head_event_id."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        try:
            with self.conn:
                # Ensure the target branch implicitly exists
                self.conn.execute("""
                    INSERT OR IGNORE INTO branches (id, head_event_id)
                    VALUES (?, ?)
                """, (branch_id, None))

                # Infer parent from the current head of the branch if not explicitly given
                if parent_event_id is None:
                    cursor = self.conn.execute("SELECT head_event_id FROM branches WHERE id = ?", (branch_id,))
                    row = cursor.fetchone()
                    if row and row['head_event_id']:
                        parent_event_id = row['head_event_id']

                # Append the event
                self.conn.execute("""
                    INSERT INTO events 
                    (id, parent_event_id, branch_id, timestamp, event_type, container_id, payload_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (event_id, parent_event_id, branch_id, timestamp, event_type, container_id, json.dumps(payload)))
                
                # Update the branch pointer
                self.conn.execute("""
                    UPDATE branches
                    SET head_event_id = ?
                    WHERE id = ?
                """, (event_id, branch_id))
                return event_id
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during event append: {e}")

    def branch(self, source_branch_id: str, new_branch_name: str, checkout_event_id: str) -> None:
        """Creates a new row in the branches table, pointing its head at the designated historical event."""
        # Note: We take `source_branch_id` as part of the conceptual signature although `checkout_event_id` is the real hook.
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT INTO branches (id, head_event_id)
                    VALUES (?, ?)
                """, (new_branch_name, checkout_event_id))
        except sqlite3.IntegrityError:
            raise ValueError(f"Branch '{new_branch_name}' already exists.")
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during branching: {e}")

    def project_state(self, branch_id: str) -> Dict[str, dict]:
        """Reconstruct the current active state of containers for a specific branch.
        
        Extracts the head event of the branch, walks backwards to the root to build
        the linear event dependency chain, and applies the JSON payloads forward.
        """
        try:
            cursor = self.conn.execute("SELECT head_event_id FROM branches WHERE id = ?", (branch_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Branch '{branch_id}' not found.")
                
            head_event_id = row['head_event_id']
            if not head_event_id:
                return {} # Return empty projection for a fresh/empty branch
                
            # Recursive CTE to dynamically trace the exact parent-child path back to the root event
            query = """
                WITH RECURSIVE EventChain AS (
                    SELECT id, parent_event_id, event_type, container_id, payload_json, 0 as depth
                    FROM events WHERE id = ?
                    
                    UNION ALL
                    
                    SELECT e.id, e.parent_event_id, e.event_type, e.container_id, e.payload_json, ec.depth + 1
                    FROM events e
                    JOIN EventChain ec ON e.id = ec.parent_event_id
                )
                SELECT * FROM EventChain ORDER BY depth DESC;
            """
            
            cursor = self.conn.execute(query, (head_event_id,))
            rows = cursor.fetchall()
            
            projected_state: Dict[str, dict] = {}
            
            for r in rows:
                event_type = r['event_type']
                container_id = r['container_id']
                payload = json.loads(r['payload_json'])
                
                if event_type in ('CREATE', 'UPDATE'):
                    # Accumulate JSON diffs/updates
                    if container_id not in projected_state:
                         projected_state[container_id] = {}
                    projected_state[container_id].update(payload)
                elif event_type == 'DELETE':
                    # Tombstone deletion
                    if container_id in projected_state:
                        del projected_state[container_id]
                        
            return projected_state
            
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during state projection: {e}")
            
    def get_all_events(self) -> List[Dict[str, Any]]:
        """Retrieve all events sorted by timestamp for rendering the timeline."""
        try:
            cursor = self.conn.execute("""
                SELECT id, parent_event_id, branch_id, timestamp, event_type, container_id, payload_json
                FROM events
                ORDER BY timestamp ASC
            """)
            events = []
            for row in cursor.fetchall():
                evt = dict(row)
                evt['payload'] = json.loads(evt.pop('payload_json'))
                events.append(evt)
            return events
        except sqlite3.Error as e:
            raise PersistenceError(f"Database error during get_all_events: {e}")

    def close(self) -> None:
        """Close the local database connection."""
        self.conn.close()
