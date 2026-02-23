"""Integration tests for Phase K (DAL) + Phase J (Chat) full write/read paths.

Tests the vertical stack:
  ChatOrchestrator → ChatSessionService → ChatSessionRepo → SQLite
  UnitOfWork → YAMLRepository → SQLiteIndexer → EntityIndexBridge
  ChatContextManager → ProjectMemoryService → YAML
  IntentClassifier → ChatOrchestrator routing
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import List

import pytest

from antigravity_tool.repositories.chat_session_repo import ChatSessionRepository
from antigravity_tool.services.chat_session_service import ChatSessionService
from antigravity_tool.services.chat_orchestrator import ChatOrchestrator
from antigravity_tool.services.project_memory_service import ProjectMemoryService
from antigravity_tool.services.chat_context_manager import ChatContextManager
from antigravity_tool.services.intent_classifier import IntentClassifier
from antigravity_tool.schemas.chat import (
    AutonomyLevel,
    ChatEvent,
    SessionState,
)


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def tmp_dir(tmp_path):
    """Create a temp directory with .antigravity/ subdirectory."""
    ag_dir = tmp_path / ".antigravity"
    ag_dir.mkdir()
    return tmp_path


@pytest.fixture
def chat_repo():
    """In-memory chat repo."""
    return ChatSessionRepository(":memory:")


@pytest.fixture
def session_service(chat_repo):
    return ChatSessionService(chat_repo)


@pytest.fixture
def memory_service(tmp_dir):
    return ProjectMemoryService(tmp_dir)


@pytest.fixture
def intent_classifier():
    return IntentClassifier()


@pytest.fixture
def context_manager(session_service, memory_service):
    return ChatContextManager(session_service, memory_service)


@pytest.fixture
def orchestrator(session_service, intent_classifier, context_manager):
    return ChatOrchestrator(
        session_service=session_service,
        intent_classifier=intent_classifier,
        context_manager=context_manager,
    )


async def collect_events(orchestrator, session_id, content, mentions=None) -> List[ChatEvent]:
    """Helper to collect all events from handle_message."""
    events = []
    async for event in orchestrator.handle_message(session_id, content, mentions):
        events.append(event)
    return events


# ── Integration: Full chat round-trip ─────────────────────────────


class TestChatRoundTrip:
    """End-to-end: create session → send message → get response → verify persistence."""

    @pytest.mark.asyncio
    async def test_full_round_trip(self, orchestrator, session_service):
        """Send a message and verify complete SSE stream + persistence."""
        session = session_service.create_session(project_id="proj-1", name="Test Chat")
        assert session.state == SessionState.ACTIVE

        events = await collect_events(orchestrator, session.id, "Hello, how are you?")

        # Should have action_trace + tokens + complete
        event_types = [e.event_type for e in events]
        assert "action_trace" in event_types
        assert "token" in event_types
        assert "complete" in event_types

        # Complete event should have message_id and session_id
        complete = [e for e in events if e.event_type == "complete"][0]
        assert complete.data["session_id"] == session.id
        assert "message_id" in complete.data

        # Messages should be persisted
        messages = session_service.get_messages(session.id)
        assert len(messages) == 2  # user + assistant
        assert messages[0].role == "user"
        assert messages[0].content == "Hello, how are you?"
        assert messages[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_multiple_messages_in_session(self, orchestrator, session_service):
        """Multiple messages accumulate in the same session."""
        session = session_service.create_session(project_id="proj-1")

        await collect_events(orchestrator, session.id, "First message")
        await collect_events(orchestrator, session.id, "Second message")
        await collect_events(orchestrator, session.id, "Third message")

        messages = session_service.get_messages(session.id)
        assert len(messages) == 6  # 3 user + 3 assistant

        user_msgs = [m for m in messages if m.role == "user"]
        assert [m.content for m in user_msgs] == ["First message", "Second message", "Third message"]

    @pytest.mark.asyncio
    async def test_session_lifecycle(self, session_service):
        """Create → end → resume → end lifecycle."""
        session = session_service.create_session(project_id="proj-1", name="Lifecycle Test")
        assert session.state == SessionState.ACTIVE

        ended = session_service.end_session(session.id)
        assert ended.state == SessionState.ENDED

        resumed = session_service.resume_session(session.id)
        assert resumed.state == SessionState.ACTIVE

        final = session_service.end_session(session.id)
        assert final.state == SessionState.ENDED

    @pytest.mark.asyncio
    async def test_error_on_nonexistent_session(self, orchestrator):
        """Sending to a nonexistent session yields an error event."""
        events = await collect_events(orchestrator, "nonexistent-id", "Hello")
        error_events = [e for e in events if e.event_type == "error"]
        assert len(error_events) > 0

    @pytest.mark.asyncio
    async def test_add_message_action_traces_roundtrip(self, session_service):
        """Test ChatSessionService.add_message with traces persists and loads correctly."""
        session = session_service.create_session(project_id="proj-1")
        
        trace1 = {"tool_name": "intent_classifier", "duration_ms": 150}
        trace2 = {"tool_name": "character_generator", "duration_ms": 1200}
        
        msg = session_service.add_message(
            session.id, 
            "assistant", 
            "Here is the character.", 
            action_traces=[trace1, trace2]
        )
        
        # Verify it loads back from DB properly
        loaded_msgs = session_service.get_messages(session.id)
        assert len(loaded_msgs) == 1
        assert loaded_msgs[0].content == "Here is the character."
        assert len(loaded_msgs[0].action_traces) == 2
        assert loaded_msgs[0].action_traces[0].tool_name == "intent_classifier"
        assert loaded_msgs[0].action_traces[1].duration_ms == 1200


# ── Integration: Intent routing ──────────────────────────────────


class TestIntentRouting:
    """Verify intent classifier routes correctly through the orchestrator."""

    @pytest.mark.asyncio
    async def test_chat_intent(self, orchestrator, session_service):
        """Plain chat message goes through CHAT path."""
        session = session_service.create_session(project_id="proj-1")
        events = await collect_events(orchestrator, session.id, "Tell me about the story")

        trace_events = [e for e in events if e.event_type == "action_trace"]
        assert any(e.data.get("tool_name") == "intent_classifier" for e in trace_events)

    @pytest.mark.asyncio
    async def test_create_intent_triggers_approval(self, orchestrator, session_service):
        """An UPDATE intent triggers approval_needed event."""
        session = session_service.create_session(project_id="proj-1")
        events = await collect_events(orchestrator, session.id, "Update the character description")

        event_types = [e.event_type for e in events]
        assert "approval_needed" in event_types

    @pytest.mark.asyncio
    async def test_search_intent_classification(self, orchestrator, session_service):
        """Search keywords are classified as SEARCH."""
        session = session_service.create_session(project_id="proj-1")
        events = await collect_events(orchestrator, session.id, "Find all characters with dark hair")

        trace_events = [e for e in events if e.event_type == "action_trace"]
        assert any(e.data.get("tool_name") == "intent_classifier" for e in trace_events)


# ── Integration: Plan/Execute mode ──────────────────────────────


class TestPlanExecuteIntegration:
    """Full plan → approve → execute cycle."""

    @pytest.mark.asyncio
    async def test_plan_approve_execute_cycle(self, orchestrator, session_service):
        """Complete plan cycle persists all messages."""
        session = session_service.create_session(project_id="proj-1")

        # Create plan
        plan_events = await collect_events(orchestrator, session.id, "/plan Build a new character")
        plan_tokens = [e for e in plan_events if e.event_type == "token"]
        assert len(plan_tokens) > 0

        # Approve all
        approve_events = await collect_events(orchestrator, session.id, "/approve all")
        approve_tokens = [e for e in approve_events if e.event_type == "token"]
        assert len(approve_tokens) > 0

        # Execute
        exec_events = await collect_events(orchestrator, session.id, "/execute")
        exec_types = [e.event_type for e in exec_events]
        assert "action_trace" in exec_types
        assert "complete" in exec_types

        # All messages persisted
        messages = session_service.get_messages(session.id)
        # 3 user + 3 assistant = 6
        assert len(messages) == 6

    @pytest.mark.asyncio
    async def test_execute_without_plan(self, orchestrator, session_service):
        """Execute without plan returns helpful message."""
        session = session_service.create_session(project_id="proj-1")
        events = await collect_events(orchestrator, session.id, "/execute")

        tokens = [e for e in events if e.event_type == "token"]
        full_text = "".join(e.data["text"] for e in tokens)
        assert "No active plan" in full_text


# ── Integration: Context Manager + Memory ────────────────────────


class TestContextIntegration:
    """ProjectMemory → ChatContextManager → ChatOrchestrator context flow."""

    def test_memory_flows_into_context(self, memory_service, context_manager, session_service):
        """Memories added to ProjectMemoryService appear in build_context."""
        memory_service.add_entry("tone", "Dark fantasy, gritty dialogue")
        memory_service.add_entry("world_rule", "Magic costs blood")

        session = session_service.create_session(project_id="proj-1")
        context = context_manager.build_context(session.id)

        assert "Dark fantasy" in context["system_context"]
        assert "blood" in context["system_context"]

    def test_empty_memory_produces_empty_context(self, context_manager, session_service):
        """No memories means empty system_context."""
        session = session_service.create_session(project_id="proj-1")
        context = context_manager.build_context(session.id)
        assert context["system_context"] == ""

    def test_messages_appear_in_context(self, context_manager, session_service):
        """Messages added to session appear in context messages."""
        session = session_service.create_session(project_id="proj-1")
        session_service.add_message(session.id, "user", "What's the plot?")
        session_service.add_message(session.id, "assistant", "The hero journeys north.")

        context = context_manager.build_context(session.id)
        assert len(context["messages"]) == 2
        assert context["messages"][0]["role"] == "user"
        assert context["messages"][1]["content"] == "The hero journeys north."

    @pytest.mark.asyncio
    async def test_compact_via_orchestrator(self, orchestrator, session_service):
        """Compaction via /compact command works through the stack."""
        session = session_service.create_session(project_id="proj-1")

        # Add enough messages to trigger meaningful compaction
        for i in range(15):
            session_service.add_message(session.id, "user", f"Message {i}: " + "x" * 300)
            session_service.add_message(session.id, "assistant", f"Reply {i}: " + "y" * 300)

        events = await collect_events(orchestrator, session.id, "/compact")

        tokens = [e for e in events if e.event_type == "token"]
        full_text = "".join(e.data["text"] for e in tokens)
        assert "Compacted" in full_text
        assert "tokens saved" in full_text


# ── Integration: Multi-session isolation ─────────────────────────


class TestSessionIsolation:
    """Ensure sessions don't leak state into each other."""

    @pytest.mark.asyncio
    async def test_sessions_are_isolated(self, orchestrator, session_service):
        """Messages in one session don't appear in another."""
        s1 = session_service.create_session(project_id="proj-1", name="Session A")
        s2 = session_service.create_session(project_id="proj-1", name="Session B")

        await collect_events(orchestrator, s1.id, "This is session A")
        await collect_events(orchestrator, s2.id, "This is session B")

        msgs_a = session_service.get_messages(s1.id)
        msgs_b = session_service.get_messages(s2.id)

        user_a = [m.content for m in msgs_a if m.role == "user"]
        user_b = [m.content for m in msgs_b if m.role == "user"]

        assert "This is session A" in user_a
        assert "This is session A" not in user_b
        assert "This is session B" in user_b
        assert "This is session B" not in user_a

    @pytest.mark.asyncio
    async def test_plan_state_per_session(self, orchestrator, session_service):
        """Plans are scoped to their session."""
        s1 = session_service.create_session(project_id="proj-1")
        s2 = session_service.create_session(project_id="proj-1")

        # Create plan in s1
        await collect_events(orchestrator, s1.id, "/plan Build character")

        # s2 should not have a plan
        events = await collect_events(orchestrator, s2.id, "/execute")
        tokens = [e for e in events if e.event_type == "token"]
        full_text = "".join(e.data["text"] for e in tokens)
        assert "No active plan" in full_text

    def test_session_listing_and_filtering(self, session_service):
        """List sessions with state filtering."""
        s1 = session_service.create_session(project_id="proj-1", name="Active")
        s2 = session_service.create_session(project_id="proj-1", name="To End")
        session_service.end_session(s2.id)

        all_sessions = session_service.list_sessions()
        assert len(all_sessions) == 2

        active = session_service.list_sessions(state=SessionState.ACTIVE)
        assert len(active) == 1
        assert active[0].name == "Active"

        ended = session_service.list_sessions(state=SessionState.ENDED)
        assert len(ended) == 1
        assert ended[0].name == "To End"


