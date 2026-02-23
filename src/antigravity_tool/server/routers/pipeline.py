"""FastAPI router for the State Machine Pipeline — with definition CRUD."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from antigravity_tool.schemas.pipeline import PipelineRunCreate, PipelineResume
from antigravity_tool.schemas.pipeline_steps import (
    PipelineDefinition,
    PipelineDefinitionCreate,
    PipelineDefinitionResponse,
    PipelineStepDef,
    PipelineEdge,
    StepRegistryEntry,
    STEP_REGISTRY,
    DistillRequest,
)
from antigravity_tool.services.pipeline_service import PipelineService
from antigravity_tool.services.agent_dispatcher import AgentDispatcher
from antigravity_tool.server.deps import get_pipeline_service, get_agent_dispatcher
from antigravity_tool.templates.workflow_templates import WORKFLOW_TEMPLATES

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class PipelineGenerateRequest(BaseModel):
    """Request body for NL-to-DAG pipeline generation."""
    intent: str
    title: str


# ------------------------------------------------------------------
# Step Registry
# ------------------------------------------------------------------

@router.get("/steps/registry")
async def get_step_registry() -> List[StepRegistryEntry]:
    """Get the full step type registry (for the frontend step library)."""
    return [
        StepRegistryEntry(
            step_type=step_type.value,
            label=info["label"],
            description=info["description"],
            icon=info["icon"],
            category=info["category"].value,
            config_schema=info["config_schema"],
        )
        for step_type, info in STEP_REGISTRY.items()
    ]


# ------------------------------------------------------------------
# Pipeline Definition CRUD
# ------------------------------------------------------------------

@router.get("/definitions")
async def list_definitions(
    svc: PipelineService = Depends(get_pipeline_service),
) -> List[Dict[str, Any]]:
    """List all saved pipeline definitions."""
    defs = svc.list_definitions()
    return [
        {
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "step_count": len(d.steps),
            "created_at": d.created_at.isoformat(),
            "updated_at": d.updated_at.isoformat(),
        }
        for d in defs
    ]


@router.get("/definitions/{definition_id}")
async def get_definition(
    definition_id: str,
    svc: PipelineService = Depends(get_pipeline_service),
) -> PipelineDefinitionResponse:
    """Get a single pipeline definition."""
    d = svc.get_definition(definition_id)
    if not d:
        raise HTTPException(status_code=404, detail="Definition not found")
    return PipelineDefinitionResponse(
        id=d.id,
        name=d.name,
        description=d.description,
        steps=d.steps,
        edges=d.edges,
        created_at=d.created_at.isoformat(),
        updated_at=d.updated_at.isoformat(),
    )


@router.post("/definitions", status_code=201)
async def create_definition(
    body: PipelineDefinitionCreate,
    svc: PipelineService = Depends(get_pipeline_service),
) -> PipelineDefinitionResponse:
    """Save a new pipeline definition."""
    definition = PipelineDefinition(
        name=body.name,
        description=body.description,
        steps=body.steps,
        edges=body.edges,
    )
    saved = svc.save_definition(definition)
    return PipelineDefinitionResponse(
        id=saved.id,
        name=saved.name,
        description=saved.description,
        steps=saved.steps,
        edges=saved.edges,
        created_at=saved.created_at.isoformat(),
        updated_at=saved.updated_at.isoformat(),
    )


@router.put("/definitions/{definition_id}")
async def update_definition(
    definition_id: str,
    body: PipelineDefinitionCreate,
    svc: PipelineService = Depends(get_pipeline_service),
) -> PipelineDefinitionResponse:
    """Update an existing pipeline definition."""
    existing = svc.get_definition(definition_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Definition not found")

    existing.name = body.name
    existing.description = body.description
    existing.steps = body.steps
    existing.edges = body.edges
    saved = svc.save_definition(existing)
    return PipelineDefinitionResponse(
        id=saved.id,
        name=saved.name,
        description=saved.description,
        steps=saved.steps,
        edges=saved.edges,
        created_at=saved.created_at.isoformat(),
        updated_at=saved.updated_at.isoformat(),
    )


@router.delete("/definitions/{definition_id}")
async def delete_definition(
    definition_id: str,
    svc: PipelineService = Depends(get_pipeline_service),
) -> Dict[str, str]:
    """Delete a pipeline definition."""
    deleted = svc.delete_definition(definition_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Definition not found")
    return {"status": "deleted", "id": definition_id}


# ------------------------------------------------------------------
# Workflow Templates Library (Phase Next-D)
# ------------------------------------------------------------------

@router.get("/templates")
async def get_workflow_templates() -> list[dict]:
    """Return available workflow templates."""
    templates_list = []
    for t_id, t_data in WORKFLOW_TEMPLATES.items():
        t_copy = t_data.copy()
        t_copy["template_id"] = t_id
        templates_list.append(t_copy)
    return templates_list


@router.post("/templates/{template_id}/create")
async def create_from_template(
    template_id: str,
    svc: PipelineService = Depends(get_pipeline_service),
) -> PipelineDefinitionResponse:
    """Create a new PipelineDefinition from a template."""
    if template_id not in WORKFLOW_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    template = WORKFLOW_TEMPLATES[template_id]
    
    definition = PipelineDefinition(
        name=template["name"],
        description=template["description"],
        steps=[PipelineStepDef(**s) for s in template["steps"]],
        edges=[PipelineEdge(**e) for e in template["edges"]],
    )
    saved = svc.save_definition(definition)
    
    return PipelineDefinitionResponse(
        id=saved.id,
        name=saved.name,
        description=saved.description,
        steps=saved.steps,
        edges=saved.edges,
        created_at=saved.created_at.isoformat(),
        updated_at=saved.updated_at.isoformat(),
    )


# ------------------------------------------------------------------
# Recorded Workflow Distillation
# ------------------------------------------------------------------


@router.post("/definitions/distill", status_code=201)
async def distill_recorded_actions(
    body: DistillRequest,
    svc: PipelineService = Depends(get_pipeline_service),
) -> PipelineDefinitionResponse:
    """Distill recorded user actions into a reusable pipeline definition.

    Uses deterministic rule-based mapping instead of LLM generation.
    Specific text inputs are generalized into template variables.
    """
    try:
        definition = svc.distill_recorded_actions(
            actions=[a.model_dump() for a in body.actions],
            title=body.title,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    saved = svc.save_definition(definition)
    return PipelineDefinitionResponse(
        id=saved.id,
        name=saved.name,
        description=saved.description,
        steps=saved.steps,
        edges=saved.edges,
        created_at=saved.created_at.isoformat(),
        updated_at=saved.updated_at.isoformat(),
    )


# ------------------------------------------------------------------
# NL-to-DAG Pipeline Generation (Phase H Track 3)
# ------------------------------------------------------------------


@router.post("/definitions/generate", status_code=201)
async def generate_definition(
    body: PipelineGenerateRequest,
    svc: PipelineService = Depends(get_pipeline_service),
    agent_dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
) -> PipelineDefinitionResponse:
    """Generate a pipeline definition from a natural-language intent."""
    try:
        definition = await svc.generate_pipeline_from_nl(
            intent=body.intent,
            title=body.title,
            agent_dispatcher=agent_dispatcher,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    saved = svc.save_definition(definition)
    return PipelineDefinitionResponse(
        id=saved.id,
        name=saved.name,
        description=saved.description,
        steps=saved.steps,
        edges=saved.edges,
        created_at=saved.created_at.isoformat(),
        updated_at=saved.updated_at.isoformat(),
    )


# ------------------------------------------------------------------
# Pipeline Execution (extended)
# ------------------------------------------------------------------

@router.get("/runs")
async def list_pipeline_runs(
    state: str | None = None,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    """List pipeline runs, optionally filtered by state."""
    runs = list(PipelineService._runs.values())
    if state:
        runs = [r for r in runs if r.state.value == state]
    return [
        {
            "id": r.id,
            "definition_id": r.definition_id,
            "state": r.state.value,
            "current_step": r.current_step,
            "created_at": r.created_at.isoformat() if hasattr(r.created_at, 'isoformat') else str(r.created_at),
        }
        for r in runs
    ]


@router.post("/run", status_code=201)
async def start_pipeline_run(
    request: PipelineRunCreate,
    svc: PipelineService = Depends(get_pipeline_service),
):
    """Initialize a new pipeline run — optionally from a saved definition."""
    run_id = await svc.start_pipeline(
        request.initial_payload,
        definition_id=request.definition_id,
    )
    return {"run_id": run_id}


@router.get("/{run_id}/stream")
async def stream_pipeline_run(run_id: str):
    """Stream Server-Sent Events (SSE) representing pipeline state changes."""
    return EventSourceResponse(PipelineService.stream_pipeline(run_id))


class ModelOverrideRequest(BaseModel):
    model: str

@router.patch("/{run_id}/steps/{step_id}/model")
async def override_step_model(
    run_id: str,
    step_id: str,
    request: ModelOverrideRequest,
    svc: PipelineService = Depends(get_pipeline_service),
):
    """Override the language model for a specific step before it resumes."""
    try:
        svc.set_step_model_override(run_id, step_id, request.model)
        return {"status": "ok", "run_id": run_id, "step_id": step_id, "model": request.model}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{run_id}/resume")
async def resume_pipeline_run(run_id: str, request: PipelineResume):
    """Resume a paused pipeline run with user edits/updates."""
    try:
        await PipelineService.resume_pipeline(run_id, request.payload)
        return {"status": "resumed", "run_id": run_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
