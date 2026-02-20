"""Graph router -- fetches all containers and relationships for React Flow."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends

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
