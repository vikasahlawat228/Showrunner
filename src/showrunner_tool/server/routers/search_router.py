"""Search REST API router — full-text search across all entities.

Endpoints:
  GET /api/v1/search          — Search all entities
  GET /api/v1/search/suggestions — Autocomplete suggestions
"""

from __future__ import annotations

import re
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/search", tags=["search"])


class SearchResult(BaseModel):
    """Single search result."""
    id: str
    name: str
    type: str  # 'character', 'location', 'scene', 'fragment', 'research', etc.
    preview: str
    score: float
    file_path: Optional[str] = None


class SearchResponse(BaseModel):
    """Search response with results."""
    query: str
    results: list[SearchResult]
    total_count: int
    execution_time_ms: float


@router.get("/")
async def search(
    q: str,
    types: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    request: Request = None,
) -> SearchResponse:
    """Search across all entities.

    Query parameters:
      q: Search query (required)
      types: Comma-separated entity types to search (e.g., 'character,scene')
      limit: Number of results to return (default 20)
      offset: Result offset for pagination (default 0)
    """
    start_time = time.time()

    try:
        kg_service = request.app.state.kg_service
        container_repo = request.app.state.container_repo

        if not q or len(q) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

        # Parse types filter
        search_types = []
        if types:
            search_types = [t.strip() for t in types.split(",")]

        # Search using knowledge graph
        results = []

        # Try semantic search first (if ChromaDB available)
        try:
            semantic_results = kg_service.semantic_search(q, top_k=limit * 2)
            for result in semantic_results:
                container_id = result.get("id")
                name = result.get("name", container_id)
                container_type = result.get("container_type", "unknown")

                # Filter by type if specified
                if search_types and container_type not in search_types:
                    continue

                # Create preview from attributes
                attrs = result.get("attributes", {})
                preview_text = attrs.get("prose", attrs.get("description", ""))[:100]
                if not preview_text:
                    preview_text = str(attrs)[:100]

                results.append(
                    SearchResult(
                        id=container_id,
                        name=name,
                        type=container_type,
                        preview=preview_text,
                        score=result.get("similarity_score", 0.8),
                    )
                )
        except Exception as e:
            # Fall back to keyword search
            pass

        # Keyword search if no semantic results or to supplement
        if not results or len(results) < limit:
            keyword_pattern = re.compile(re.escape(q), re.IGNORECASE)

            # Search all containers
            all_containers = kg_service.find_containers()

            for container in all_containers:
                # Filter by type if specified
                container_type = container.get("container_type", "unknown")
                if search_types and container_type not in search_types:
                    continue

                name = container.get("name", "")
                attrs = container.get("attributes", {})

                # Calculate match score
                score = 0.0
                if keyword_pattern.search(name):
                    score += 0.8  # Name match is strong
                if keyword_pattern.search(str(attrs)):
                    score += 0.3  # Attribute match is weaker

                if score > 0:
                    # Create preview
                    preview_text = attrs.get("prose", attrs.get("description", ""))[:100]
                    if not preview_text:
                        preview_text = f"({container_type})"

                    # Check if already in results (from semantic search)
                    existing = [r for r in results if r.id == container["id"]]
                    if existing:
                        # Update score with keyword match
                        existing[0].score = max(existing[0].score, score)
                    else:
                        results.append(
                            SearchResult(
                                id=container["id"],
                                name=name,
                                type=container_type,
                                preview=preview_text,
                                score=score,
                            )
                        )

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)

        # Apply pagination
        paginated_results = results[offset : offset + limit]

        execution_time_ms = (time.time() - start_time) * 1000

        return SearchResponse(
            query=q,
            results=paginated_results,
            total_count=len(results),
            execution_time_ms=execution_time_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_suggestions(
    q: str,
    limit: int = 10,
    request: Request = None,
) -> dict:
    """Get autocomplete suggestions for search.

    Returns character names, locations, and other common entities.
    """
    try:
        kg_service = request.app.state.kg_service

        if not q or len(q) < 2:
            return {"suggestions": []}

        # Get containers that match the query prefix
        pattern = re.compile(f"^{re.escape(q)}", re.IGNORECASE)
        all_containers = kg_service.find_containers()

        suggestions = set()

        for container in all_containers:
            name = container.get("name", "")
            if pattern.search(name) and len(suggestions) < limit:
                suggestions.add(name)

        return {"suggestions": sorted(list(suggestions))}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_available_types(request: Request = None) -> dict:
    """Get all available entity types that can be searched."""
    try:
        kg_service = request.app.state.kg_service

        # Scan all containers and collect unique types
        types = set()
        all_containers = kg_service.find_containers()

        for container in all_containers:
            container_type = container.get("container_type", "unknown")
            types.add(container_type)

        return {
            "types": sorted(list(types)),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
