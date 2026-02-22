"""Tests for ChatOrchestrator plan/execute mode and /commands (J-6, J-7)."""

from __future__ import annotations

import pytest

from antigravity_tool.repositories.chat_session_repo import ChatSessionRepository
from antigravity_tool.schemas.chat import ChatEvent, ChatSession
from antigravity_tool.services.chat_orchestrator import ChatOrchestrator
from antigravity_tool.services.chat_session_service import ChatSessionService


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def session_service():
    repo = ChatSessionRepository(":memory:")
    return ChatSessionService(repo)


@pytest.fixture
def orchestrator(session_service):
    return ChatOrchestrator(session_service)


@pytest.fixture
def active_session(session_service) -> ChatSession:
    return session_service.create_session(project_id="proj_001", name="Plan Test")


async def _collect_events(orchestrator, session_id, content):
    events = []
    async for event in orchestrator.handle_message(session_id, content):
        events.append(event)
    return events


# ═══════════════════════════════════════════════════════════════════
# /plan Tests
# ═══════════════════════════════════════════════════════════════════


class TestPlanCommand:
    @pytest.mark.asyncio
    async def test_plan_creates_steps(self, orchestrator, active_session):
        events = await _collect_events(
            orchestrator, active_session.id, "/plan Create a new character arc"
        )

        # Should have action_trace, tokens, and complete
        trace_events = [e for e in events if e.event_type == "action_trace"]
        assert any(e.data.get("tool_name") == "plan_generator" for e in trace_events)

        complete = [e for e in events if e.event_type == "complete"]
        assert len(complete) == 1

    @pytest.mark.asyncio
    async def test_plan_without_goal_shows_usage(self, orchestrator, active_session):
        events = await _collect_events(
            orchestrator, active_session.id, "/plan"
        )

        token_events = [e for e in events if e.event_type == "token"]
        text = "".join(e.data.get("text", "") for e in token_events)
        assert "Usage" in text

    @pytest.mark.asyncio
    async def test_plan_stored_in_session(self, orchestrator, active_session):
        await _collect_events(
            orchestrator, active_session.id, "/plan Build the world"
        )

        assert active_session.id in orchestrator._plans
        assert len(orchestrator._plans[active_session.id]) == 4


# ═══════════════════════════════════════════════════════════════════
# /approve Tests
# ═══════════════════════════════════════════════════════════════════


class TestApproveCommand:
    @pytest.mark.asyncio
    async def test_approve_specific_steps(self, orchestrator, active_session):
        await _collect_events(orchestrator, active_session.id, "/plan Test goal")
        events = await _collect_events(
            orchestrator, active_session.id, "/approve 1, 3"
        )

        plan = orchestrator._plans[active_session.id]
        assert plan[0]["status"] == "approved"
        assert plan[1]["status"] == "pending"
        assert plan[2]["status"] == "approved"

    @pytest.mark.asyncio
    async def test_approve_all(self, orchestrator, active_session):
        await _collect_events(orchestrator, active_session.id, "/plan Test goal")
        await _collect_events(orchestrator, active_session.id, "/approve all")

        plan = orchestrator._plans[active_session.id]
        assert all(s["status"] == "approved" for s in plan)

    @pytest.mark.asyncio
    async def test_approve_without_plan(self, orchestrator, active_session):
        events = await _collect_events(
            orchestrator, active_session.id, "/approve 1"
        )

        text = "".join(e.data.get("text", "") for e in events if e.event_type == "token")
        assert "No active plan" in text


# ═══════════════════════════════════════════════════════════════════
# /execute Tests
# ═══════════════════════════════════════════════════════════════════


class TestExecuteCommand:
    @pytest.mark.asyncio
    async def test_execute_runs_approved_steps(self, orchestrator, active_session):
        await _collect_events(orchestrator, active_session.id, "/plan Test goal")
        await _collect_events(orchestrator, active_session.id, "/approve all")
        events = await _collect_events(orchestrator, active_session.id, "/execute")

        # Should have background_update events for each step
        bg_events = [e for e in events if e.event_type == "background_update"]
        assert len(bg_events) == 4

        # Plan should be cleared after execution
        assert active_session.id not in orchestrator._plans

    @pytest.mark.asyncio
    async def test_execute_without_approved_steps(self, orchestrator, active_session):
        await _collect_events(orchestrator, active_session.id, "/plan Test goal")
        events = await _collect_events(orchestrator, active_session.id, "/execute")

        text = "".join(e.data.get("text", "") for e in events if e.event_type == "token")
        assert "No approved steps" in text

    @pytest.mark.asyncio
    async def test_execute_without_plan(self, orchestrator, active_session):
        events = await _collect_events(orchestrator, active_session.id, "/execute")

        text = "".join(e.data.get("text", "") for e in events if e.event_type == "token")
        assert "No active plan" in text


# ═══════════════════════════════════════════════════════════════════
# Unknown Command Tests
# ═══════════════════════════════════════════════════════════════════


class TestUnknownCommand:
    @pytest.mark.asyncio
    async def test_unknown_command(self, orchestrator, active_session):
        events = await _collect_events(
            orchestrator, active_session.id, "/nonexistent"
        )

        text = "".join(e.data.get("text", "") for e in events if e.event_type == "token")
        assert "Unknown command" in text


# ═══════════════════════════════════════════════════════════════════
# Tool Registry Tests
# ═══════════════════════════════════════════════════════════════════


class TestToolExecution:
    @pytest.mark.asyncio
    async def test_registered_tool_called(self, session_service, active_session):
        tool_called = []

        def my_tool(content, mentions):
            tool_called.append(content)
            return "Tool result here"

        from antigravity_tool.services.intent_classifier import IntentClassifier

        orchestrator = ChatOrchestrator(
            session_service,
            intent_classifier=IntentClassifier(),
            tool_registry={"search": my_tool},
        )

        events = await _collect_events(
            orchestrator, active_session.id, "Search for all characters"
        )

        assert len(tool_called) == 1
        text = "".join(e.data.get("text", "") for e in events if e.event_type == "token")
        assert "Tool result here" in text
