"""Graph router -- fetches all containers and relationships for React Flow."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query

from antigravity_tool.server.deps import get_knowledge_graph_service
from antigravity_tool.services.knowledge_graph_service import KnowledgeGraphService

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


@router.get("/")
async def get_graph(
    svc: KnowledgeGraphService = Depends(get_knowledge_graph_service),
) -> Dict[str, Any]:
    """Get the full knowledge graph suitable for React Flow serialization."""
    containers = svc.find_containers()
    relationships = svc.get_all_relationships()
    
    # Process attributes back from JSON for typical fastAPI return serialization
    import json
    for container in containers:
        if "attributes_json" in container:
            if isinstance(container["attributes_json"], str):
                container["attributes"] = json.loads(container["attributes_json"])
            del container["attributes_json"]
            
    for rel in relationships:
        if "metadata_json" in rel and rel["metadata_json"]:
            if isinstance(rel["metadata_json"], str):
                rel["metadata"] = json.loads(rel["metadata_json"])
            del rel["metadata_json"]
            
    return {
        "nodes": containers,
        "edges": relationships
    }


@router.get("/search")
async def search_graph(
    q: str = Query(..., description="Natural-language search query"),
    limit: int = Query(5, ge=1, le=50, description="Max results to return"),
    svc: KnowledgeGraphService = Depends(get_knowledge_graph_service),
) -> Dict[str, Any]:
    """Semantic search across all containers using vector similarity (RAG).

    Returns the closest containers ranked by cosine distance (lower = more similar).
    """
    results = svc.semantic_search(q, limit=limit)
    return {"results": results, "query": q, "count": len(results)}

@router.get("/unresolved-threads")
async def get_unresolved_threads(
    era_id: str = None,
    svc: KnowledgeGraphService = Depends(get_knowledge_graph_service),
) -> Dict[str, Any]:
    """Get all unresolved plot threads."""
    threads = svc.get_unresolved_threads(era_id=era_id)
    return {"threads": threads}


from pydantic import BaseModel
class ResolveThreadRequest(BaseModel):
    edge_id: str
    resolved_in_era: str

@router.post("/resolve-thread")
async def resolve_thread(
    req: ResolveThreadRequest,
    svc: KnowledgeGraphService = Depends(get_knowledge_graph_service),
) -> Dict[str, Any]:
    """Mark a plot thread as resolved."""
    svc.resolve_thread(req.edge_id, req.resolved_in_era)
    return {"status": "success"}
