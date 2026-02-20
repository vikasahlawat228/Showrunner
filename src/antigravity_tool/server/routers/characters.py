"""Characters router -- character CRUD and prompt compilation."""

from fastapi import APIRouter, Depends, HTTPException

from antigravity_tool.server.api_schemas import (
    CharacterSummary,
    CreateCharacterRequest,
    PromptResponse,
)
from antigravity_tool.server.deps import get_character_service
from antigravity_tool.services.character_service import CharacterService

router = APIRouter(prefix="/api/v1/characters", tags=["characters"])


@router.get("/", response_model=list[CharacterSummary])
async def list_characters(svc: CharacterService = Depends(get_character_service)):
    chars = svc.list_all(filter_secrets=False)
    return [
        CharacterSummary(
            id=c.id,
            name=c.name,
            role=c.role.value,
            one_line=c.one_line,
            has_dna=bool(c.dna.face.face_shape),
        )
        for c in chars
    ]


@router.get("/{name}")
async def get_character(name: str, svc: CharacterService = Depends(get_character_service)):
    char = svc.get(name)
    if not char:
        raise HTTPException(status_code=404, detail=f"Character '{name}' not found")
    return char.model_dump(mode="json")


@router.post("/prompt", response_model=PromptResponse)
async def compile_create_prompt(
    req: CreateCharacterRequest,
    svc: CharacterService = Depends(get_character_service),
):
    result = svc.compile_create_prompt(req.name, req.role)
    return PromptResponse(
        prompt_text=result.prompt_text,
        step=result.step,
        template_used=result.template_used,
        context_keys=result.context_keys,
    )


@router.post("/{name}/dna/prompt", response_model=PromptResponse)
async def compile_dna_prompt(
    name: str,
    svc: CharacterService = Depends(get_character_service),
):
    result = svc.compile_dna_prompt(name)
    return PromptResponse(
        prompt_text=result.prompt_text,
        step=result.step,
        template_used=result.template_used,
        context_keys=result.context_keys,
    )
