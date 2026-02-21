"""Containers router -- CRUD operations and reordering."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException

from antigravity_tool.server.deps import get_container_repo, get_event_service, get_knowledge_graph_service
from antigravity_tool.repositories.container_repo import ContainerRepository
from antigravity_tool.repositories.event_sourcing_repo import EventService
from antigravity_tool.schemas.container import GenericContainer
from antigravity_tool.server.api_schemas import ContainerCreateRequest, ContainerUpdateRequest, ReorderRequest

router = APIRouter(prefix="/api/v1/containers", tags=["containers"])


@router.post("/")
async def create_container(
    req: ContainerCreateRequest,
    container_repo: ContainerRepository = Depends(get_container_repo),
    event_service: EventService = Depends(get_event_service),
):
    container = GenericContainer(
        container_type=req.container_type,
        name=req.name,
        parent_id=req.parent_id,
        sort_order=req.sort_order,
        attributes=req.attributes,
    )
    container_repo.save_container(container)
    event_service.append_event(
        parent_event_id=None,
        branch_id="main",
        event_type="CREATE",
        container_id=container.id,
        payload=container.model_dump(mode="json"),
    )
    return container.model_dump()


@router.get("/{container_id}")
async def get_container(
    container_id: str,
    container_repo: ContainerRepository = Depends(get_container_repo),
):
    container = container_repo.get_by_id(container_id)
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")
    return container.model_dump()


@router.put("/{container_id}")
async def update_container(
    container_id: str,
    req: ContainerUpdateRequest,
    container_repo: ContainerRepository = Depends(get_container_repo),
    event_service: EventService = Depends(get_event_service),
):
    container = container_repo.get_by_id(container_id)
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")
    
    updates = {}
    if req.name is not None:
        container.name = req.name
        updates["name"] = req.name
    if req.parent_id is not None:
        container.parent_id = req.parent_id
        updates["parent_id"] = req.parent_id
    if req.sort_order is not None:
        container.sort_order = req.sort_order
        updates["sort_order"] = req.sort_order
    if req.attributes is not None:
        container.attributes = req.attributes
        updates["attributes"] = req.attributes
        
    container_repo.save_container(container)
    
    if updates:
        event_service.append_event(
            parent_event_id=None,
            branch_id="main",
            event_type="UPDATE",
            container_id=container.id,
            payload=updates,
        )
        
    return container.model_dump()


@router.delete("/{container_id}")
async def delete_container(
    container_id: str,
    container_repo: ContainerRepository = Depends(get_container_repo),
    event_service: EventService = Depends(get_event_service),
    kg_service: Any = Depends(get_knowledge_graph_service),
):
    success = container_repo.delete_by_id(container_id)
    if not success:
        raise HTTPException(status_code=404, detail="Container not found")
        
    # Emit DELETE event
    event_service.append_event(
        parent_event_id=None,
        branch_id="main",
        event_type="DELETE",
        container_id=container_id,
        payload={},
    )
    
    # Try to remove from SQLite indexer
    try:
        kg_service.indexer.delete_entity(container_id)
    except Exception:
        pass
        
    return {"status": "deleted", "id": container_id}


@router.post("/reorder")
async def reorder_containers(
    req: ReorderRequest,
    container_repo: ContainerRepository = Depends(get_container_repo),
):
    for item in req.items:
        container_id = item.get("id")
        sort_order = item.get("sort_order")
        if container_id and sort_order is not None:
            container = container_repo.get_by_id(container_id)
            if container:
                container.sort_order = sort_order
                container_repo.save_container(container)
    return {"status": "reordered"}
