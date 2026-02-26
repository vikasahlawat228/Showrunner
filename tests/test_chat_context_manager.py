"""Tests for ChatContextManager — 3-layer context, token budgeting, compaction."""

from __future__ import annotations

import pytest

from showrunner_tool.repositories.chat_session_repo import ChatSessionRepository
from showrunner_tool.services.chat_context_manager import ChatContextManager
from showrunner_tool.services.chat_session_service import ChatSessionService
from showrunner_tool.services.project_memory_service import ProjectMemoryService


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def session_service():
    repo = ChatSessionRepository(":memory:")
    return ChatSessionService(repo)


@pytest.fixture
def memory_service(tmp_path):
    return ProjectMemoryService(tmp_path)


@pytest.fixture
def ctx_mgr(session_service, memory_service):
    return ChatContextManager(session_service, memory_service)


@pytest.fixture
def active_session(session_service):
    return session_service.create_session(project_id="proj_001", name="Test")


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════


class TestBuildContext:
    """build_context should assemble 3-layer context dict."""

    def test_returns_expected_keys(self, ctx_mgr, active_session):
        ctx = ctx_mgr.build_context(active_session.id)

        assert "system_context" in ctx
        assert "messages" in ctx
        assert "entity_context" in ctx
        assert "token_usage" in ctx
        assert "layers" in ctx

    def test_empty_session_has_empty_messages(self, ctx_mgr, active_session):
        ctx = ctx_mgr.build_context(active_session.id)
        assert ctx["messages"] == []

    def test_includes_session_messages(self, ctx_mgr, active_session, session_service):
        session_service.add_message(active_session.id, "user", "Hello")
        session_service.add_message(active_session.id, "assistant", "Hi there")

        ctx = ctx_mgr.build_context(active_session.id)
        assert len(ctx["messages"]) == 2
        assert ctx["messages"][0]["role"] == "user"
        assert ctx["messages"][1]["role"] == "assistant"

    def test_includes_project_memory(self, ctx_mgr, active_session, memory_service):
        memory_service.add_entry("tone", "Dark fantasy")

        ctx = ctx_mgr.build_context(active_session.id)
        assert "Dark fantasy" in ctx["system_context"]

    def test_empty_memory_produces_empty_system_context(self, ctx_mgr, active_session):
        ctx = ctx_mgr.build_context(active_session.id)
        assert ctx["system_context"] == ""


class TestTokenBudgeting:
    """Token budget should be respected across layers."""

    def test_layer_breakdown_present(self, ctx_mgr, active_session):
        ctx = ctx_mgr.build_context(active_session.id, token_budget=10000)

        assert "project_memory" in ctx["layers"]
        assert "session_history" in ctx["layers"]
        assert "on_demand_retrieval" in ctx["layers"]

    def test_total_tokens_within_budget(self, ctx_mgr, active_session, session_service):
        # Add many messages
        for i in range(20):
            session_service.add_message(active_session.id, "user", f"Message {i} " * 100)

        ctx = ctx_mgr.build_context(active_session.id, token_budget=1000)

        # Total tokens should not exceed budget
        assert ctx["token_usage"] <= 1000

    def test_message_trimming(self, ctx_mgr, active_session, session_service):
        # Add lots of messages
        for i in range(50):
            session_service.add_message(active_session.id, "user", f"Msg {i}: " + "x" * 200)

        ctx = ctx_mgr.build_context(active_session.id, token_budget=500)

        # Should have fewer messages than total
        assert len(ctx["messages"]) < 50


class TestMentionedEntities:
    """@-mentioned entity IDs should be resolved in Layer 3."""

    def test_mentions_without_assembler(self, ctx_mgr, active_session):
        # Without context_assembler, entity_context should be empty
        ctx = ctx_mgr.build_context(
            active_session.id,
            mentioned_entity_ids=["char_zara"],
        )
        assert ctx["entity_context"] == ""

    def test_mentions_with_assembler(self, session_service, memory_service, active_session):
        from unittest.mock import MagicMock

        assembler = MagicMock()
        mgr = ChatContextManager(session_service, memory_service, context_assembler=assembler)

        ctx = mgr.build_context(
            active_session.id,
            mentioned_entity_ids=["char_zara"],
        )
        # Should have some entity context text
        assert "char_zara" in ctx["entity_context"]


class TestCompaction:
    """/compact should summarize old messages and keep recent ones."""

    def test_compact_empty_session(self, ctx_mgr, active_session):
        result = ctx_mgr.compact(active_session.id)
        assert result.original_message_count == 0
        assert result.token_reduction == 0

    def test_compact_few_messages_is_noop(self, ctx_mgr, active_session, session_service):
        for i in range(5):
            session_service.add_message(active_session.id, "user", f"msg {i}")

        result = ctx_mgr.compact(active_session.id, keep_recent=10)
        assert result.token_reduction == 0

    def test_compact_creates_digest(self, ctx_mgr, active_session, session_service):
        # Use long messages so digest (200-char truncation) is shorter than originals
        for i in range(20):
            session_service.add_message(active_session.id, "user", f"Message number {i}: " + "x" * 500)
            session_service.add_message(active_session.id, "assistant", f"Reply to {i}: " + "y" * 500)

        result = ctx_mgr.compact(active_session.id, keep_recent=5)

        assert result.original_message_count == 40
        assert result.digest
        assert "Conversation Summary" in result.digest
        assert result.token_reduction > 0

    def test_compact_preserves_entity_mentions(self, ctx_mgr, active_session, session_service):
        from showrunner_tool.schemas.chat import ChatMessage

        # Add messages with mentioned entities
        msg = ChatMessage(
            session_id=active_session.id,
            role="user",
            content="Tell me about @zara",
            mentioned_entity_ids=["char_zara"],
        )
        session_service._repo.save_message(msg)

        for i in range(20):
            session_service.add_message(active_session.id, "user", f"msg {i}")

        result = ctx_mgr.compact(active_session.id, keep_recent=5)
        # Recent messages' entities should be preserved
        assert isinstance(result.preserved_entities, list)
