"""Director router -- AI director task execution and agent dispatch."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from antigravity_tool.server.api_schemas import (
    AgentResultResponse,
    AgentSkillSummary,
    DirectorActRequest,
    DirectorResultResponse,
    DispatchRequest,
)
from antigravity_tool.server.deps import get_agent_dispatcher, get_director_service, get_container_repo
from antigravity_tool.services.agent_dispatcher import AgentDispatcher
from antigravity_tool.services.director_service import DirectorService
from antigravity_tool.schemas.container import GenericContainer
from antigravity_tool.repositories.container_repo import ContainerRepository

router = APIRouter(prefix="/api/v1/director", tags=["director"])


# ── Existing Endpoints (unchanged) ──────────────────────────────


@router.post("/act", response_model=DirectorResultResponse)
async def director_act(
    req: DirectorActRequest = DirectorActRequest(),
    svc: DirectorService = Depends(get_director_service),
):
    result = svc.act(step_override=req.step_override)
    return DirectorResultResponse(
        step_executed=result.step_executed,
        status=result.status,
        files_created=result.files_created,
        files_modified=result.files_modified,
        next_step=result.next_step,
        message=result.message,
    )


@router.get("/status")
async def director_status(svc: DirectorService = Depends(get_director_service)):
    return {"current_step": svc.get_current_step()}


# ── Agent Dispatch Endpoints ─────────────────────────────────────


@router.post("/dispatch", response_model=AgentResultResponse | DirectorResultResponse)
async def director_dispatch(
    req: DispatchRequest,
    dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
    director_svc: DirectorService = Depends(get_director_service),
):
    """Route a user intent to a specialized agent skill and execute it.

    Routing strategy:
    1. Try AgentDispatcher keyword matching first
    2. If no keyword match, try LLM-based classification
    3. If still no match, fall back to DirectorService.act()

    Returns AgentResultResponse if a skill handled it,
    or DirectorResultResponse if it fell through to the Director workflow.
    """
    # Try agent dispatch first
    agent_result = await dispatcher.route_and_execute(
        intent=req.intent,
        context=req.context or None,
    )

    if agent_result is not None:
        return AgentResultResponse(
            skill_used=agent_result.skill_used,
            response=agent_result.response,
            actions=agent_result.actions,
            success=agent_result.success,
            error=agent_result.error,
            model_used=agent_result.model_used,
            context_used=agent_result.context_used,
        )

    # No agent skill matched -- fall back to DirectorService
    director_result = director_svc.act()
    return DirectorResultResponse(
        step_executed=director_result.step_executed,
        status=director_result.status,
        files_created=director_result.files_created,
        files_modified=director_result.files_modified,
        next_step=director_result.next_step,
        message=director_result.message,
    )


@router.get("/skills", response_model=list[AgentSkillSummary])
async def list_agent_skills(
    dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
):
    """List all available agent skills and their keywords."""
    return [
        AgentSkillSummary(**skill_info)
        for skill_info in dispatcher.list_skills()
    ]


# ── Brainstorm Canvas Endpoints ───────────────────────────────────

class BrainstormSuggestRequest(BaseModel):
    cards: list[dict]
    intent: str = ""

class BrainstormCardSaveRequest(BaseModel):
    text: str
    position_x: float
    position_y: float
    color: str | None = None
    tags: list[str] | None = None

@router.post("/brainstorm/suggest-connections")
async def suggest_connections(
    req: BrainstormSuggestRequest,
    dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
):
    """AI analyzes idea cards and suggests connections/new ideas."""
    cards_text = "\n".join(
        f"- ID: {c.get('id', 'unknown')}, Text: {c.get('text', '')}"
        for c in req.cards
    )
    
    intent = req.intent if req.intent else "Connect these brainstorm cards and suggest missing ideas."
    context = {"cards": cards_text}

    # Execute brainstorm_agent skill
    agent_result = await dispatcher.route_and_execute(
        intent=f"brainstorm: {intent}",
        context=context,
    )

    if not agent_result or not agent_result.success:
        raise HTTPException(status_code=500, detail="Failed to suggest connections.")

    # Try to extract the first action as our structured response
    if agent_result.actions:
        return agent_result.actions[0]
        
    return {
        "suggested_edges": [],
        "suggested_cards": [],
        "themes": []
    }


@router.post("/brainstorm/save-card")
async def save_brainstorm_card(
    req: BrainstormCardSaveRequest,
    container_repo: ContainerRepository = Depends(get_container_repo),
):
    """Save an idea card as a GenericContainer."""
    attributes = {
        "text": req.text,
        "position_x": req.position_x,
        "position_y": req.position_y,
    }
    if req.color:
        attributes["color"] = req.color
        
    tags = req.tags if req.tags else []

    card = GenericContainer(
        container_type="idea_card",
        name=req.text[:20] + "..." if len(req.text) > 20 else req.text,
        attributes=attributes,
        tags=tags,
    )
    saved = container_repo.save_container(card)
    return saved.model_dump()


@router.get("/brainstorm/cards")
async def get_brainstorm_cards(
    container_repo: ContainerRepository = Depends(get_container_repo),
):
    """List all idea_card containers."""
    return [c.model_dump() for c in container_repo.list_by_type("idea_card")]


@router.delete("/brainstorm/cards/{card_id}")
async def delete_brainstorm_card(
    card_id: str,
    container_repo: ContainerRepository = Depends(get_container_repo),
):
    """Delete a brainstorm card."""
    if not container_repo.delete_container(card_id):
        raise HTTPException(status_code=404, detail="Card not found")
    return {"status": "deleted", "id": card_id}
