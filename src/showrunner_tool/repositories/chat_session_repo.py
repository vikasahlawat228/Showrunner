"""SQLite-backed repository for chat sessions and messages (Phase J).

Separate from the entity SQLite DB — chat has its own lifecycle and schema.
Tables: chat_sessions, chat_messages.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from showrunner_tool.schemas.chat import (
    ChatMessage,
    ChatSession,
    ChatSessionSummary,
    SessionState,
)

logger = logging.getLogger(__name__)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    project_id TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT 'active',
    autonomy_level INTEGER NOT NULL DEFAULT 1,
    context_budget INTEGER NOT NULL DEFAULT 100000,
    token_usage INTEGER NOT NULL DEFAULT 0,
    digest TEXT,
    compaction_count INTEGER NOT NULL DEFAULT 0,
    tags_json TEXT NOT NULL DEFAULT '[]',
    schema_version TEXT NOT NULL DEFAULT '1.0.0',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    action_traces_json TEXT NOT NULL DEFAULT '[]',
    artifacts_json TEXT NOT NULL DEFAULT '[]',
    mentioned_entity_ids_json TEXT NOT NULL DEFAULT '[]',
    approval_state TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    schema_version TEXT NOT NULL DEFAULT '1.0.0',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_sort_order ON chat_messages(session_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_sessions_state ON chat_sessions(state);
CREATE INDEX IF NOT EXISTS idx_sessions_project ON chat_sessions(project_id);
"""


