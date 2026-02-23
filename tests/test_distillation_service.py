"""Test suite for PipelineService.distill_recorded_actions().

Covers:
  1. Single slash command → prompt_template + llm_generate pipeline
  2. Multi-action sequence → multi-step pipeline with edges
  3. Text generalization (specific text replaced with template variables)
  4. Approval actions → human checkpoint steps
  5. Empty actions list → ValueError
  6. Mixed action types in a realistic workflow
"""

import tempfile
from pathlib import Path

import pytest

from antigravity_tool.schemas.pipeline_steps import (
    PipelineDefinition,
    PipelineStepDef,
    PipelineEdge,
    StepType,
)
from antigravity_tool.repositories.container_repo import ContainerRepository
from antigravity_tool.repositories.event_sourcing_repo import EventService
from antigravity_tool.services.pipeline_service import PipelineService


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
# Tests
# ═══════════════════════════════════════════════════════════════════


class TestDistillRecordedActions:
    """Test the deterministic distillation of recorded actions."""

    def test_empty_actions_raises(self, pipeline_service: PipelineService):
        """An empty action list should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot distill an empty action list"):
            pipeline_service.distill_recorded_actions([], "Empty Test")

    def test_single_slash_command(self, pipeline_service: PipelineService):
        """A single slash command creates a prompt_template + llm_generate pair."""
        actions = [
            {
                "type": "slash_command",
                "description": "Invoked /brainstorm on selected text",
                "payload": {
                    "command": "brainstorm",
                    "selected_text": "The dark knight falls.",
                },
            }
        ]

        definition = pipeline_service.distill_recorded_actions(actions, "Brainstorm Pipeline")

        assert definition.name == "Brainstorm Pipeline"
        assert len(definition.steps) == 2
        assert definition.steps[0].step_type == StepType.PROMPT_TEMPLATE
        assert definition.steps[1].step_type == StepType.LLM_GENERATE
        assert len(definition.edges) == 1
        assert definition.edges[0].source == definition.steps[0].id
        assert definition.edges[0].target == definition.steps[1].id

    def test_command_prompt_generalization(self, pipeline_service: PipelineService):
        """Specific text should be generalized into {{input_text}} template variable."""
        actions = [
            {
                "type": "slash_command",
                "description": "Invoked /expand",
                "payload": {
                    "command": "expand",
                    "selected_text": "Very specific scene text here.",
                },
            }
        ]

        definition = pipeline_service.distill_recorded_actions(actions, "Expand Pipeline")

        # The prompt template should use {{input_text}} not the specific text
        prompt_config = definition.steps[0].config
        assert "{{input_text}}" in prompt_config["template_inline"]
        assert "Very specific scene text here." not in prompt_config["template_inline"]

    def test_multi_action_sequence(self, pipeline_service: PipelineService):
        """Multiple actions create connected steps with edges."""
        actions = [
            {
                "type": "text_selection",
                "description": "Selected text",
                "payload": {},
            },
            {
                "type": "slash_command",
                "description": "Invoked /brainstorm",
                "payload": {"command": "brainstorm"},
            },
            {
                "type": "save",
                "description": "Saved output",
                "payload": {},
            },
        ]

        definition = pipeline_service.distill_recorded_actions(actions, "Multi-Step")

        # text_selection → gather_buckets
        # slash_command → prompt_template + llm_generate
        # save → save_to_bucket
        # Total: 4 steps
        assert len(definition.steps) == 4
        assert definition.steps[0].step_type == StepType.GATHER_BUCKETS
        assert definition.steps[1].step_type == StepType.PROMPT_TEMPLATE
        assert definition.steps[2].step_type == StepType.LLM_GENERATE
        assert definition.steps[3].step_type == StepType.SAVE_TO_BUCKET

        # Check edges form a chain
        assert len(definition.edges) >= 3

    def test_approval_actions(self, pipeline_service: PipelineService):
        """Approval actions create approve_output checkpoint steps."""
        actions = [
            {
                "type": "slash_command",
                "description": "Invoked /expand",
                "payload": {"command": "expand"},
            },
            {
                "type": "approval",
                "description": "Approved the output",
                "payload": {"decision": "approve"},
            },
        ]

        definition = pipeline_service.distill_recorded_actions(actions, "With Approval")

        # slash_command → 2 steps + approval → 1 step = 3 steps
        assert len(definition.steps) == 3
        assert definition.steps[2].step_type == StepType.APPROVE_OUTPUT

    def test_chat_message_action(self, pipeline_service: PipelineService):
        """Chat messages create an LLM generation step."""
        actions = [
            {
                "type": "chat_message",
                "description": "Make this scene more dramatic",
                "payload": {"message": "Make this scene more dramatic"},
            },
        ]

        definition = pipeline_service.distill_recorded_actions(actions, "Chat Pipeline")

        assert len(definition.steps) == 1
        assert definition.steps[0].step_type == StepType.LLM_GENERATE
        assert "Chat:" in definition.steps[0].label

    def test_entity_mention_action(self, pipeline_service: PipelineService):
        """Entity mentions create semantic search steps."""
        actions = [
            {
                "type": "entity_mention",
                "description": "Mentioned character",
                "payload": {"entity_name": "Marcus"},
            },
        ]

        definition = pipeline_service.distill_recorded_actions(actions, "Entity Pipeline")

        assert len(definition.steps) == 1
        assert definition.steps[0].step_type == StepType.SEMANTIC_SEARCH
        assert "Marcus" in definition.steps[0].label

    def test_option_select_action(self, pipeline_service: PipelineService):
        """Option selection creates a review_prompt checkpoint."""
        actions = [
            {
                "type": "option_select",
                "description": "Selected brainstorm option #2",
                "payload": {"option_index": 2},
            },
        ]

        definition = pipeline_service.distill_recorded_actions(actions, "Option Pipeline")

        assert len(definition.steps) == 1
        assert definition.steps[0].step_type == StepType.REVIEW_PROMPT

    def test_realistic_workflow(self, pipeline_service: PipelineService):
        """A realistic multi-step workflow with mixed action types."""
        actions = [
            {
                "type": "text_selection",
                "description": "Selected scene text",
                "payload": {},
            },
            {
                "type": "slash_command",
                "description": "Invoked /brainstorm",
                "payload": {"command": "brainstorm", "selected_text": "A hero's journey begins..."},
            },
            {
                "type": "option_select",
                "description": "Selected option #1",
                "payload": {"option_index": 1},
            },
            {
                "type": "slash_command",
                "description": "Invoked /expand",
                "payload": {"command": "expand", "selected_text": "The chosen path."},
            },
            {
                "type": "approval",
                "description": "Approved final output",
                "payload": {"decision": "approve"},
            },
            {
                "type": "save",
                "description": "Saved to project",
                "payload": {},
            },
        ]

        definition = pipeline_service.distill_recorded_actions(actions, "Full Workflow")

        # text_selection: 1 + brainstorm: 2 + option_select: 1 + expand: 2 + approval: 1 + save: 1 + final_review: 1 = 9
        assert len(definition.steps) == 9
        assert "Recorded workflow" in definition.description

        # First step should be gather context
        assert definition.steps[0].step_type == StepType.GATHER_BUCKETS

        # Last step should be final review (since session had approvals)
        assert definition.steps[-1].step_type == StepType.APPROVE_OUTPUT
        assert definition.steps[-1].label == "Final Review"

        # Second-to-last should be save
        assert definition.steps[-2].step_type == StepType.SAVE_TO_BUCKET

        # All steps should be connected (at least n-1 edges for n steps)
        assert len(definition.edges) >= 8

    def test_unknown_action_types_skipped(self, pipeline_service: PipelineService):
        """Unknown action types are skipped gracefully."""
        actions = [
            {
                "type": "slash_command",
                "description": "Invoked /brainstorm",
                "payload": {"command": "brainstorm"},
            },
            {
                "type": "unknown_magic_action",
                "description": "Something weird",
                "payload": {},
            },
        ]

        definition = pipeline_service.distill_recorded_actions(actions, "With Unknown")

        # Only the slash command should produce steps
        assert len(definition.steps) == 2
        assert definition.steps[0].step_type == StepType.PROMPT_TEMPLATE

    def test_positions_are_laid_out(self, pipeline_service: PipelineService):
        """Steps should have incrementing x positions for visual layout."""
        actions = [
            {"type": "text_selection", "description": "", "payload": {}},
            {"type": "slash_command", "description": "", "payload": {"command": "expand"}},
            {"type": "save", "description": "", "payload": {}},
        ]

        definition = pipeline_service.distill_recorded_actions(actions, "Layout Test")

        x_positions = [s.position["x"] for s in definition.steps]
        # Positions should be strictly increasing
        for i in range(1, len(x_positions)):
            assert x_positions[i] > x_positions[i - 1]

    def test_approval_in_session_adds_final_checkpoint(self, pipeline_service: PipelineService):
        """If session had approvals, a final checkpoint is added if last step isn't one."""
        actions = [
            {
                "type": "approval",
                "description": "Approved something",
                "payload": {},
            },
            {
                "type": "slash_command",
                "description": "Invoked /expand",
                "payload": {"command": "expand"},
            },
        ]

        definition = pipeline_service.distill_recorded_actions(actions, "Approval Final")

        # Should have: approval + prompt_template + llm_generate + final_approve = 4
        assert len(definition.steps) == 4
        assert definition.steps[-1].step_type == StepType.APPROVE_OUTPUT
        assert definition.steps[-1].label == "Final Review"
