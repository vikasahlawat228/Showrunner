"""Phase G Track 2 -- Research Agent tests.

Tests cover:
  1. ResearchService CRUD (save, list, get)
  2. Container creation with correct attributes
  3. Agent dispatch execution (mocked)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from antigravity_tool.repositories.container_repo import ContainerRepository
from antigravity_tool.repositories.event_sourcing_repo import EventService
from antigravity_tool.services.agent_dispatcher import AgentResult, AgentSkill
from antigravity_tool.services.research_service import ResearchService


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def container_repo(tmp_path: Path) -> ContainerRepository:
    """Container repo pointing at a temp dir."""
    return ContainerRepository(tmp_path)


@pytest.fixture
def event_service() -> EventService:
    """In-memory event service."""
    return EventService(":memory:")


@pytest.fixture
def mock_dispatcher() -> MagicMock:
    """Mock AgentDispatcher with a research_agent skill loaded."""
    dispatcher = MagicMock()
    dispatcher.skills = {
        "research_agent": AgentSkill(
            name="research_agent",
            description="Research librarian",
            system_prompt="You are a research agent",
            keywords=["research"],
        )
    }
    return dispatcher


@pytest.fixture
def research_service(
    container_repo: ContainerRepository,
    event_service: EventService,
    mock_dispatcher: MagicMock,
) -> ResearchService:
    """ResearchService wired with test dependencies."""
    return ResearchService(container_repo, event_service, mock_dispatcher)


# ═══════════════════════════════════════════════════════════════════
# Tests: save_research
# ═══════════════════════════════════════════════════════════════════


class TestResearchServiceSave:
    def test_save_creates_container_with_correct_type(self, research_service):
        """save_research creates a GenericContainer with container_type='research_topic'."""
        container = research_service.save_research(
            query="Medieval castle architecture",
            summary="Castles were fortified structures built across Europe.",
            confidence_score=0.85,
            sources=["Wikipedia: Castle", "Britannica: Fortification"],
            key_facts={"primary_material": "stone", "era": "11th-15th century"},
        )
        assert container.container_type == "research_topic"
        assert container.name == "Research: Medieval castle architecture"

    def test_save_stores_all_attributes(self, research_service):
        """All research fields are stored in the container attributes."""
        container = research_service.save_research(
            query="Dragon mythology",
            summary="Dragons appear across many cultures.",
            confidence_score=0.9,
            sources=["Mythology Database"],
            key_facts={"element": "fire", "origin": "worldwide"},
        )
        attrs = container.attributes
        assert attrs["original_query"] == "Dragon mythology"
        assert attrs["summary"] == "Dragons appear across many cultures."
        assert attrs["confidence_score"] == 0.9
        assert attrs["sources"] == ["Mythology Database"]
        assert attrs["key_facts"] == {"element": "fire", "origin": "worldwide"}

    def test_save_persists_to_repository(self, research_service, container_repo):
        """Saved research is retrievable from the container repository."""
        research_service.save_research(
            query="Sword types",
            summary="Various sword types existed across cultures.",
            confidence_score=0.8,
            sources=["Arms & Armor DB"],
            key_facts={"katana": "Japanese single-edged"},
        )
        containers = container_repo.list_by_type("research_topic")
        assert len(containers) == 1
        assert containers[0].attributes["original_query"] == "Sword types"

    def test_save_emits_create_event(self, research_service, event_service):
        """save_research emits a CREATE event to the event service."""
        container = research_service.save_research(
            query="Alchemy",
            summary="The predecessor of chemistry.",
            confidence_score=0.7,
            sources=["History of Science"],
            key_facts={"goal": "transmutation"},
        )
        events = event_service.get_all_events()
        assert len(events) >= 1
        latest = events[-1]
        assert latest["event_type"] == "CREATE"
        assert latest["container_id"] == container.id


# ═══════════════════════════════════════════════════════════════════
# Tests: list_research
# ═══════════════════════════════════════════════════════════════════


class TestResearchServiceList:
    def test_list_returns_all_research_topics(self, research_service):
        """list_research returns all persisted research containers."""
        research_service.save_research(
            query="Q1", summary="S1",
            confidence_score=0.5, sources=[], key_facts={},
        )
        research_service.save_research(
            query="Q2", summary="S2",
            confidence_score=0.7, sources=["src"], key_facts={"k": "v"},
        )
        items = research_service.list_research()
        assert len(items) == 2
        queries = {item["original_query"] for item in items}
        assert queries == {"Q1", "Q2"}

    def test_list_returns_empty_when_no_research(self, research_service):
        """list_research returns an empty list when no research exists."""
        items = research_service.list_research()
        assert items == []

    def test_list_items_have_expected_keys(self, research_service):
        """Each item in list_research has all expected dict keys."""
        research_service.save_research(
            query="Test", summary="Test summary",
            confidence_score=0.6, sources=["src1"], key_facts={"a": "b"},
        )
        items = research_service.list_research()
        item = items[0]
        expected_keys = {
            "id", "original_query", "summary", "confidence_score",
            "sources", "key_facts", "created_at", "updated_at",
        }
        assert set(item.keys()) == expected_keys


# ═══════════════════════════════════════════════════════════════════
# Tests: get_research
# ═══════════════════════════════════════════════════════════════════


class TestResearchServiceGet:
    def test_get_returns_correct_item(self, research_service):
        """get_research returns the correct research item by ID."""
        container = research_service.save_research(
            query="Navigation in the Age of Sail",
            summary="Celestial navigation was the primary method.",
            confidence_score=0.85,
            sources=["Maritime History DB"],
            key_facts={"instrument": "sextant"},
        )
        result = research_service.get_research(container.id)
        assert result is not None
        assert result["original_query"] == "Navigation in the Age of Sail"
        assert result["id"] == container.id

    def test_get_returns_none_for_missing_id(self, research_service):
        """get_research returns None for a nonexistent ID."""
        assert research_service.get_research("nonexistent-id") is None


# ═══════════════════════════════════════════════════════════════════
# Tests: execute_research (async, mocked dispatcher)
# ═══════════════════════════════════════════════════════════════════


class TestResearchServiceExecute:
    @pytest.mark.asyncio
    async def test_execute_success_saves_and_returns(
        self, research_service, mock_dispatcher
    ):
        """execute_research dispatches to agent, saves result, and returns dict."""
        mock_dispatcher.execute = AsyncMock(
            return_value=AgentResult(
                skill_used="research_agent",
                response="",
                actions=[
                    {
                        "summary": "Castles are fortified medieval structures.",
                        "confidence_score": 0.85,
                        "sources": ["Wikipedia: Castle"],
                        "key_facts": {"walls": "thick stone"},
                    }
                ],
                success=True,
            )
        )

        result = await research_service.execute_research("Medieval castles")
        assert result is not None
        assert result["summary"] == "Castles are fortified medieval structures."
        assert result["confidence_score"] == 0.85
        assert result["sources"] == ["Wikipedia: Castle"]
        assert result["key_facts"] == {"walls": "thick stone"}
        assert result["original_query"] == "Medieval castles"
        assert "id" in result

    @pytest.mark.asyncio
    async def test_execute_persists_container(
        self, research_service, mock_dispatcher, container_repo
    ):
        """execute_research persists the result as a container."""
        mock_dispatcher.execute = AsyncMock(
            return_value=AgentResult(
                skill_used="research_agent",
                response="",
                actions=[
                    {
                        "summary": "Test summary",
                        "confidence_score": 0.7,
                        "sources": ["src"],
                        "key_facts": {},
                    }
                ],
                success=True,
            )
        )

        await research_service.execute_research("Test query")
        containers = container_repo.list_by_type("research_topic")
        assert len(containers) == 1

    @pytest.mark.asyncio
    async def test_execute_returns_none_on_agent_failure(
        self, research_service, mock_dispatcher
    ):
        """execute_research returns None when the agent fails."""
        mock_dispatcher.execute = AsyncMock(
            return_value=AgentResult(
                skill_used="research_agent",
                response="",
                actions=[],
                success=False,
                error="LLM timeout",
            )
        )

        result = await research_service.execute_research("Failing query")
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_returns_none_when_skill_missing(
        self, research_service, mock_dispatcher
    ):
        """execute_research returns None when research_agent skill isn't loaded."""
        mock_dispatcher.skills = {}
        result = await research_service.execute_research("Any query")
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_handles_unparseable_response(
        self, research_service, mock_dispatcher
    ):
        """execute_research returns None when agent response isn't valid JSON."""
        mock_dispatcher.execute = AsyncMock(
            return_value=AgentResult(
                skill_used="research_agent",
                response="This is not JSON at all",
                actions=[],
                success=True,
            )
        )

        result = await research_service.execute_research("Bad response query")
        assert result is None
