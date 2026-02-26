"""Phase H Track 3 — NL-to-DAG Pipeline Generation Tests.

Tests cover:
  1. generate_pipeline_from_nl() — basic 2-step pipeline from mocked LLM
  2. Logic node mapping (IF_ELSE) from intent
  3. Graceful error on invalid JSON from LLM
  4. API endpoint integration via TestClient
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from showrunner_tool.schemas.pipeline_steps import (
    PipelineDefinition,
    PipelineStepDef,
    PipelineEdge,
    StepType,
)
from showrunner_tool.repositories.container_repo import ContainerRepository
from showrunner_tool.repositories.event_sourcing_repo import EventService
from showrunner_tool.services.pipeline_service import PipelineService
from showrunner_tool.services.agent_dispatcher import AgentDispatcher, AgentSkill, AgentResult


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / "schemas").mkdir()
    (tmp_path / "showrunner.yaml").write_text(
        "name: Test Project\nversion: 0.1.0\n"
    )
    return tmp_path


@pytest.fixture
def pipeline_service(tmp_project: Path) -> PipelineService:
    container_repo = ContainerRepository(tmp_project)
    event_service = EventService(tmp_project / "events.db")
    return PipelineService(container_repo, event_service)


@pytest.fixture
def mock_dispatcher() -> AgentDispatcher:
    """Create an AgentDispatcher with a pipeline_director skill but no real files."""
    dispatcher = AgentDispatcher.__new__(AgentDispatcher)
    dispatcher.skills = {
        "pipeline_director": AgentSkill(
            name="pipeline_director",
            description="Assembles pipeline DAGs from natural language.",
            system_prompt="You are the Pipeline Director.",
            keywords=["pipeline", "workflow", "dag"],
        )
    }
    return dispatcher


def _make_llm_response(content: str):
    """Build a mock litellm response with the given content string."""
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


# ═══════════════════════════════════════════════════════════════════
# Test: Basic 2-step pipeline generation
# ═══════════════════════════════════════════════════════════════════


BASIC_LLM_JSON = json.dumps({
    "steps": [
        {
            "id": "step_1",
            "step_type": "prompt_template",
            "label": "Assemble Outline Prompt",
            "config": {"template_inline": "Write a 3-act outline for: {{text}}"},
        },
        {
            "id": "step_2",
            "step_type": "llm_generate",
            "label": "Generate Outline",
            "config": {"model": "gemini/gemini-2.0-flash", "temperature": 0.7},
        },
        {
            "id": "step_3",
            "step_type": "review_prompt",
            "label": "Review Output",
            "config": {},
        },
    ],
    "edges": [
        {"source": "step_1", "target": "step_2"},
        {"source": "step_2", "target": "step_3"},
    ],
})


class TestGeneratePipelineBasic:
    @pytest.mark.asyncio
    async def test_generate_pipeline_from_nl_basic(
        self, pipeline_service: PipelineService, mock_dispatcher: AgentDispatcher
    ):
        """Mock LLM returns valid JSON → parses into PipelineDefinition."""
        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response(BASIC_LLM_JSON)

            definition = await pipeline_service.generate_pipeline_from_nl(
                intent="Create a 3-act structure and critique it",
                title="Structure Gen",
                agent_dispatcher=mock_dispatcher,
            )

        assert isinstance(definition, PipelineDefinition)
        assert definition.name == "Structure Gen"
        assert "Auto-generated from intent" in definition.description

        # Must have at least 2 steps and 1 edge
        assert len(definition.steps) >= 2
        assert len(definition.edges) >= 1

        # Verify step types are valid
        step_types = {s.step_type for s in definition.steps}
        assert StepType.PROMPT_TEMPLATE in step_types
        assert StepType.LLM_GENERATE in step_types

        # Verify edges connect valid step IDs
        step_ids = {s.id for s in definition.steps}
        for edge in definition.edges:
            assert edge.source in step_ids
            assert edge.target in step_ids

    @pytest.mark.asyncio
    async def test_generate_pipeline_handles_code_fences(
        self, pipeline_service: PipelineService, mock_dispatcher: AgentDispatcher
    ):
        """LLM wraps JSON in markdown code fences → still parses correctly."""
        fenced_response = f"Here is the pipeline:\n```json\n{BASIC_LLM_JSON}\n```\n"

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response(fenced_response)

            definition = await pipeline_service.generate_pipeline_from_nl(
                intent="Generate an outline",
                title="Fenced Test",
                agent_dispatcher=mock_dispatcher,
            )

        assert isinstance(definition, PipelineDefinition)
        assert len(definition.steps) >= 2


# ═══════════════════════════════════════════════════════════════════
# Test: Logic node mapping (IF_ELSE)
# ═══════════════════════════════════════════════════════════════════


LOGIC_NODE_JSON = json.dumps({
    "steps": [
        {
            "id": "step_1",
            "step_type": "llm_generate",
            "label": "Generate Draft",
            "config": {"model": "gemini/gemini-2.0-flash"},
        },
        {
            "id": "step_2",
            "step_type": "if_else",
            "label": "Check Word Count",
            "config": {
                "condition": "word_count > 500",
                "true_target": "step_3",
                "false_target": "step_4",
            },
        },
        {
            "id": "step_3",
            "step_type": "save_to_bucket",
            "label": "Save Long Draft",
            "config": {"container_type": "fragment"},
        },
        {
            "id": "step_4",
            "step_type": "llm_generate",
            "label": "Expand Draft",
            "config": {"model": "gemini/gemini-2.0-flash"},
        },
    ],
    "edges": [
        {"source": "step_1", "target": "step_2"},
        {"source": "step_2", "target": "step_3"},
        {"source": "step_2", "target": "step_4"},
    ],
})


class TestGeneratePipelineLogicNodes:
    @pytest.mark.asyncio
    async def test_generate_pipeline_with_logic_nodes(
        self, pipeline_service: PipelineService, mock_dispatcher: AgentDispatcher
    ):
        """Mock LLM includes IF_ELSE step → maps to StepType.IF_ELSE."""
        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response(LOGIC_NODE_JSON)

            definition = await pipeline_service.generate_pipeline_from_nl(
                intent="Generate a draft and if it's long enough, save it; otherwise expand it",
                title="Conditional Pipeline",
                agent_dispatcher=mock_dispatcher,
            )

        assert isinstance(definition, PipelineDefinition)
        assert len(definition.steps) == 4
        assert len(definition.edges) == 3

        # Find the IF_ELSE step
        if_else_steps = [s for s in definition.steps if s.step_type == StepType.IF_ELSE]
        assert len(if_else_steps) == 1

        if_step = if_else_steps[0]
        assert if_step.config["condition"] == "word_count > 500"
        assert if_step.config["true_target"] == "step_3"
        assert if_step.config["false_target"] == "step_4"


# ═══════════════════════════════════════════════════════════════════
# Test: Invalid JSON handling
# ═══════════════════════════════════════════════════════════════════


class TestGeneratePipelineErrors:
    @pytest.mark.asyncio
    async def test_generate_pipeline_invalid_json_raises(
        self, pipeline_service: PipelineService, mock_dispatcher: AgentDispatcher
    ):
        """Mock LLM returns garbage → raises ValueError."""
        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response(
                "Sorry, I can't generate a pipeline right now."
            )

            with pytest.raises(ValueError, match="Failed to parse pipeline JSON"):
                await pipeline_service.generate_pipeline_from_nl(
                    intent="do something",
                    title="Bad Pipeline",
                    agent_dispatcher=mock_dispatcher,
                )

    @pytest.mark.asyncio
    async def test_generate_pipeline_empty_steps_raises(
        self, pipeline_service: PipelineService, mock_dispatcher: AgentDispatcher
    ):
        """Mock LLM returns valid JSON but with no steps → raises ValueError."""
        empty_json = json.dumps({"steps": [], "edges": []})

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response(empty_json)

            with pytest.raises(ValueError, match="no pipeline steps"):
                await pipeline_service.generate_pipeline_from_nl(
                    intent="do something",
                    title="Empty Pipeline",
                    agent_dispatcher=mock_dispatcher,
                )

    @pytest.mark.asyncio
    async def test_generate_pipeline_llm_failure_raises(
        self, pipeline_service: PipelineService, mock_dispatcher: AgentDispatcher
    ):
        """AgentDispatcher reports failure → raises ValueError."""
        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("API rate limited")

            with pytest.raises(ValueError, match="Pipeline generation failed"):
                await pipeline_service.generate_pipeline_from_nl(
                    intent="do something",
                    title="Failed Pipeline",
                    agent_dispatcher=mock_dispatcher,
                )


# ═══════════════════════════════════════════════════════════════════
# Test: API Endpoint via TestClient
# ═══════════════════════════════════════════════════════════════════


class TestGeneratePipelineEndpoint:
    @pytest.mark.asyncio
    async def test_generate_pipeline_api_endpoint(self, tmp_project: Path):
        """POST /api/pipeline/definitions/generate returns 201 with valid pipeline."""
        from fastapi import FastAPI
        from showrunner_tool.server.routers import pipeline as pipeline_router

        app = FastAPI()
        app.include_router(pipeline_router.router, prefix="/api")

        # Override DI dependencies
        container_repo = ContainerRepository(tmp_project)
        event_service = EventService(tmp_project / "events.db")
        svc = PipelineService(container_repo, event_service)

        dispatcher = AgentDispatcher.__new__(AgentDispatcher)
        dispatcher.skills = {
            "pipeline_director": AgentSkill(
                name="pipeline_director",
                description="Assembles pipeline DAGs.",
                system_prompt="You are the Pipeline Director.",
                keywords=["pipeline"],
            )
        }

        from showrunner_tool.server.deps import get_pipeline_service, get_agent_dispatcher
        app.dependency_overrides[get_pipeline_service] = lambda: svc
        app.dependency_overrides[get_agent_dispatcher] = lambda: dispatcher

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response(BASIC_LLM_JSON)

            client = TestClient(app)
            response = client.post(
                "/api/pipeline/definitions/generate",
                json={
                    "intent": "Create a 3-act structure and critique it",
                    "title": "Structure Gen",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Structure Gen"
        assert len(data["steps"]) >= 2
        assert len(data["edges"]) >= 1
        assert data["id"]  # has a generated ID
        assert data["created_at"]
