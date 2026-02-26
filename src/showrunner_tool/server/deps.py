"""FastAPI dependency injection for services.

Uses Depends() to provide services to route handlers.
Phase F adds ModelConfigRegistry as a cached singleton.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends, Request

from showrunner_tool.core.project import Project
from showrunner_tool.services.base import ServiceContext
from showrunner_tool.services.world_service import WorldService
from showrunner_tool.services.character_service import CharacterService
from showrunner_tool.services.story_service import StoryService
from showrunner_tool.services.scene_service import SceneService
from showrunner_tool.services.panel_service import PanelService
from showrunner_tool.services.evaluation_service import EvaluationService
from showrunner_tool.services.session_service import SessionService
from showrunner_tool.services.director_service import DirectorService
from showrunner_tool.repositories.container_repo import SchemaRepository, ContainerRepository
from showrunner_tool.services.knowledge_graph_service import KnowledgeGraphService
from showrunner_tool.services.agent_dispatcher import AgentDispatcher
from showrunner_tool.services.writing_service import WritingService
from showrunner_tool.services.storyboard_service import StoryboardService
from showrunner_tool.services.pipeline_service import PipelineService
from showrunner_tool.services.context_engine import ContextEngine
from showrunner_tool.services.model_config_registry import ModelConfigRegistry
from showrunner_tool.services.research_service import ResearchService
from showrunner_tool.services.export_service import ExportService
from showrunner_tool.repositories.event_sourcing_repo import EventService
from showrunner_tool.services.analysis_service import AnalysisService
from showrunner_tool.services.reader_sim_service import ReaderSimService
from showrunner_tool.services.translation_service import TranslationService
from showrunner_tool.services.continuity_service import ContinuityService
from showrunner_tool.services.style_service import StyleService


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
    return SchemaRepository(project.path / "schemas")


def get_container_repo(project: Project = Depends(get_project)) -> ContainerRepository:
    return ContainerRepository(project.path)


def get_event_service(project: Project = Depends(get_project)) -> EventService:
    db_path = project.path / "event_log.db"
    return EventService(db_path)


def get_knowledge_graph_service(
    request: Request,
) -> KnowledgeGraphService:
    """Return the singleton KnowledgeGraphService created during app lifespan.

    Falls back to per-request creation if lifespan hasn't run (e.g. tests).
    """
    if hasattr(request.app.state, "kg_service"):
        return request.app.state.kg_service

    # Fallback for tests or when lifespan is not used
    project = get_project()
    container_repo = ContainerRepository(project.path)
    schema_repo = SchemaRepository(project.path / "schemas")
    db_path = project.path / "knowledge_graph.db"
    from showrunner_tool.repositories.sqlite_indexer import SQLiteIndexer
    indexer = SQLiteIndexer(db_path)

    from showrunner_tool.repositories.chroma_indexer import ChromaIndexer
    chroma_dir = project.path / ".chroma"
    chroma_indexer = ChromaIndexer(persist_dir=chroma_dir)

    svc = KnowledgeGraphService(container_repo, schema_repo, indexer, chroma_indexer=chroma_indexer)
    svc.sync_all(project.path)
    return svc


def get_writing_service(
    project: Project = Depends(get_project),
    container_repo: ContainerRepository = Depends(get_container_repo),
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    event_service: EventService = Depends(get_event_service),
) -> WritingService:
    return WritingService(container_repo, kg_service, project.path, event_service)


def get_storyboard_service(
    container_repo: ContainerRepository = Depends(get_container_repo),
    event_service: EventService = Depends(get_event_service),
) -> StoryboardService:
    """Create a StoryboardService with persistence and event sourcing."""
    return StoryboardService(container_repo, event_service)


def get_pipeline_service(
    container_repo: ContainerRepository = Depends(get_container_repo),
    event_service: EventService = Depends(get_event_service),
) -> PipelineService:
    """Create a PipelineService with persistence and event sourcing."""
    return PipelineService(container_repo, event_service)


def get_context_engine(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    container_repo: ContainerRepository = Depends(get_container_repo),
) -> ContextEngine:
    """Create a ContextEngine for centralized context assembly and token budgeting."""
    return ContextEngine(kg_service, container_repo)


# ── Phase F additions ─────────────────────────────────────────────


@lru_cache()
def get_model_config_registry(
    project: Project = Depends(get_project),
) -> ModelConfigRegistry:
    """LRU-cached ModelConfigRegistry, loaded from showrunner.yaml."""
    return ModelConfigRegistry(project.path)


@lru_cache()
def get_agent_dispatcher() -> AgentDispatcher:
    """Cached AgentDispatcher that loads skills from agents/skills/.

    The skills_dir path resolves relative to the package root:
    src/showrunner_tool/server/deps.py -> ../../../../agents/skills/
    """
    skills_dir = Path(__file__).resolve().parent.parent.parent.parent / "agents" / "skills"
    return AgentDispatcher(skills_dir)


# ── Phase G additions ─────────────────────────────────────────────


def get_research_service(
    container_repo: ContainerRepository = Depends(get_container_repo),
    event_service: EventService = Depends(get_event_service),
    agent_dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
) -> ResearchService:
    """Create a ResearchService with persistence, events, and agent dispatch."""
    return ResearchService(container_repo, event_service, agent_dispatcher)


# ── Phase I additions ─────────────────────────────────────────────


def get_export_service(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    container_repo: ContainerRepository = Depends(get_container_repo),
    schema_repo: SchemaRepository = Depends(get_schema_repo),
    event_service: EventService = Depends(get_event_service),
) -> ExportService:
    """Create an ExportService for manuscript, bundle, and screenplay exports."""
    return ExportService(kg_service, container_repo, schema_repo, event_service)


# ── Analysis Additions ───────────────────────────────────────────

def get_analysis_service(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    container_repo: ContainerRepository = Depends(get_container_repo),
    context_engine: ContextEngine = Depends(get_context_engine),
) -> AnalysisService:
    return AnalysisService(kg_service, container_repo, context_engine)


# ── Reader Preview Simulation ───────────────────────────────────────

def get_reader_sim_service(
    container_repo: ContainerRepository = Depends(get_container_repo),
) -> ReaderSimService:
    return ReaderSimService(container_repo)


def get_continuity_service(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    context_engine: ContextEngine = Depends(get_context_engine),
    event_service: EventService = Depends(get_event_service),
    agent_dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
) -> ContinuityService:
    return ContinuityService(kg_service, context_engine, event_service, agent_dispatcher)


def get_style_service(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    context_engine: ContextEngine = Depends(get_context_engine),
    agent_dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
) -> StyleService:
    return StyleService(kg_service, context_engine, agent_dispatcher)

def get_translation_service(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    context_engine: ContextEngine = Depends(get_context_engine),
    agent_dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
    container_repo: ContainerRepository = Depends(get_container_repo),
) -> TranslationService:
    return TranslationService(kg_service, context_engine, agent_dispatcher, container_repo)


# ── Phase J / Phase K additions ──────────────────────────────────

from showrunner_tool.repositories.chat_session_repo import ChatSessionRepository
from showrunner_tool.services.chat_session_service import ChatSessionService
from showrunner_tool.services.chat_orchestrator import ChatOrchestrator
from showrunner_tool.services.project_memory_service import ProjectMemoryService
from showrunner_tool.services.chat_context_manager import ChatContextManager
from showrunner_tool.services.intent_classifier import IntentClassifier


def get_chat_session_repo(request: Request) -> ChatSessionRepository:
    """Return the singleton ChatSessionRepository created during lifespan."""
    if hasattr(request.app.state, "chat_session_repo"):
        return request.app.state.chat_session_repo
    # Fallback for tests
    project = get_project()
    db_path = str(project.path / ".showrunner" / "chat.db")
    return ChatSessionRepository(db_path)


def get_chat_deps(request: Request = None) -> ChatSessionService:
    """Return a ChatSessionService.

    When called from route handlers with lazy import, request may be None.
    Falls back to app.state singleton if available.
    """
    if request and hasattr(request.app.state, "chat_session_service"):
        return request.app.state.chat_session_service
    # Fallback: create on-the-fly
    project = get_project()
    db_path = str(project.path / ".showrunner" / "chat.db")
    repo = ChatSessionRepository(db_path)
    return ChatSessionService(repo)


def get_chat_orchestrator_dep(request: Request = None) -> ChatOrchestrator:
    """Return the ChatOrchestrator singleton."""
    if request and hasattr(request.app.state, "chat_orchestrator"):
        return request.app.state.chat_orchestrator
    # Fallback: minimal orchestrator
    project = get_project()
    db_path = str(project.path / ".showrunner" / "chat.db")
    repo = ChatSessionRepository(db_path)
    svc = ChatSessionService(repo)
    return ChatOrchestrator(session_service=svc)


def get_project_memory_service(
    project: Project = Depends(get_project),
) -> ProjectMemoryService:
    return ProjectMemoryService(project.path)


def get_chat_context_manager(
    request: Request,
) -> ChatContextManager:
    """Return the ChatContextManager singleton."""
    if hasattr(request.app.state, "chat_context_manager"):
        return request.app.state.chat_context_manager
    # Fallback
    project = get_project()
    db_path = str(project.path / ".showrunner" / "chat.db")
    repo = ChatSessionRepository(db_path)
    svc = ChatSessionService(repo)
    memory_svc = ProjectMemoryService(project.path)
    return ChatContextManager(svc, memory_svc)


# ── Schema Inference Service ─────────────────────────────────────────

from showrunner_tool.services.schema_inference_service import SchemaInferenceService


def get_schema_inference_service(
    container_repo: ContainerRepository = Depends(get_container_repo),
    schema_repo: SchemaRepository = Depends(get_schema_repo),
) -> SchemaInferenceService:
    """Create a SchemaInferenceService for text extraction and schema suggestions."""
    return SchemaInferenceService(container_repo, schema_repo)

