"""Writing router — Zen Mode REST endpoints for fragments and entity detection."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from antigravity_tool.schemas.fragment import (
    ContainerContextResponse,
    EntityDetectionRequest,
    EntityDetectionResponse,
    FragmentCreateRequest,
    FragmentResponse,
)
from antigravity_tool.services.writing_service import WritingService
from antigravity_tool.server.deps import get_writing_service

router = APIRouter(prefix="/api/v1/writing", tags=["writing"])


@router.post("/fragments", response_model=FragmentResponse)
async def save_fragment(
    body: FragmentCreateRequest,
    svc: WritingService = Depends(get_writing_service),
):
    """Save a writing fragment and optionally auto-detect entities."""
    fragment, detected = svc.save_fragment(
        text=body.text,
        title=body.title,
        scene_id=body.scene_id,
        chapter=body.chapter,
        branch_id=body.branch_id,
        associated_containers=body.associated_containers,
        metadata=body.metadata,
    )

    return FragmentResponse(
        id=fragment.id,
        text=fragment.text,
        title=fragment.title,
        associated_containers=fragment.associated_containers,
        detected_entities=detected,
        word_count=fragment.metadata.get("word_count", 0),
    )


@router.post("/detect-entities", response_model=EntityDetectionResponse)
async def detect_entities(
    body: EntityDetectionRequest,
    svc: WritingService = Depends(get_writing_service),
):
    """Detect entity mentions in text using LLM-based analysis."""
    entities = svc.detect_entities(body.text)
    return EntityDetectionResponse(entities=entities)


@router.get("/context/{container_id}", response_model=ContainerContextResponse)
async def get_container_context(
    container_id: str,
    svc: WritingService = Depends(get_writing_service),
):
    """Get a formatted context summary for a container (used by @-mention popover)."""
    result = svc.get_context_summary(container_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
    return result


from fastapi import Query
from antigravity_tool.server.deps import get_knowledge_graph_service
from antigravity_tool.services.knowledge_graph_service import KnowledgeGraphService

@router.get("/semantic-search")
async def semantic_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(8, ge=1, le=20),
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Semantic search for containers using vector similarity.

    Returns enriched results with container metadata, ordered by relevance.
    Used by Zen Mode @mentions for smarter entity suggestions.
    """
    results = kg_service.semantic_search(q, limit=limit)
    return results


@router.get("/search")
async def search_containers(
    q: str = "",
    limit: int = 10,
    svc: WritingService = Depends(get_writing_service),
) -> List[Dict[str, Any]]:
    """Fuzzy search containers by name for @-mention autocomplete."""
    if not q.strip():
        return []
    return svc.search_containers(q.strip(), limit=limit)
