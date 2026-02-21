"""Research router -- query execution and research library."""

from fastapi import APIRouter, Depends, HTTPException

from antigravity_tool.server.api_schemas import (
    ResearchQueryRequest,
    ResearchResultResponse,
    ResearchLibraryResponse,
)
from antigravity_tool.services.research_service import ResearchService
from antigravity_tool.server.deps import get_research_service

router = APIRouter(prefix="/api/v1/research", tags=["research"])


@router.post("/query", response_model=ResearchResultResponse, status_code=201)
async def research_query(
    body: ResearchQueryRequest,
    svc: ResearchService = Depends(get_research_service),
):
    """Execute a research query via the research agent skill."""
    result = await svc.execute_research(query=body.query)
    if result is None:
        raise HTTPException(status_code=500, detail="Research agent failed to produce results")
    return ResearchResultResponse(**result)


@router.get("/library", response_model=ResearchLibraryResponse)
async def research_library(
    svc: ResearchService = Depends(get_research_service),
):
    """List all research results from the library."""
    items = svc.list_research()
    return ResearchLibraryResponse(
        items=[ResearchResultResponse(**item) for item in items],
        total=len(items),
    )


@router.get("/library/{research_id}", response_model=ResearchResultResponse)
async def get_research(
    research_id: str,
    svc: ResearchService = Depends(get_research_service),
):
    """Get a single research result by ID."""
    result = svc.get_research(research_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Research not found")
    return ResearchResultResponse(**result)
