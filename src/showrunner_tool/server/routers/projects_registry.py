"""Project registry router — manage registered projects via REST API.

Endpoints for listing, registering, switching between projects.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from showrunner_tool.services.project_registry_service import (
    ProjectRegistryService,
    ProjectSummary,
)

router = APIRouter(prefix="/api/v1/projects-registry", tags=["projects-registry"])


# ── Request/Response Models ───────────────────────────────────────


class ProjectResponse(BaseModel):
    """Response model for a project."""
    id: str
    name: str
    path: str
    last_opened: str
    tags: List[str] = []


class RegisterProjectRequest(BaseModel):
    """Request to register a new project."""
    path: str
    name: str = None
    tags: List[str] = []
    set_active: bool = False


class SetActiveProjectRequest(BaseModel):
    """Request to set active project."""
    project_id: str


# ── Helper Functions ───────────────────────────────────────────


def _project_to_response(project: ProjectSummary) -> ProjectResponse:
    """Convert ProjectSummary to response model."""
    return ProjectResponse(
        id=project.id,
        name=project.name,
        path=project.path,
        last_opened=project.last_opened,
        tags=project.tags,
    )


# ── Endpoints ──────────────────────────────────────────────────


@router.get("/", response_model=List[ProjectResponse])
async def list_all_projects():
    """List all registered projects."""
    registry = ProjectRegistryService()
    projects = registry.get_all_projects()
    return [_project_to_response(p) for p in projects]


@router.get("/current", response_model=ProjectResponse)
async def get_current_project():
    """Get the currently active project."""
    registry = ProjectRegistryService()
    project = registry.get_active_project()

    if not project:
        raise HTTPException(status_code=404, detail="No active project set")

    return _project_to_response(project)


@router.post("/", response_model=ProjectResponse, status_code=201)
async def register_project(request: RegisterProjectRequest):
    """Register a new project.

    Args:
        request: Registration request with path and optional name/tags

    Returns:
        ProjectResponse with the registered project details
    """
    registry = ProjectRegistryService()

    try:
        project = registry.register_project(
            path=request.path,
            name=request.name,
            tags=request.tags,
        )

        if request.set_active:
            registry.set_active_project(project.id)

        return _project_to_response(project)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/set-active", response_model=ProjectResponse)
async def set_active_project(request: SetActiveProjectRequest):
    """Set the active project.

    Args:
        request: Request with project_id to activate

    Returns:
        ProjectResponse of the newly active project
    """
    registry = ProjectRegistryService()

    if not registry.set_active_project(request.project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    project = registry.get_project_by_id(request.project_id)
    return _project_to_response(project)


@router.delete("/{project_id}", status_code=204)
async def remove_project(project_id: str):
    """Remove a project from the registry.

    Args:
        project_id: ID of the project to remove
    """
    registry = ProjectRegistryService()

    if not registry.remove_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get a project by ID.

    Args:
        project_id: ID of the project

    Returns:
        ProjectResponse with project details
    """
    registry = ProjectRegistryService()
    project = registry.get_project_by_id(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return _project_to_response(project)
