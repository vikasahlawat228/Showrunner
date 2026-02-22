"""Tests for ChatSessionRepository — SQLite CRUD for chat sessions and messages."""

from __future__ import annotations

import pytest

from antigravity_tool.repositories.chat_session_repo import ChatSessionRepository
from antigravity_tool.schemas.chat import (
    AutonomyLevel,
    ChatActionTrace,
    ChatArtifact,
    ChatMessage,
    ChatSession,
    SessionState,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def repo():
    """In-memory chat session repository."""
    return ChatSessionRepository(":memory:")


def _make_session(**overrides) -> ChatSession:
    """Create a ChatSession with sensible defaults."""
    defaults = {
        "name": "Test Chat",
        "project_id": "proj_001",
    }
    defaults.update(overrides)
    return ChatSession(**defaults)


def _make_message(session_id: str, role: str = "user", content: str = "Hello") -> ChatMessage:
    return ChatMessage(session_id=session_id, role=role, content=content)


# ═══════════════════════════════════════════════════════════════════
# Session CRUD Tests
# ═══════════════════════════════════════════════════════════════════


class TestSessionCreate:
    def test_create_returns_session(self, repo):
        session = _make_session()
        result = repo.create_session(session)
        assert result.id == session.id
        assert result.name == "Test Chat"

    def test_created_session_is_retrievable(self, repo):
        session = _make_session()
        repo.create_session(session)

        loaded = repo.get_session(session.id)
        assert loaded is not None
        assert loaded.id == session.id
        assert loaded.name == "Test Chat"
        assert loaded.state == SessionState.ACTIVE

    def test_session_preserves_autonomy_level(self, repo):
        session = _make_session(autonomy_level=AutonomyLevel.EXECUTE)
        repo.create_session(session)

        loaded = repo.get_session(session.id)
        assert loaded.autonomy_level == AutonomyLevel.EXECUTE

    def test_session_preserves_tags(self, repo):
        session = _make_session(tags=["worldbuilding", "chapter1"])
        repo.create_session(session)

        loaded = repo.get_session(session.id)
        assert loaded.tags == ["worldbuilding", "chapter1"]


class TestSessionGet:
    def test_nonexistent_session_returns_none(self, repo):
        assert repo.get_session("does_not_exist") is None


class TestSessionList:
    def test_list_empty_repo(self, repo):
        assert repo.list_sessions() == []

    def test_list_returns_summaries(self, repo):
        repo.create_session(_make_session(name="Chat A"))
        repo.create_session(_make_session(name="Chat B"))

        summaries = repo.list_sessions()
        assert len(summaries) == 2
        names = {s.name for s in summaries}
        assert names == {"Chat A", "Chat B"}

    def test_list_filters_by_project_id(self, repo):
        repo.create_session(_make_session(name="A", project_id="p1"))
        repo.create_session(_make_session(name="B", project_id="p2"))

        summaries = repo.list_sessions(project_id="p1")
        assert len(summaries) == 1
        assert summaries[0].name == "A"

    def test_list_filters_by_state(self, repo):
        s1 = _make_session(name="Active")
        repo.create_session(s1)

        s2 = _make_session(name="Ended", state=SessionState.ENDED)
        repo.create_session(s2)

        active = repo.list_sessions(state=SessionState.ACTIVE)
        assert len(active) == 1
        assert active[0].name == "Active"

    def test_list_respects_limit_offset(self, repo):
        for i in range(5):
            repo.create_session(_make_session(name=f"Chat {i}"))

        page1 = repo.list_sessions(limit=2, offset=0)
        assert len(page1) == 2

        page2 = repo.list_sessions(limit=2, offset=2)
        assert len(page2) == 2

    def test_list_includes_message_count(self, repo):
        session = _make_session()
        repo.create_session(session)
        repo.save_message(_make_message(session.id, "user", "hi"))
        repo.save_message(_make_message(session.id, "assistant", "hello"))

        summaries = repo.list_sessions()
        assert summaries[0].message_count == 2

    def test_list_includes_last_message_preview(self, repo):
        session = _make_session()
        repo.create_session(session)
        repo.save_message(_make_message(session.id, "user", "What is the world like?"))

        summaries = repo.list_sessions()
        assert "What is the world" in summaries[0].last_message_preview


class TestSessionUpdate:
    def test_update_session_fields(self, repo):
        session = _make_session()
        repo.create_session(session)

        session.name = "Renamed Chat"
        session.token_usage = 5000
        session.state = SessionState.COMPACTED
        repo.update_session(session)

        loaded = repo.get_session(session.id)
        assert loaded.name == "Renamed Chat"
        assert loaded.token_usage == 5000
        assert loaded.state == SessionState.COMPACTED


class TestSessionDelete:
    def test_delete_existing_session(self, repo):
        session = _make_session()
        repo.create_session(session)

        assert repo.delete_session(session.id) is True
        assert repo.get_session(session.id) is None

    def test_delete_nonexistent_returns_false(self, repo):
        assert repo.delete_session("ghost") is False

    def test_delete_cascades_to_messages(self, repo):
        session = _make_session()
        repo.create_session(session)
        repo.save_message(_make_message(session.id, "user", "hi"))

        repo.delete_session(session.id)
        assert repo.get_messages(session.id) == []


# ═══════════════════════════════════════════════════════════════════
# Message CRUD Tests
# ═══════════════════════════════════════════════════════════════════


class TestMessageSave:
    def test_save_and_retrieve(self, repo):
        session = _make_session()
        repo.create_session(session)

        msg = _make_message(session.id, "user", "Hello world")
        repo.save_message(msg)

        messages = repo.get_messages(session.id)
        assert len(messages) == 1
        assert messages[0].content == "Hello world"
        assert messages[0].role == "user"

    def test_messages_ordered_by_sort_order(self, repo):
        session = _make_session()
        repo.create_session(session)

        repo.save_message(_make_message(session.id, "user", "First"))
        repo.save_message(_make_message(session.id, "assistant", "Second"))
        repo.save_message(_make_message(session.id, "user", "Third"))

        messages = repo.get_messages(session.id)
        assert len(messages) == 3
        assert [m.content for m in messages] == ["First", "Second", "Third"]

    def test_message_preserves_mentioned_entity_ids(self, repo):
        session = _make_session()
        repo.create_session(session)

        msg = ChatMessage(
            session_id=session.id,
            role="user",
            content="Tell me about @zara",
            mentioned_entity_ids=["char_zara", "char_kael"],
        )
        repo.save_message(msg)

        loaded = repo.get_messages(session.id)[0]
        assert loaded.mentioned_entity_ids == ["char_zara", "char_kael"]

    def test_message_preserves_action_traces(self, repo):
        session = _make_session()
        repo.create_session(session)

        trace = ChatActionTrace(
            tool_name="scene_write",
            context_summary="Wrote scene 1",
            duration_ms=150,
        )
        msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content="Done!",
            action_traces=[trace],
        )
        repo.save_message(msg)

        loaded = repo.get_messages(session.id)[0]
        assert len(loaded.action_traces) == 1
        assert loaded.action_traces[0].tool_name == "scene_write"
        assert loaded.action_traces[0].duration_ms == 150

    def test_message_preserves_artifacts(self, repo):
        session = _make_session()
        repo.create_session(session)

        artifact = ChatArtifact(
            artifact_type="prose",
            title="Scene Draft",
            content="The sun rose over the mountain...",
        )
        msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content="Here's your draft",
            artifacts=[artifact],
        )
        repo.save_message(msg)

        loaded = repo.get_messages(session.id)[0]
        assert len(loaded.artifacts) == 1
        assert loaded.artifacts[0].artifact_type == "prose"
        assert loaded.artifacts[0].title == "Scene Draft"


class TestMessageCount:
    def test_count_empty_session(self, repo):
        session = _make_session()
        repo.create_session(session)
        assert repo.get_message_count(session.id) == 0

    def test_count_with_messages(self, repo):
        session = _make_session()
        repo.create_session(session)
        for i in range(5):
            repo.save_message(_make_message(session.id, "user", f"msg {i}"))
        assert repo.get_message_count(session.id) == 5


class TestMessagePagination:
    def test_limit_and_offset(self, repo):
        session = _make_session()
        repo.create_session(session)
        for i in range(10):
            repo.save_message(_make_message(session.id, "user", f"msg {i}"))

        page = repo.get_messages(session.id, limit=3, offset=2)
        assert len(page) == 3
        assert page[0].content == "msg 2"
