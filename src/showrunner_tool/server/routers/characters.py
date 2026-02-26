"""Characters router -- character CRUD and prompt compilation."""

from fastapi import APIRouter, Depends, HTTPException

from showrunner_tool.server.api_schemas import (
    CharacterSummary,
    CreateCharacterRequest,
    PromptResponse,
    CharacterProgression,
    ProgressionCreateRequest,
    ResolvedDNAResponse,
)
from showrunner_tool.server.deps import get_character_service, get_container_repo
from showrunner_tool.services.character_service import CharacterService
from showrunner_tool.repositories.container_repo import ContainerRepository
from typing import Any
import uuid

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


# ── Character Progressions ──────────────────────────────────────────────

@router.get("/{name}/progressions", response_model=list[CharacterProgression])
async def list_progressions(
    name: str,
    svc: CharacterService = Depends(get_character_service),
    repo: ContainerRepository = Depends(get_container_repo),
):
    char = svc.get(name)
    if not char:
        raise HTTPException(status_code=404, detail=f"Character '{name}' not found")
    
    container = repo.get_container(char.id)
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")

    progressions = container.attributes.get("progressions", [])
    
    # Sort by chapter
    progressions = sorted(progressions, key=lambda x: x.get("chapter", 0))
    
    return [CharacterProgression(**p) for p in progressions]


@router.post("/{name}/progressions", response_model=CharacterProgression)
async def add_progression(
    name: str,
    req: ProgressionCreateRequest,
    svc: CharacterService = Depends(get_character_service),
    repo: ContainerRepository = Depends(get_container_repo),
):
    char = svc.get(name)
    if not char:
        raise HTTPException(status_code=404, detail=f"Character '{name}' not found")

    container = repo.get_container(char.id)
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")

    progressions = container.attributes.get("progressions", [])
    
    prog_id = f"prog_{uuid.uuid4().hex[:8]}"
    new_prog = {
        "id": prog_id,
        "chapter": req.chapter,
        "label": req.label,
        "changes": req.changes,
        "notes": req.notes,
    }
    
    progressions.append(new_prog)
    container.attributes["progressions"] = progressions
    repo.save_container(container)
    
    return CharacterProgression(**new_prog)


@router.put("/{name}/progressions/{progression_id}", response_model=CharacterProgression)
async def update_progression(
    name: str,
    progression_id: str,
    req: ProgressionCreateRequest,
    svc: CharacterService = Depends(get_character_service),
    repo: ContainerRepository = Depends(get_container_repo),
):
    char = svc.get(name)
    if not char:
        raise HTTPException(status_code=404, detail=f"Character '{name}' not found")

    container = repo.get_container(char.id)
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")

    progressions = container.attributes.get("progressions", [])
    
    for i, p in enumerate(progressions):
        if p.get("id") == progression_id:
            progressions[i].update({
                "chapter": req.chapter,
                "label": req.label,
                "changes": req.changes,
                "notes": req.notes,
            })
            container.attributes["progressions"] = progressions
            repo.save_container(container)
            return CharacterProgression(**progressions[i])
            
    raise HTTPException(status_code=404, detail=f"Progression '{progression_id}' not found")


@router.delete("/{name}/progressions/{progression_id}")
async def delete_progression(
    name: str,
    progression_id: str,
    svc: CharacterService = Depends(get_character_service),
    repo: ContainerRepository = Depends(get_container_repo),
):
    char = svc.get(name)
    if not char:
        raise HTTPException(status_code=404, detail=f"Character '{name}' not found")

    container = repo.get_container(char.id)
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")

    progressions = container.attributes.get("progressions", [])
    filtered = [p for p in progressions if p.get("id") != progression_id]
    
    if len(filtered) == len(progressions):
        raise HTTPException(status_code=404, detail=f"Progression '{progression_id}' not found")
        
    container.attributes["progressions"] = filtered
    repo.save_container(container)
    return {"status": "deleted"}


def _deep_merge(target: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge source dict into target dict."""
    for key, value in source.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            target[key] = _deep_merge(target[key], value)
        else:
            target[key] = value
    return target


@router.get("/{name}/dna-at-chapter/{chapter}", response_model=ResolvedDNAResponse)
async def get_dna_at_chapter(
    name: str,
    chapter: int,
    svc: CharacterService = Depends(get_character_service),
    repo: ContainerRepository = Depends(get_container_repo),
):
    char = svc.get(name)
    if not char:
        raise HTTPException(status_code=404, detail=f"Character '{name}' not found")
        
    container = repo.get_container(char.id)
    
    if char.dna:
        base_dna = char.dna.model_dump(mode="json")
    else:
        base_dna = {}

    progressions = container.attributes.get("progressions", []) if container else []
    
    # Sort and filter progressions
    valid_progressions = sorted(
        [p for p in progressions if p.get("chapter", 0) <= chapter],
        key=lambda x: x.get("chapter", 0)
    )
    
    resolved_dna = base_dna.copy()
    applied_labels = []
    
    for prog in valid_progressions:
        changes = prog.get("changes", {})
        resolved_dna = _deep_merge(resolved_dna, changes)
        applied_labels.append(prog.get("label", ""))
        
    return ResolvedDNAResponse(
        character_id=char.id,
        character_name=char.name,
        chapter=chapter,
        resolved_dna=resolved_dna,
        progressions_applied=applied_labels
    )

