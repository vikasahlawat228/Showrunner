"""Chat session service — CRUD operations and session lifecycle (Phase J)."""

from __future__ import annotations

import logging
from typing import List, Optional

from antigravity_tool.repositories.chat_session_repo import ChatSessionRepository
from antigravity_tool.schemas.chat import (
    AutonomyLevel,
    ChatMessage,
    ChatSession,
    ChatSessionSummary,
    SessionState,
)

logger = logging.getLogger(__name__)


class ChatSessionService:
    """High-level service for chat session management.

    Lifecycle: create → active → (compacted)* → ended → (resumed → active)
    """

    def __init__(self, repo: ChatSessionRepository):
        self._repo = repo

    # ── Session lifecycle ─────────────────────────────────────────

    def create_session(
        self,
        project_id: str,
        name: str = "",
        autonomy_level: AutonomyLevel = AutonomyLevel.SUGGEST,
        context_budget: int = 100_000,
        tags: Optional[List[str]] = None,
    ) -> ChatSession:
        """Create a new active chat session."""
        session = ChatSession(
            name=name or "New Chat",
            project_id=project_id,
            state=SessionState.ACTIVE,
            autonomy_level=autonomy_level,
            context_budget=context_budget,
            tags=tags or [],
        )
        return self._repo.create_session(session)

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a session by ID."""
        return self._repo.get_session(session_id)

    def list_sessions(
        self,
        project_id: Optional[str] = None,
        state: Optional[SessionState] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ChatSessionSummary]:
        """List sessions as lightweight summaries."""
        return self._repo.list_sessions(
            project_id=project_id, state=state, limit=limit, offset=offset
        )

    def end_session(self, session_id: str) -> Optional[ChatSession]:
        """Transition a session to ENDED state."""
        session = self._repo.get_session(session_id)
        if session is None:
            return None
        session.state = SessionState.ENDED
        self._repo.update_session(session)
        return session

    def resume_session(self, session_id: str) -> Optional[ChatSession]:
        """Resume an ended session back to ACTIVE."""
        session = self._repo.get_session(session_id)
        if session is None:
            return None
        if session.state != SessionState.ENDED:
            logger.warning("Cannot resume session %s in state %s", session_id, session.state)
            return session
        session.state = SessionState.ACTIVE
        self._repo.update_session(session)
        return session

    def delete_session(self, session_id: str) -> bool:
        """Permanently delete a session and its messages."""
        return self._repo.delete_session(session_id)

    # ── Message operations ────────────────────────────────────────

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        mentioned_entity_ids: Optional[List[str]] = None,
        action_traces: Optional[List[dict]] = None,
        artifacts: Optional[List[dict]] = None,
    ) -> ChatMessage:
        """Add a message to a session."""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            mentioned_entity_ids=mentioned_entity_ids or [],
            action_traces=action_traces or [],
            artifacts=artifacts or [],
        )
        return self._repo.save_message(message)

    def get_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ChatMessage]:
        """Get messages for a session, ordered chronologically."""
        return self._repo.get_messages(session_id, limit=limit, offset=offset)

    def get_message_count(self, session_id: str) -> int:
        """Get total number of messages in a session."""
        return self._repo.get_message_count(session_id)

    # ── Token tracking ────────────────────────────────────────────

    def update_token_usage(self, session_id: str, tokens_used: int) -> None:
        """Increment token usage for a session."""
        session = self._repo.get_session(session_id)
        if session is None:
            return
        session.token_usage += tokens_used
        self._repo.update_session(session)
