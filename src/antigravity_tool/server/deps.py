"""FastAPI dependency injection for services.

Uses Depends() to provide services to route handlers.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends

from antigravity_tool.core.project import Project
from antigravity_tool.services.base import ServiceContext
from antigravity_tool.services.world_service import WorldService
from antigravity_tool.services.character_service import CharacterService
from antigravity_tool.services.story_service import StoryService
from antigravity_tool.services.scene_service import SceneService
from antigravity_tool.services.panel_service import PanelService
from antigravity_tool.services.evaluation_service import EvaluationService
from antigravity_tool.services.session_service import SessionService
from antigravity_tool.services.director_service import DirectorService
from antigravity_tool.repositories.container_repo import SchemaRepository, ContainerRepository
from antigravity_tool.services.knowledge_graph_service import KnowledgeGraphService


@lru_cache()
def get_project() -> Project:
    """Cached project instance. One per process."""
    return Project.find(Path.cwd())


def get_service_context(project: Project = Depends(get_project)) -> ServiceContext:
    """Create a ServiceContext from the cached project."""
    return ServiceContext.from_project(project)


def get_world_service(ctx: ServiceContext = Depends(get_service_context)) -> WorldService:
    return WorldService(ctx)


def get_character_service(ctx: ServiceContext = Depends(get_service_context)) -> CharacterService:
    return CharacterService(ctx)


def get_story_service(ctx: ServiceContext = Depends(get_service_context)) -> StoryService:
    return StoryService(ctx)


def get_scene_service(ctx: ServiceContext = Depends(get_service_context)) -> SceneService:
    return SceneService(ctx)


def get_panel_service(ctx: ServiceContext = Depends(get_service_context)) -> PanelService:
    return PanelService(ctx)


def get_evaluation_service(ctx: ServiceContext = Depends(get_service_context)) -> EvaluationService:
    return EvaluationService(ctx)


def get_session_service(ctx: ServiceContext = Depends(get_service_context)) -> SessionService:
    return SessionService(ctx)


def get_director_service(ctx: ServiceContext = Depends(get_service_context)) -> DirectorService:
    return DirectorService(ctx)


def get_schema_repo(project: Project = Depends(get_project)) -> SchemaRepository:
    return SchemaRepository(project.root / "schemas")


def get_container_repo(project: Project = Depends(get_project)) -> ContainerRepository:
    return ContainerRepository(project.root)


def get_event_service(project: Project = Depends(get_project)):
    from antigravity_tool.repositories.event_sourcing_repo import EventService
    db_path = project.root / "event_log.db"
    return EventService(db_path)


def get_knowledge_graph_service(
    project: Project = Depends(get_project),
    container_repo: ContainerRepository = Depends(get_container_repo),
    schema_repo: SchemaRepository = Depends(get_schema_repo),
) -> KnowledgeGraphService:
    # In a real app the indexer would be a singleton or app-level dependency
    # For now we'll let the service create its own indexer pointing to the project root
    db_path = project.root / "knowledge_graph.db"
    from antigravity_tool.repositories.sqlite_indexer import SQLiteIndexer
    indexer = SQLiteIndexer(db_path)
    # Automatically sync on start
    svc = KnowledgeGraphService(container_repo, schema_repo, indexer)
    svc.sync_all(project.root)
    return svc
