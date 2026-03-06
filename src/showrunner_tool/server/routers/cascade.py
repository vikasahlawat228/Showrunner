from pathlib import Path
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from showrunner_tool.services.cascade_update_service import CascadeUpdateService

router = APIRouter(prefix="/api/v1/cascade", tags=["cascade"])

class CascadeRequest(BaseModel):
    file_path: str
    dry_run: bool = False

class CascadeResult(BaseModel):
    file_path: str
    entities_analyzed: int
    entities_updated: int
    updates: list
    dry_run: bool

@router.post("/update", response_model=CascadeResult)
async def trigger_cascade(body: CascadeRequest, request: Request):
    """Analyze a changed file and cascade updates to related entities."""
    app = request.app
    kg_service = getattr(app.state, "kg_service", None)
    container_repo = getattr(app.state, "container_repo", None)
    agent_dispatcher = getattr(app.state, "agent_dispatcher", None)

    if not all([kg_service, container_repo, agent_dispatcher]):
        raise HTTPException(status_code=500, detail="Missing required services for cascade update")

    service = CascadeUpdateService(
        kg_service=kg_service,
        container_repo=container_repo,
        agent_dispatcher=agent_dispatcher,
    )

    full_path = container_repo.base_dir / body.file_path

    try:
        result = await service.analyze_and_update(full_path, dry_run=body.dry_run)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=", ".join(result.get("errors", ["Unknown error"])))
        
        # Format updates list
        updates_list = []
        for entity_id, changes in result.get("updates", {}).items():
            for key, val in changes.items():
                if isinstance(val, dict) and "old_value" in val and "new_value" in val:
                    updates_list.append({
                        "entity": entity_id,
                        "field": key,
                        "old_value": val["old_value"],
                        "new_value": val["new_value"],
                    })
                else:
                    updates_list.append({
                        "entity": entity_id,
                        "field": key,
                        "old_value": None,
                        "new_value": val,
                    })

        return CascadeResult(
            file_path=body.file_path,
            entities_analyzed=len(result.get("updates", {})),
            entities_updated=len(result.get("changed_files", [])),
            updates=updates_list,
            dry_run=body.dry_run
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
