"""World router -- world settings and building prompts."""

from fastapi import APIRouter, Depends

from showrunner_tool.server.api_schemas import PromptResponse
from showrunner_tool.server.deps import get_world_service
from showrunner_tool.services.world_service import WorldService

router = APIRouter(prefix="/api/v1/world", tags=["world"])


@router.get("/")
async def get_world(svc: WorldService = Depends(get_world_service)):
    settings = svc.get_settings()
    if not settings:
        return {"status": "empty", "message": "No world settings. Run 'showrunner world build'."}
    return settings.model_dump(mode="json")


@router.post("/build/prompt", response_model=PromptResponse)
async def compile_build_prompt(svc: WorldService = Depends(get_world_service)):
    result = svc.compile_build_prompt()
    return PromptResponse(
        prompt_text=result.prompt_text,
        step=result.step,
        template_used=result.template_used,
        context_keys=result.context_keys,
    )
