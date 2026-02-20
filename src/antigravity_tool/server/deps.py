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
