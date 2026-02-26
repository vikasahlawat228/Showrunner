"""Tests for ChatToolRegistry — intent→tool function mapping."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from pathlib import Path

import pytest

from showrunner_tool.services.chat_tool_registry import build_tool_registry


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def mock_kg_service():
    svc = MagicMock()
    svc.find_containers.return_value = [
        {"name": "Hero", "container_type": "character", "id": "char-001"},
        {"name": "Dark World", "container_type": "world", "id": "world-001"},
        {"name": "Battle Scene", "container_type": "scene", "id": "scene-001"},
    ]
    return svc


@pytest.fixture
def mock_container_repo():
    return MagicMock()


@pytest.fixture
def mock_pipeline_service():
    svc = MagicMock()
    # PipelineDefinition has .name and .steps attributes
    defn = MagicMock()
    defn.name = "Scene→Panels"
    defn.steps = [MagicMock(), MagicMock(), MagicMock()]
    defn.id = "pipe-001"
    svc.list_definitions.return_value = [defn]
    return svc


@pytest.fixture
def mock_memory_service():
    svc = MagicMock()
    entry = MagicMock()
    entry.key = "dark_fantasy_tone"
    entry.value = "Dark fantasy tone throughout"
    svc.add_entry.return_value = entry
    return svc


@pytest.fixture
def full_registry(mock_kg_service, mock_container_repo, mock_pipeline_service, mock_memory_service):
    return build_tool_registry(
        kg_service=mock_kg_service,
        container_repo=mock_container_repo,
        project_memory_service=mock_memory_service,
        pipeline_service=mock_pipeline_service,
        project_path=Path("/tmp/test_project"),
    )


# ── Registry building ────────────────────────────────────────────


class TestRegistryBuilding:
    def test_full_registry_has_all_tools(self, full_registry):
        expected = {"search", "create", "update", "delete", "navigate", "evaluate", "research", "relationship", "world_summary", "pipeline", "decide", "unresolved_threads", "plausibility_check", "save_to_memory"}
        assert set(full_registry.keys()) == expected

    def test_empty_registry_has_navigate_only(self):
        registry = build_tool_registry()
        assert set(registry.keys()) == {"navigate"}

    def test_partial_registry_only_search(self, mock_kg_service):
        registry = build_tool_registry(kg_service=mock_kg_service)
        assert "search" in registry
        assert "update" in registry
        assert "delete" in registry
        assert "evaluate" in registry
        assert "research" in registry
        assert "navigate" in registry
        assert "create" not in registry  # needs container_repo + project_path
        assert "pipeline" not in registry  # needs pipeline_service
        assert "decide" not in registry  # needs memory_service


# ── SEARCH tool ─────────────────────────────────────────────────


class TestSearchTool:
    def test_search_finds_by_name(self, full_registry, mock_kg_service):
        result = full_registry["search"]("Find Hero", [])
        assert "Found" in result
        assert "Hero" in result

    def test_search_no_results(self, full_registry, mock_kg_service):
        mock_kg_service.find_containers.return_value = []
        mock_kg_service.semantic_search.side_effect = Exception("no semantic")
        result = full_registry["search"]("Find nonexistent xyz", [])
        assert "No results found" in result

    def test_search_fallback_to_semantic(self, full_registry, mock_kg_service):
        mock_kg_service.find_containers.return_value = []
        mock_kg_service.semantic_search.return_value = [
            {"name": "Semantic Result", "container_type": "character"}
        ]
        result = full_registry["search"]("Find something abstract", [])
        assert "Found" in result
        assert "Semantic Result" in result


# ── CREATE tool ─────────────────────────────────────────────────


class TestCreateTool:
    @patch("litellm.completion")
    def test_create_character(self, mock_completion, full_registry):
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="- type: character\n  name: Villain"))]
        )
        result = full_registry["create"]('Create a character called "Villain"', [])
        assert "character" in result
        assert "Villain" in result

    @patch("litellm.completion")
    def test_create_scene(self, mock_completion, full_registry):
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="- type: scene\n  name: Battle"))]
        )
        result = full_registry["create"]("Create a scene for the battle", [])
        assert "scene" in result

    @patch("litellm.completion")
    def test_create_unknown_type(self, mock_completion, full_registry):
        # Mock LLM to return something that doesn't match a known type in the fallback
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="I can't help with that."))]
        )
        result = full_registry["create"]("Create something weird", [])
        # The new implementation returns a 'couldn't automatically scaffold' message
        assert "automatically scaffold" in result.lower()


# ── UPDATE tool ─────────────────────────────────────────────────


class TestUpdateTool:
    def test_update_with_mentions(self, full_registry):
        result = full_registry["update"]("Change hair color to black", ["char-001"])
        assert "char-001" in result
        assert "Approval required" in result

    def test_update_without_mentions(self, full_registry):
        result = full_registry["update"]("Update the character description", [])
        assert "@mention" in result


# ── DELETE tool ─────────────────────────────────────────────────


class TestDeleteTool:
    def test_delete_with_mentions(self, full_registry):
        result = full_registry["delete"]("Delete this character", ["char-001"])
        assert "char-001" in result
        assert "destructive" in result.lower()

    def test_delete_without_mentions(self, full_registry):
        result = full_registry["delete"]("Delete the old scene", [])
        assert "@mention" in result


# ── NAVIGATE tool ───────────────────────────────────────────────


class TestNavigateTool:
    def test_navigate_storyboard(self, full_registry):
        result = full_registry["navigate"]("Go to the storyboard", [])
        assert "/storyboard" in result

    def test_navigate_dashboard(self, full_registry):
        result = full_registry["navigate"]("Show me the dashboard", [])
        assert "/dashboard" in result

    def test_navigate_zen(self, full_registry):
        result = full_registry["navigate"]("Open zen mode", [])
        assert "/zen" in result

    def test_navigate_unknown(self, full_registry):
        result = full_registry["navigate"]("Go to xyzzy", [])
        assert "Available views" in result


# ── EVALUATE tool ───────────────────────────────────────────────


class TestEvaluateTool:
    def test_evaluate_lists_checks(self, full_registry):
        result = full_registry["evaluate"]("Evaluate this scene", [])
        assert "Scene quality" in result
        assert "Character consistency" in result
        assert "Continuity" in result


# ── RESEARCH tool ───────────────────────────────────────────────


class TestResearchTool:
    def test_research_echoes_content(self, full_registry):
        result = full_registry["research"]("Research feudal Japan warfare", [])
        assert "feudal Japan warfare" in result


# ── PIPELINE tool ───────────────────────────────────────────────


class TestPipelineTool:
    @pytest.mark.asyncio
    async def test_pipeline_lists_definitions(self, full_registry):
        result_gen = full_registry["pipeline"]("Show pipelines", [])
        chunks = []
        async for chunk in result_gen:
            chunks.append(str(chunk))
        result = "".join(chunks)
        assert "Scene→Panels" in result
        assert "3 steps" in result

    @pytest.mark.asyncio
    async def test_pipeline_empty(self, full_registry, mock_pipeline_service):
        mock_pipeline_service.list_definitions.return_value = []
        result_gen = full_registry["pipeline"]("Show pipelines", [])
        chunks = []
        async for chunk in result_gen:
            chunks.append(str(chunk))
        result = "".join(chunks)
        assert "No pipeline definitions" in result

    @pytest.mark.asyncio
    async def test_pipeline_error(self, full_registry, mock_pipeline_service):
        mock_pipeline_service.list_definitions.side_effect = RuntimeError("DB error")
        result_gen = full_registry["pipeline"]("Show pipelines", [])
        chunks = []
        async for chunk in result_gen:
            chunks.append(str(chunk))
        result = "".join(chunks)
        assert "error" in result.lower()


# ── DECIDE tool ─────────────────────────────────────────────────


class TestDecideTool:
    def test_decide_records_decision(self, full_registry, mock_memory_service):
        result = full_registry["decide"]("Always use dark fantasy tone", [])
        assert "Decision recorded" in result
        assert "dark_fantasy_tone" in result
        mock_memory_service.add_entry.assert_called_once()

    def test_decide_with_remember_prefix(self, full_registry, mock_memory_service):
        result = full_registry["decide"]("remember that magic costs blood", [])
        assert "Decision recorded" in result
        mock_memory_service.add_entry.assert_called_once()
        # The value should strip the "remember that " prefix
        call_kwargs = mock_memory_service.add_entry.call_args
        assert "magic costs blood" in call_kwargs.kwargs.get("value", call_kwargs[1].get("value", ""))