# ── Integration: Tool execution ──────────────────────────────────


class TestToolExecution:
    """Test tool registration and execution through chat."""

    @pytest.mark.asyncio
    async def test_registered_tool_executes(self, session_service):
        """A registered tool is called when intent matches."""
        call_log = []

        def mock_search(content, entity_ids, **kwargs):
            call_log.append({"content": content, "entity_ids": entity_ids})
            return "Found 3 characters matching your query."

        orch = ChatOrchestrator(
            session_service=session_service,
            intent_classifier=IntentClassifier(),
            tool_registry={"search": mock_search},
        )

        session = session_service.create_session(project_id="proj-1")
        events = await collect_events(orch, session.id, "Search for all characters")

        assert len(call_log) == 1
        tokens = [e for e in events if e.event_type == "token"]
        full_text = "".join(e.data["text"] for e in tokens)
        assert "Found 3 characters" in full_text

    @pytest.mark.asyncio
    async def test_tool_failure_yields_error_in_response(self, session_service):
        """A tool that raises returns error text, not a crash."""
        def failing_tool(content, entity_ids, **kwargs):
            raise ValueError("Database connection failed")

        orch = ChatOrchestrator(
            session_service=session_service,
            intent_classifier=IntentClassifier(),
            tool_registry={"search": failing_tool},
        )

        session = session_service.create_session(project_id="proj-1")
        events = await collect_events(orch, session.id, "Search for villains")

        tokens = [e for e in events if e.event_type == "token"]
        full_text = "".join(e.data["text"] for e in tokens)
        assert "failed" in full_text.lower()