class ChatSessionRepository:
    """SQLite persistence for chat sessions and messages."""

    def __init__(self, db_path: str = ":memory:"):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA_SQL)

    # ── Session CRUD ──────────────────────────────────────────────

    def create_session(self, session: ChatSession) -> ChatSession:
        """Persist a new chat session."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """INSERT INTO chat_sessions
               (id, name, project_id, state, autonomy_level, context_budget,
                token_usage, digest, compaction_count, tags_json,
                schema_version, created_at, updated_at, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session.id,
                session.name,
                session.project_id,
                session.state.value,
                session.autonomy_level.value,
                session.context_budget,
                session.token_usage,
                session.digest,
                session.compaction_count,
                json.dumps(session.tags),
                session.schema_version,
                session.created_at.isoformat() if isinstance(session.created_at, datetime) else str(session.created_at),
                now,
                session.notes,
            ),
        )
        self._conn.commit()
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Load a session by ID, or None if not found."""
        row = self._conn.execute(
            "SELECT * FROM chat_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_session(row)

    def list_sessions(
        self,
        project_id: Optional[str] = None,
        state: Optional[SessionState] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ChatSessionSummary]:
        """List sessions as lightweight summaries, newest first."""
        query = "SELECT * FROM chat_sessions WHERE 1=1"
        params: List[Any] = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if state:
            query += " AND state = ?"
            params.append(state.value)
        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self._conn.execute(query, params).fetchall()
        summaries = []
        for row in rows:
            msg_count = self._conn.execute(
                "SELECT COUNT(*) FROM chat_messages WHERE session_id = ?",
                (row["id"],),
            ).fetchone()[0]
            last_preview = ""
            last_msg = self._conn.execute(
                "SELECT content FROM chat_messages WHERE session_id = ? ORDER BY sort_order DESC LIMIT 1",
                (row["id"],),
            ).fetchone()
            if last_msg:
                content = last_msg["content"]
                last_preview = content[:100] + "..." if len(content) > 100 else content

            summaries.append(
                ChatSessionSummary(
                    id=row["id"],
                    name=row["name"],
                    state=SessionState(row["state"]),
                    message_count=msg_count,
                    context_budget=row["context_budget"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    tags=json.loads(row["tags_json"]),
                    last_message_preview=last_preview,
                )
            )
        return summaries

    def update_session(self, session: ChatSession) -> None:
        """Update a session's mutable fields."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """UPDATE chat_sessions
               SET name=?, state=?, autonomy_level=?, context_budget=?,
                   token_usage=?, digest=?, compaction_count=?, tags_json=?,
                   updated_at=?, notes=?
               WHERE id=?""",
            (
                session.name,
                session.state.value,
                session.autonomy_level.value,
                session.context_budget,
                session.token_usage,
                session.digest,
                session.compaction_count,
                json.dumps(session.tags),
                now,
                session.notes,
                session.id,
            ),
        )
        self._conn.commit()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its messages. Returns True if deleted."""
        self._conn.execute(
            "DELETE FROM chat_messages WHERE session_id = ?", (session_id,)
        )
        cursor = self._conn.execute(
            "DELETE FROM chat_sessions WHERE id = ?", (session_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    # ── Message CRUD ──────────────────────────────────────────────

    def save_message(self, message: ChatMessage) -> ChatMessage:
        """Persist a chat message, auto-assigning sort_order."""
        # Get next sort_order for this session
        row = self._conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM chat_messages WHERE session_id = ?",
            (message.session_id,),
        ).fetchone()
        sort_order = row[0] if row else 0

        self._conn.execute(
            """INSERT OR REPLACE INTO chat_messages
               (id, session_id, role, content, action_traces_json, artifacts_json,
                mentioned_entity_ids_json, approval_state, sort_order,
                schema_version, created_at, updated_at, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                message.id,
                message.session_id,
                message.role,
                message.content,
                json.dumps([t.model_dump() for t in message.action_traces]),
                json.dumps([a.model_dump() for a in message.artifacts]),
                json.dumps(message.mentioned_entity_ids),
                message.approval_state,
                sort_order,
                message.schema_version,
                message.created_at.isoformat() if isinstance(message.created_at, datetime) else str(message.created_at),
                datetime.now(timezone.utc).isoformat(),
                message.notes,
            ),
        )
        self._conn.commit()
        return message

    def get_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ChatMessage]:
        """Get messages for a session, ordered by sort_order."""
        rows = self._conn.execute(
            """SELECT * FROM chat_messages
               WHERE session_id = ?
               ORDER BY sort_order ASC
               LIMIT ? OFFSET ?""",
            (session_id, limit, offset),
        ).fetchall()
        return [self._row_to_message(row) for row in rows]

    def get_message_count(self, session_id: str) -> int:
        """Get total message count for a session."""
        row = self._conn.execute(
            "SELECT COUNT(*) FROM chat_messages WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return row[0] if row else 0

    # ── Internal ──────────────────────────────────────────────────

    def _row_to_session(self, row: sqlite3.Row) -> ChatSession:
        """Convert a SQLite row to a ChatSession model."""
        return ChatSession(
            id=row["id"],
            name=row["name"],
            project_id=row["project_id"],
            state=SessionState(row["state"]),
            autonomy_level=row["autonomy_level"],
            context_budget=row["context_budget"],
            token_usage=row["token_usage"],
            digest=row["digest"],
            compaction_count=row["compaction_count"],
            tags=json.loads(row["tags_json"]),
            schema_version=row["schema_version"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            notes=row["notes"],
        )

    def _row_to_message(self, row: sqlite3.Row) -> ChatMessage:
        """Convert a SQLite row to a ChatMessage model."""
        from showrunner_tool.schemas.chat import ChatActionTrace, ChatArtifact

        traces_raw = json.loads(row["action_traces_json"])
        traces = [ChatActionTrace(**t) for t in traces_raw]

        artifacts_raw = json.loads(row["artifacts_json"])
        artifacts = [ChatArtifact(**a) for a in artifacts_raw]

        return ChatMessage(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            action_traces=traces,
            artifacts=artifacts,
            mentioned_entity_ids=json.loads(row["mentioned_entity_ids_json"]),
            approval_state=row["approval_state"],
            schema_version=row["schema_version"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            notes=row["notes"],
        )

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
