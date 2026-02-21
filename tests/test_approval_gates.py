"""Phase G Track 4 — Approval Gates & UI backend tests."""

import asyncio
from pathlib import Path

import pytest

from antigravity_tool.schemas.pipeline_steps import (
    PipelineDefinition,
    PipelineStepDef,
    PipelineEdge,
    StepType,
)
from antigravity_tool.schemas.pipeline import PipelineState
from antigravity_tool.repositories.container_repo import ContainerRepository
from antigravity_tool.repositories.event_sourcing_repo import EventService
from antigravity_tool.services.pipeline_service import PipelineService
from antigravity_tool.schemas.model_config import ModelConfig, ProjectModelConfig

class DummyModelConfigRegistry:
    def resolve(self, step_config, bucket_model_preference, agent_id):
        return ModelConfig(model="dummy-default-model", temperature=0.5, max_tokens=100)

@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / "schemas").mkdir()
    (tmp_path / "antigravity.yaml").write_text(
        "name: Test Project\nversion: 0.1.0\ndefault_model: dummy-default-model\n"
    )
    return tmp_path

@pytest.fixture
def pipeline_service(tmp_project: Path) -> PipelineService:
    container_repo = ContainerRepository(tmp_project)
    event_service = EventService(tmp_project / "events.db")
    svc = PipelineService(container_repo, event_service)
    PipelineService.set_model_config_registry(DummyModelConfigRegistry())
    return svc

def _build_approval_pipeline() -> PipelineDefinition:
    return PipelineDefinition(
        name="Approval Test",
        steps=[
            PipelineStepDef(
                id="init",
                step_type=StepType.PROMPT_TEMPLATE,
                label="Init",
                config={"template_inline": "hello"},
            ),
            PipelineStepDef(
                id="generate",
                step_type=StepType.LLM_GENERATE,
                label="Generate",
                config={"model": "default-model"},
            ),
            PipelineStepDef(
                id="review",
                step_type=StepType.REVIEW_PROMPT,
                label="Review",
                config={},
            ),
        ],
        edges=[
            PipelineEdge(source="init", target="generate"),
            PipelineEdge(source="generate", target="review"),
        ],
    )

@pytest.mark.asyncio
async def test_resume_with_refine_instructions(pipeline_service: PipelineService):
    definition = _build_approval_pipeline()
    pipeline_service.save_definition(definition)

    run_id = await pipeline_service.start_pipeline(
        initial_payload={"prompt_text": "start"},
        definition_id=definition.id,
    )

    # Wait for PAUSED_FOR_USER
    for _ in range(50):
        run = PipelineService._runs.get(run_id)
        if run and run.current_state == PipelineState.PAUSED_FOR_USER:
            break
        await asyncio.sleep(0.1)

    run = PipelineService._runs[run_id]
    assert run.current_state == PipelineState.PAUSED_FOR_USER
    
    # Send refine instructions
    await PipelineService.resume_pipeline(run_id, {
        "refine_instructions": "make it spicier"
    })

    # Wait for it to loop back to generate and pause again
    for _ in range(50):
        run = PipelineService._runs.get(run_id)
        # Should complete a second generate, and then hit review again
        # The prompt_text should have changed
        if run and run.current_state == PipelineState.PAUSED_FOR_USER:
            if "make it spicier" in run.payload.get("prompt_text", ""):
                break
        await asyncio.sleep(0.1)

    run = PipelineService._runs[run_id]
    assert "make it spicier" in run.payload["prompt_text"]

@pytest.mark.asyncio
async def test_resume_with_model_override(pipeline_service: PipelineService):
    definition = _build_approval_pipeline()
    pipeline_service.save_definition(definition)

    run_id = await pipeline_service.start_pipeline(
        initial_payload={"prompt_text": "start"},
        definition_id=definition.id,
    )

    # Wait for PAUSED_FOR_USER
    for _ in range(50):
        run = PipelineService._runs.get(run_id)
        if run and run.current_state == PipelineState.PAUSED_FOR_USER:
            break
        await asyncio.sleep(0.1)

    run = PipelineService._runs[run_id]
    assert run.current_state == PipelineState.PAUSED_FOR_USER
    
    # Provide a model override and refine instructions
    await PipelineService.resume_pipeline(run_id, {
        "refine_instructions": "use a specific model",
        "model": "my-cool-custom-model"
    })

    # Wait for it to hit PAUSED_FOR_USER again
    for _ in range(50):
        run = PipelineService._runs.get(run_id)
        if run and run.current_state == PipelineState.PAUSED_FOR_USER:
            if "use a specific model" in run.payload.get("prompt_text", ""):
                break
        await asyncio.sleep(0.1)

    run = PipelineService._runs[run_id]
    # The generated_text should reflect what LLM_GENERATE produced or the resolved_model should be tracked
    assert run.payload.get("resolved_model") == "my-cool-custom-model"
