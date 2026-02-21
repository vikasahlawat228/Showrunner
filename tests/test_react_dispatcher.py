"""Phase H Track 2 — ReAct Dispatcher backend tests.

Tests the AgentDispatcher's ReAct (Reason → Act → Observe) loop by
mocking LiteLLM responses and verifying tool dispatch, iteration limits,
and plain (non-ReAct) fallback behaviour.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from antigravity_tool.services.agent_dispatcher import (
    AgentDispatcher,
    AgentResult,
    AgentSkill,
    ReActTool,
    DEFAULT_MAX_REACT_ITERATIONS,
)


# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def skills_dir(tmp_path: Path) -> Path:
    """Create a minimal skills directory with one test skill."""
    d = tmp_path / "skills"
    d.mkdir()
    (d / "test_skill.md").write_text(
        "# Test Skill\n\nA test agent for unit testing the dispatcher.\n"
    )
    return d


@pytest.fixture
def dispatcher(skills_dir: Path) -> AgentDispatcher:
    """Return an AgentDispatcher loaded from the temp skills dir."""
    return AgentDispatcher(skills_dir)


def _make_llm_response(content: str):
    """Build a mock LiteLLM response object."""
    msg = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=msg)
    return SimpleNamespace(choices=[choice])


# ── Test: ReAct loop with a tool call ────────────────────────────


@pytest.mark.asyncio
async def test_react_loop_with_tool_call(dispatcher: AgentDispatcher):
    """Simulate a ReAct loop: LLM calls a tool, gets observation, then
    emits a Final Answer.
    """
    # Register a custom tool that returns a known observation
    tool_called_with: list[str] = []

    def search_handler(query: str) -> str:
        tool_called_with.append(query)
        return 'Found entity: Spaceship "Nebula Runner" (id=ship_01)'

    dispatcher.register_tool(
        ReActTool(
            name="SearchKG",
            description="Search the Knowledge Graph.",
            handler=search_handler,
        )
    )

    # Mock LiteLLM: first call returns an Action, second returns Final Answer
    call_count = 0

    async def mock_acompletion(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _make_llm_response(
                'Thought: I need to look up spaceship designs.\n'
                'Action: SearchKG("spaceship design")'
            )
        else:
            return _make_llm_response(
                'Thought: I found the Nebula Runner.\n'
                'Final Answer: The spaceship "Nebula Runner" (ship_01) '
                "is a light cruiser with advanced shielding."
            )

    skill = dispatcher.skills["test_skill"]

    with patch("antigravity_tool.services.agent_dispatcher.litellm") as mock_litellm:
        mock_litellm.acompletion = mock_acompletion
        result = await dispatcher.execute(skill, "describe the spaceship")

    assert result.success is True
    assert result.react_iterations == 2
    assert "Nebula Runner" in result.response
    assert tool_called_with == ["spaceship design"]


# ── Test: ReAct loop hits max iterations ─────────────────────────


@pytest.mark.asyncio
async def test_react_loop_max_iterations(dispatcher: AgentDispatcher):
    """When the LLM keeps emitting Action lines, the loop should terminate
    after max_iterations and return the last response.
    """
    calls = 0

    async def mock_acompletion(**kwargs):
        nonlocal calls
        calls += 1
        return _make_llm_response(
            f"Thought: Still searching (attempt {calls}).\n"
            f'Action: SearchKG("query_{calls}")'
        )

    skill = dispatcher.skills["test_skill"]
    max_iter = 3

    with patch("antigravity_tool.services.agent_dispatcher.litellm") as mock_litellm:
        mock_litellm.acompletion = mock_acompletion
        result = await dispatcher.execute(
            skill, "loop forever", max_iterations=max_iter
        )

    assert result.success is True
    assert result.react_iterations == max_iter
    # The response should contain the last LLM output (with the Action line)
    assert f"query_{max_iter}" in result.response


# ── Test: Plain execution (no ReAct) ─────────────────────────────


@pytest.mark.asyncio
async def test_execute_without_react(dispatcher: AgentDispatcher):
    """When the LLM gives a plain response (no Action/Final Answer), the
    dispatcher should return it in a single pass — backward compatible.
    """

    async def mock_acompletion(**kwargs):
        return _make_llm_response(
            "Here is a schema for your spaceship type:\n"
            '{"container_type": "spaceship", "fields": []}'
        )

    skill = dispatcher.skills["test_skill"]

    with patch("antigravity_tool.services.agent_dispatcher.litellm") as mock_litellm:
        mock_litellm.acompletion = mock_acompletion
        result = await dispatcher.execute(skill, "create spaceship schema")

    assert result.success is True
    assert result.react_iterations == 1  # Single pass
    assert "spaceship" in result.response


# ── Test: _parse_react_action edge cases ─────────────────────────


class TestParseReactAction:
    """Unit tests for the static _parse_react_action method."""

    def test_standard_action(self):
        text = 'Thought: need data\nAction: SearchKG("railgun physics")'
        result = AgentDispatcher._parse_react_action(text)
        assert result == ("SearchKG", "railgun physics")

    def test_single_quoted_action(self):
        text = "Action: GetContainer('char_zara')"
        result = AgentDispatcher._parse_react_action(text)
        assert result == ("GetContainer", "char_zara")

    def test_unquoted_action(self):
        text = "Action: ListContainers(character)"
        result = AgentDispatcher._parse_react_action(text)
        assert result == ("ListContainers", "character")

    def test_no_action(self):
        text = "Just a regular response with no tools."
        result = AgentDispatcher._parse_react_action(text)
        assert result is None

    def test_action_with_preceding_thought(self):
        text = (
            "Thought: I should check the KG for existing characters.\n"
            'Action: SearchKG("all characters")'
        )
        result = AgentDispatcher._parse_react_action(text)
        assert result == ("SearchKG", "all characters")


# ── Test: _execute_tool with unknown tool ────────────────────────


def test_execute_unknown_tool(dispatcher: AgentDispatcher):
    """Calling an unregistered tool should return an error observation."""
    obs = dispatcher._execute_tool("NonExistentTool", "arg")
    assert "Unknown tool" in obs
    assert "NonExistentTool" in obs


# ── Test: Skills loaded correctly ────────────────────────────────


def test_dispatcher_loads_all_skills():
    """Verify the dispatcher loads all skill files from the real skills dir."""
    skills_dir = (
        Path(__file__).resolve().parent.parent
        / "agents"
        / "skills"
    )
    if not skills_dir.exists():
        pytest.skip("Skills directory not found at expected path")

    dispatcher = AgentDispatcher(skills_dir)

    expected_skills = {
        "continuity_analyst",
        "graph_arranger",
        "pipeline_director",
        "research_agent",
        "schema_architect",
        "schema_wizard",
        "story_architect",
        "prompt_composer",
        "style_enforcer",
        "translator_agent",
        "brainstorm_agent",
    }
    loaded = set(dispatcher.skills.keys())
    missing = expected_skills - loaded
    assert not missing, f"Missing skills: {missing}"
