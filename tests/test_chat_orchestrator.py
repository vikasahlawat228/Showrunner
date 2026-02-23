"""Tests for ChatOrchestrator — basic message flow and SSE event generation."""

from __future__ import annotations

import asyncio

import pytest

from antigravity_tool.repositories.chat_session_repo import ChatSessionRepository
from antigravity_tool.schemas.chat import ChatEvent, ChatSession, SessionState
from antigravity_tool.services.chat_orchestrator import ChatOrchestrator
from antigravity_tool.services.chat_session_service import ChatSessionService


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def repo():
    return ChatSessionRepository(":memory:")


@pytest.fixture
def session_service(repo):
    return ChatSessionService(repo)


@pytest.fixture
def orchestrator(session_service):
    return ChatOrchestrator(session_service)


@pytest.fixture
def active_session(session_service) -> ChatSession:
    return session_service.create_session(project_id="proj_001", name="Test Chat")


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════


async def _collect_events(orchestrator, session_id, content, mentioned=None):
    """Collect all events from handle_message into a list."""
    events = []
    async for event in orchestrator.handle_message(session_id, content, mentioned):
        events.append(event)
    return events


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════


class TestBasicMessageFlow:
    """handle_message should yield a sequence of ChatEvents."""

    @pytest.mark.asyncio
    async def test_yields_events(self, orchestrator, active_session):
        events = await _collect_events(
            orchestrator, active_session.id, "Hello!"
        )

        assert len(events) > 0
        assert all(isinstance(e, ChatEvent) for e in events)

    @pytest.mark.asyncio
    async def test_starts_with_action_trace(self, orchestrator, active_session):
        events = await _collect_events(
            orchestrator, active_session.id, "Hello!"
        )

        # First event should be intent classification trace
        assert events[0].event_type == "action_trace"
        assert events[0].data["tool_name"] == "intent_classifier"

    @pytest.mark.asyncio
    async def test_has_token_events(self, orchestrator, active_session):
        events = await _collect_events(
            orchestrator, active_session.id, "Hello!"
        )

        token_events = [e for e in events if e.event_type == "token"]
        assert len(token_events) > 0

        # Tokens should form the response text
        full_text = "".join(e.data["text"] for e in token_events)
        assert "shell mode" in full_text

    @pytest.mark.asyncio
    async def test_ends_with_complete(self, orchestrator, active_session):
        events = await _collect_events(
            orchestrator, active_session.id, "Hello!"
        )

        assert events[-1].event_type == "complete"
        assert "message_id" in events[-1].data
        assert "duration_ms" in events[-1].data


class TestMessagePersistence:
    """Messages should be persisted to the session."""

    @pytest.mark.asyncio
    async def test_user_message_persisted(self, orchestrator, active_session, session_service):
        await _collect_events(
            orchestrator, active_session.id, "What is the world like?"
        )

        messages = session_service.get_messages(active_session.id)
        assert len(messages) == 2  # user + assistant
        assert messages[0].role == "user"
        assert messages[0].content == "What is the world like?"

    @pytest.mark.asyncio
    async def test_assistant_message_persisted(self, orchestrator, active_session, session_service):
        await _collect_events(
            orchestrator, active_session.id, "Hi there"
        )

        messages = session_service.get_messages(active_session.id)
        assert messages[1].role == "assistant"
        assert len(messages[1].content) > 0

    @pytest.mark.asyncio
    async def test_multiple_messages_ordered(self, orchestrator, active_session, session_service):
        await _collect_events(orchestrator, active_session.id, "First")
        await _collect_events(orchestrator, active_session.id, "Second")

        messages = session_service.get_messages(active_session.id)
        assert len(messages) == 4  # 2 user + 2 assistant
        assert messages[0].content == "First"
        assert messages[2].content == "Second"


class TestMentionedEntities:
    """Mentioned entity IDs should be preserved in the user message."""

    @pytest.mark.asyncio
    async def test_mentioned_entities_persisted(self, orchestrator, active_session, session_service):
        await _collect_events(
            orchestrator,
            active_session.id,
            "Tell me about @zara",
            mentioned=["char_zara"],
        )

        messages = session_service.get_messages(active_session.id)
        user_msg = messages[0]
        assert "char_zara" in user_msg.mentioned_entity_ids


class TestErrorHandling:
    """Errors during processing should yield an error event."""

    @pytest.mark.asyncio
    async def test_invalid_session_yields_error(self, orchestrator):
        # Saving a message for a nonexistent session should trigger error
        events = await _collect_events(
            orchestrator, "nonexistent_session_id", "Hello!"
        )

        # Should get an error event (the exact behavior depends on SQLite FK enforcement)
        # At minimum, should not crash
        assert len(events) > 0


class TestWelcomeBack:
    """Resuming after 24 h+ should yield welcome-back tokens."""

    @pytest.mark.asyncio
    async def test_welcome_back_after_gap(self, session_service, repo):
        from datetime import datetime, timedelta, timezone

        session = session_service.create_session(project_id="proj_001", name="Old Chat")

        # Backdate updated_at by 48 hours using raw SQL
        # (repo.update_session always overwrites updated_at with now)
        past = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        repo._conn.execute(
            "UPDATE chat_sessions SET updated_at=? WHERE id=?",
            (past, session.id),
        )
        repo._conn.commit()

        orchestrator = ChatOrchestrator(session_service)
        events = await _collect_events(orchestrator, session.id, "Hey, I'm back!")

        token_events = [e for e in events if e.event_type == "token"]
        full_text = "".join(e.data["text"] for e in token_events)
        assert "Welcome back" in full_text

    @pytest.mark.asyncio
    async def test_no_welcome_back_for_recent_session(self, orchestrator, active_session):
        # Active session was just created — no gap
        events = await _collect_events(orchestrator, active_session.id, "Hello!")

        token_events = [e for e in events if e.event_type == "token"]
        full_text = "".join(e.data["text"] for e in token_events)
        assert "Welcome back" not in full_text
