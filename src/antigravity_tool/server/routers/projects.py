"""Projects router — multi-project management (Phase F).

Provides CRUD for multiple isolated project directories, story structure
tree resolution, and project-level settings management.
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request

from antigravity_tool.core.project import Project
from antigravity_tool.schemas.project import (
    ProjectCreate,
    ProjectSettings,
    ProjectSettingsUpdate,
    ProjectSummary,
    StructureTree,
    StructureTreeNode,
)
from antigravity_tool.server.deps import (
    get_knowledge_graph_service,
    get_project,
)
from antigravity_tool.services.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=List[ProjectSummary])
async def get_current_project(project: Project = Depends(get_project)):
    """Return summary of the current project.

    Multi-project listing will be expanded later; for now we expose the
    active project wrapped in a list so the frontend can fetch its metadata.
    """
    return [ProjectSummary(
        id=str(project.path),
        name=project.name,
        path=str(project.path),
        description=project.variables.get("description"),
        default_model=project.variables.get("default_model", "gemini/gemini-2.0-flash"),
    )]


@router.get("/settings", response_model=ProjectSettings)
async def get_project_settings(project: Project = Depends(get_project)):
    """Return full project settings."""
    return ProjectSettings(
        name=project.name,
        version=project.variables.get("version", "0.1.0"),
        description=project.variables.get("description"),
        default_model=project.variables.get("default_model", "gemini/gemini-2.0-flash"),
        model_overrides=project.variables.get("model_overrides", {}),
        variables=project.variables,
    )


@router.put("/settings", response_model=ProjectSettings)
async def update_project_settings(
    update: ProjectSettingsUpdate,
    project: Project = Depends(get_project),
):
    """Update project settings in antigravity.yaml."""
    from antigravity_tool.utils.io import read_yaml, write_yaml

    yaml_path = project.path / "antigravity.yaml"
    data = read_yaml(yaml_path)

    if update.name is not None:
        data["name"] = update.name
    if update.description is not None:
        data["description"] = update.description
    if update.default_model is not None:
        data["default_model"] = update.default_model
    if update.variables is not None:
        data.setdefault("variables", {}).update(update.variables)

    write_yaml(yaml_path, data)

    return ProjectSettings(
        name=data.get("name", project.name),
        version=data.get("version", "0.1.0"),
        description=data.get("description"),
        default_model=data.get("default_model", "gemini/gemini-2.0-flash"),
        model_overrides=data.get("model_overrides", {}),
        variables=data.get("variables", {}),
    )


@router.get("/structure", response_model=StructureTree)
async def get_structure_tree(
    project: Project = Depends(get_project),
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Build the hierarchical story structure tree (Season → Scene).

    Walks ``parent_id`` chains in the Knowledge Graph index to produce
    a nested tree.
    """
    raw_tree = kg_service.get_structure_tree(project_id=str(project.path))

    def _to_node(raw: dict) -> StructureTreeNode:
        return StructureTreeNode(
            id=raw["id"],
            name=raw["name"],
            container_type=raw["container_type"],
            sort_order=raw.get("sort_order", 0),
            children=[_to_node(c) for c in raw.get("children", [])],
        )

    return StructureTree(
        project_id=str(project.path),
        roots=[_to_node(r) for r in raw_tree],
    )
