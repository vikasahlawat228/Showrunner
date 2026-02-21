"""Phase G Track 1 — Pipeline Logic Node Tests.

Tests cover:
  1. evaluate_condition() — the safe expression evaluator
  2. IF_ELSE branching pipeline
  3. LOOP pipeline with exit condition and max iterations
  4. MERGE_OUTPUTS pipeline
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from antigravity_tool.schemas.pipeline_steps import (
    PipelineDefinition,
    PipelineStepDef,
    PipelineEdge,
    StepType,
    StepCategory,
    STEP_CATEGORIES,
)
from antigravity_tool.schemas.pipeline import PipelineState
from antigravity_tool.repositories.container_repo import ContainerRepository
from antigravity_tool.repositories.event_sourcing_repo import EventService
from antigravity_tool.services.pipeline_service import (
    PipelineService,
    evaluate_condition,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / "schemas").mkdir()
    (tmp_path / "antigravity.yaml").write_text(
        "name: Test Project\nversion: 0.1.0\n"
    )
    return tmp_path


@pytest.fixture
def pipeline_service(tmp_project: Path) -> PipelineService:
    container_repo = ContainerRepository(tmp_project)
    event_service = EventService(tmp_project / "events.db")
    return PipelineService(container_repo, event_service)


# ═══════════════════════════════════════════════════════════════════
# Schema Tests — new enum values exist
# ═══════════════════════════════════════════════════════════════════


class TestSchemaEnums:
    def test_step_types_include_logic_nodes(self):
        assert StepType.IF_ELSE == "if_else"
        assert StepType.LOOP == "loop"
        assert StepType.MERGE_OUTPUTS == "merge_outputs"

    def test_step_category_includes_logic(self):
        assert StepCategory.LOGIC == "logic"

    def test_step_categories_map_logic_nodes(self):
        assert STEP_CATEGORIES[StepType.IF_ELSE] == StepCategory.LOGIC
        assert STEP_CATEGORIES[StepType.LOOP] == StepCategory.LOGIC
        assert STEP_CATEGORIES[StepType.MERGE_OUTPUTS] == StepCategory.LOGIC


# ═══════════════════════════════════════════════════════════════════
# evaluate_condition() unit tests
# ═══════════════════════════════════════════════════════════════════


class TestEvaluateCondition:
    def test_simple_gt(self):
        assert evaluate_condition("x > 5", {"x": 10}) is True
        assert evaluate_condition("x > 5", {"x": 3}) is False

    def test_equality(self):
        assert evaluate_condition("status == 'done'", {"status": "done"}) is True
        assert evaluate_condition("status == 'done'", {"status": "pending"}) is False

    def test_boolean_literal(self):
        assert evaluate_condition("ready == true", {"ready": True}) is True
        assert evaluate_condition("ready == false", {"ready": False}) is True

    def test_boolean_and_or(self):
        assert evaluate_condition("a > 1 and b > 1", {"a": 2, "b": 2}) is True
        assert evaluate_condition("a > 1 and b > 1", {"a": 2, "b": 0}) is False
        assert evaluate_condition("a > 1 or b > 1", {"a": 0, "b": 2}) is True

    def test_not(self):
        assert evaluate_condition("not ready", {"ready": False}) is True
        assert evaluate_condition("not ready", {"ready": True}) is False

    def test_missing_key_is_none(self):
        assert evaluate_condition("missing == None", {"other": 1}) is True

    def test_empty_expression_returns_false(self):
        assert evaluate_condition("", {}) is False
        assert evaluate_condition("  ", {}) is False

    def test_invalid_expression_raises(self):
        with pytest.raises(ValueError, match="Invalid condition"):
            evaluate_condition("x >>>= 5", {"x": 1})

    def test_disallowed_node_raises(self):
        with pytest.raises(ValueError, match="Disallowed expression"):
            evaluate_condition("print('hello')", {})

    def test_arithmetic(self):
        assert evaluate_condition("a + b > 10", {"a": 6, "b": 7}) is True
        assert evaluate_condition("a * 2 == 10", {"a": 5}) is True

    def test_nested_dict_access(self):
        payload = {"result": {"ready": True, "score": 95}}
        assert evaluate_condition("result.ready == true", payload) is True
        assert evaluate_condition("result.score > 90", payload) is True


# ═══════════════════════════════════════════════════════════════════
# IF_ELSE Branching Pipeline
# ═══════════════════════════════════════════════════════════════════


class TestIfElsePipeline:
    """Pipeline: step_start → if_check → (branch_a | branch_b)

    step_start sets a value; if_check routes based on it.
    """

    def _build_branching_definition(self) -> PipelineDefinition:
        return PipelineDefinition(
            name="Branching Test",
            steps=[
                PipelineStepDef(
                    id="start",
                    step_type=StepType.PROMPT_TEMPLATE,
                    label="Start",
                    config={"template_inline": "{{text}}"},
                ),
                PipelineStepDef(
                    id="if_check",
                    step_type=StepType.IF_ELSE,
                    label="Check Value",
                    config={
                        "condition": "value > 5",
                        "true_target": "branch_a",
                        "false_target": "branch_b",
                    },
                ),
                PipelineStepDef(
                    id="branch_a",
                    step_type=StepType.PROMPT_TEMPLATE,
                    label="Branch A (high)",
                    config={"template_inline": "HIGH"},
                ),
                PipelineStepDef(
                    id="branch_b",
                    step_type=StepType.PROMPT_TEMPLATE,
                    label="Branch B (low)",
                    config={"template_inline": "LOW"},
                ),
            ],
            edges=[
                PipelineEdge(source="start", target="if_check"),
                PipelineEdge(source="if_check", target="branch_a"),
                PipelineEdge(source="if_check", target="branch_b"),
            ],
        )

    @pytest.mark.asyncio
    async def test_if_else_true_branch(self, pipeline_service: PipelineService):
        definition = self._build_branching_definition()
        pipeline_service.save_definition(definition)

        run_id = await pipeline_service.start_pipeline(
            initial_payload={"text": "hello", "value": 10},
            definition_id=definition.id,
        )

        # Wait for pipeline to complete
        for _ in range(50):
            run = PipelineService._runs.get(run_id)
            if run and run.current_state in (PipelineState.COMPLETED, PipelineState.FAILED):
                break
            await asyncio.sleep(0.1)

        run = PipelineService._runs[run_id]
        assert run.current_state == PipelineState.COMPLETED
        # Should have gone through start → if_check → branch_a
        assert "start" in run.steps_completed
        assert "if_check" in run.steps_completed
        assert "branch_a" in run.steps_completed
        assert "branch_b" not in run.steps_completed
        # Logic metadata should be recorded
        assert run.payload["_logic"]["if_check"]["result"] is True

    @pytest.mark.asyncio
    async def test_if_else_false_branch(self, pipeline_service: PipelineService):
        definition = self._build_branching_definition()
        pipeline_service.save_definition(definition)

        run_id = await pipeline_service.start_pipeline(
            initial_payload={"text": "hello", "value": 2},
            definition_id=definition.id,
        )

        for _ in range(50):
            run = PipelineService._runs.get(run_id)
            if run and run.current_state in (PipelineState.COMPLETED, PipelineState.FAILED):
                break
            await asyncio.sleep(0.1)

        run = PipelineService._runs[run_id]
        assert run.current_state == PipelineState.COMPLETED
        # Should have gone through start → if_check → branch_b
        assert "start" in run.steps_completed
        assert "if_check" in run.steps_completed
        assert "branch_b" in run.steps_completed
        assert "branch_a" not in run.steps_completed
        assert run.payload["_logic"]["if_check"]["result"] is False


# ═══════════════════════════════════════════════════════════════════
# LOOP Pipeline
# ═══════════════════════════════════════════════════════════════════


class TestLoopPipeline:
    """Pipeline: init → work → loop_check → (back to work | done)

    The work step increments a counter in the payload.
    The loop_check exits when counter >= 3.
    """

    def _build_loop_definition(self) -> PipelineDefinition:
        return PipelineDefinition(
            name="Loop Test",
            steps=[
                PipelineStepDef(
                    id="init",
                    step_type=StepType.PROMPT_TEMPLATE,
                    label="Init",
                    config={"template_inline": "start"},
                ),
                PipelineStepDef(
                    id="work",
                    step_type=StepType.SAVE_TO_BUCKET,
                    label="Do Work",
                    config={"container_type": "fragment"},
                ),
                PipelineStepDef(
                    id="loop_check",
                    step_type=StepType.LOOP,
                    label="Loop Check",
                    config={
                        "condition": "ready == true",
                        "loop_back_to": "work",
                        "max_iterations": 5,
                    },
                ),
                PipelineStepDef(
                    id="done",
                    step_type=StepType.PROMPT_TEMPLATE,
                    label="Done",
                    config={"template_inline": "finished"},
                ),
            ],
            edges=[
                PipelineEdge(source="init", target="work"),
                PipelineEdge(source="work", target="loop_check"),
                PipelineEdge(source="loop_check", target="done"),
            ],
        )

    @pytest.mark.asyncio
    async def test_loop_exits_on_condition(self, pipeline_service: PipelineService):
        """The loop should exit immediately if the exit condition is already true."""
        definition = self._build_loop_definition()
        pipeline_service.save_definition(definition)

        run_id = await pipeline_service.start_pipeline(
            initial_payload={"ready": True},
            definition_id=definition.id,
        )

        for _ in range(50):
            run = PipelineService._runs.get(run_id)
            if run and run.current_state in (PipelineState.COMPLETED, PipelineState.FAILED):
                break
            await asyncio.sleep(0.1)

        run = PipelineService._runs[run_id]
        assert run.current_state == PipelineState.COMPLETED
        assert "done" in run.steps_completed
        # Loop should have run exactly once (exit met on first check)
        assert run.payload["_logic"]["loop_check"]["exit_met"] is True
        assert run.payload["_logic"]["loop_check"]["iteration"] == 1

    @pytest.mark.asyncio
    async def test_loop_respects_max_iterations(self, pipeline_service: PipelineService):
        """When the condition is never met, the loop should stop at max_iterations."""
        definition = self._build_loop_definition()
        # Override max_iterations to 3 for faster testing
        for step in definition.steps:
            if step.id == "loop_check":
                step.config["max_iterations"] = 3
        pipeline_service.save_definition(definition)

        run_id = await pipeline_service.start_pipeline(
            initial_payload={"ready": False},
            definition_id=definition.id,
        )

        for _ in range(100):
            run = PipelineService._runs.get(run_id)
            if run and run.current_state in (PipelineState.COMPLETED, PipelineState.FAILED):
                break
            await asyncio.sleep(0.1)

        run = PipelineService._runs[run_id]
        assert run.current_state == PipelineState.COMPLETED
        # Should have looped exactly max_iterations times
        assert run.payload["_logic"]["loop_check"]["iteration"] == 3
        assert "done" in run.steps_completed
        # "work" should appear multiple times in steps_completed (3 visits)
        work_count = run.steps_completed.count("work")
        assert work_count == 3


# ═══════════════════════════════════════════════════════════════════
# MERGE_OUTPUTS Pipeline
# ═══════════════════════════════════════════════════════════════════


class TestMergeOutputsPipeline:
    """Pipeline: step_a → step_b → merge → finish

    step_a and step_b each produce a dict in the payload,
    merge combines them.
    """

    def _build_merge_definition(self) -> PipelineDefinition:
        return PipelineDefinition(
            name="Merge Test",
            steps=[
                PipelineStepDef(
                    id="step_a",
                    step_type=StepType.PROMPT_TEMPLATE,
                    label="Step A",
                    config={"template_inline": "a output"},
                ),
                PipelineStepDef(
                    id="step_b",
                    step_type=StepType.PROMPT_TEMPLATE,
                    label="Step B",
                    config={"template_inline": "b output"},
                ),
                PipelineStepDef(
                    id="merge",
                    step_type=StepType.MERGE_OUTPUTS,
                    label="Merge",
                    config={
                        "source_keys": ["branch_a_data", "branch_b_data"],
                        "merge_strategy": "shallow",
                    },
                ),
                PipelineStepDef(
                    id="finish",
                    step_type=StepType.PROMPT_TEMPLATE,
                    label="Finish",
                    config={"template_inline": "done"},
                ),
            ],
            edges=[
                PipelineEdge(source="step_a", target="step_b"),
                PipelineEdge(source="step_b", target="merge"),
                PipelineEdge(source="merge", target="finish"),
            ],
        )

    @pytest.mark.asyncio
    async def test_merge_outputs_combines_payload_keys(self, pipeline_service: PipelineService):
        definition = self._build_merge_definition()
        pipeline_service.save_definition(definition)

        run_id = await pipeline_service.start_pipeline(
            initial_payload={
                "branch_a_data": {"title": "Chapter 1", "words": 500},
                "branch_b_data": {"summary": "A hero's journey", "rating": 4.5},
            },
            definition_id=definition.id,
        )

        for _ in range(50):
            run = PipelineService._runs.get(run_id)
            if run and run.current_state in (PipelineState.COMPLETED, PipelineState.FAILED):
                break
            await asyncio.sleep(0.1)

        run = PipelineService._runs[run_id]
        assert run.current_state == PipelineState.COMPLETED
        assert "merge" in run.steps_completed

        merged = run.payload.get("merged", {})
        assert merged["title"] == "Chapter 1"
        assert merged["words"] == 500
        assert merged["summary"] == "A hero's journey"
        assert merged["rating"] == 4.5

    @pytest.mark.asyncio
    async def test_merge_deep_strategy(self, pipeline_service: PipelineService):
        definition = self._build_merge_definition()
        # Switch to deep merge
        for step in definition.steps:
            if step.id == "merge":
                step.config["merge_strategy"] = "deep"
        pipeline_service.save_definition(definition)

        run_id = await pipeline_service.start_pipeline(
            initial_payload={
                "branch_a_data": {"meta": {"author": "Alice", "version": 1}},
                "branch_b_data": {"meta": {"editor": "Bob", "version": 2}},
            },
            definition_id=definition.id,
        )

        for _ in range(50):
            run = PipelineService._runs.get(run_id)
            if run and run.current_state in (PipelineState.COMPLETED, PipelineState.FAILED):
                break
            await asyncio.sleep(0.1)

        run = PipelineService._runs[run_id]
        assert run.current_state == PipelineState.COMPLETED

        merged = run.payload.get("merged", {})
        # Deep merge should preserve both author and editor under meta
        assert merged["meta"]["author"] == "Alice"
        assert merged["meta"]["editor"] == "Bob"
        # Last write wins for conflicting keys in deep merge
        assert merged["meta"]["version"] == 2


# ═══════════════════════════════════════════════════════════════════
# Deep Merge utility
# ═══════════════════════════════════════════════════════════════════


class TestDeepMerge:
    def test_shallow_override(self):
        result = PipelineService._deep_merge({"a": 1}, {"a": 2})
        assert result == {"a": 2}

    def test_nested_merge(self):
        base = {"x": {"a": 1, "b": 2}}
        override = {"x": {"b": 3, "c": 4}}
        result = PipelineService._deep_merge(base, override)
        assert result == {"x": {"a": 1, "b": 3, "c": 4}}

    def test_disjoint_keys(self):
        result = PipelineService._deep_merge({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}
