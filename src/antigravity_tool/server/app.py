"""Antigravity Studio API -- FastAPI application with router-based architecture.

Phase F adds ModelConfigRegistry singleton and new routers (projects, models).
"""

from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

# Load environment variables early so litellm and other services can find API keys
load_dotenv()


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from antigravity_tool.errors import AntigravityError
from antigravity_tool.server.error_handlers import antigravity_error_handler
from antigravity_tool.server.routers import (
    project,
    characters,
    world,
    chapters,
    workflow,
    director,
    pipeline,
    schemas_router,
    graph,
    timeline,
    writing,
    storyboard,
)
from antigravity_tool.server.routers import projects as projects_router
from antigravity_tool.server.routers import containers as containers_router
from antigravity_tool.server.routers import models as models_router
from antigravity_tool.server.routers import research as research_router
from antigravity_tool.server.routers import export as export_router
from antigravity_tool.server.routers import analysis as analysis_router
from antigravity_tool.server.routers import preview as preview_router
from antigravity_tool.server.routers import translation as translation_router
from antigravity_tool.server.routers import chat as chat_router
from antigravity_tool.server.routers import db as db_router

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — start/stop the file watcher & singleton services
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application-level singletons:

    * KnowledgeGraphService + SQLiteIndexer (one per process)
    * FileWatcherService (background observer thread)
    * ModelConfigRegistry (Phase F)
    """
    from pathlib import Path
    from antigravity_tool.core.project import Project
    from antigravity_tool.repositories.container_repo import (
        ContainerRepository,
        SchemaRepository,
    )
    from antigravity_tool.repositories.sqlite_indexer import SQLiteIndexer
    from antigravity_tool.services.knowledge_graph_service import KnowledgeGraphService
    from antigravity_tool.services.file_watcher_service import FileWatcherService
    from antigravity_tool.services.model_config_registry import ModelConfigRegistry
    from antigravity_tool.services.pipeline_service import PipelineService
    from antigravity_tool.server.routers.project import broadcast_event

    # Resolve project
    proj = Project.find(Path.cwd())
    logger.info("Showrunner project: %s (%s)", proj.name, proj.path)

    # ChromaDB vector store (optional — graceful fallback if unavailable)
    chroma_indexer = None
    try:
        from antigravity_tool.repositories.chroma_indexer import ChromaIndexer
        chroma_dir = proj.path / ".chroma"
        chroma_indexer = ChromaIndexer(persist_dir=chroma_dir)
    except Exception:
        logger.warning("ChromaDB unavailable — semantic search disabled")

    # Build singletons
    container_repo = ContainerRepository(proj.path)
    schema_repo = SchemaRepository(proj.path / "schemas")
    indexer = SQLiteIndexer(proj.path / "knowledge_graph.db")
    kg_service = KnowledgeGraphService(
        container_repo, schema_repo, indexer, chroma_indexer=chroma_indexer
    )

    # Initial full sync
    kg_service.sync_all(proj.path)
    logger.info("Knowledge Graph initial sync complete")

    # Model Configuration Registry (Phase F)
    model_config_registry = ModelConfigRegistry(proj.path)
    logger.info(
        "ModelConfigRegistry loaded — default model: %s",
        model_config_registry.project_config.default_model,
    )

    # Inject into PipelineService class-level state for model resolution
    PipelineService.set_model_config_registry(model_config_registry)

    # Agent Dispatcher for pipeline research steps (Phase G Track 2)
    from antigravity_tool.services.agent_dispatcher import AgentDispatcher
    skills_dir = Path(__file__).resolve().parent.parent.parent.parent / "agents" / "skills"
    agent_dispatcher = AgentDispatcher(skills_dir)
    PipelineService.set_agent_dispatcher(agent_dispatcher)

    # File watcher
    watcher = FileWatcherService(
        project_path=proj.path,
        knowledge_graph_service=kg_service,
        container_repo=container_repo,
        broadcast_fn=broadcast_event,
    )
    watcher.start()

    # ── Phase J / Phase K: Chat system singletons ──────────────────
    from antigravity_tool.repositories.chat_session_repo import ChatSessionRepository
    from antigravity_tool.services.chat_session_service import ChatSessionService
    from antigravity_tool.services.chat_orchestrator import ChatOrchestrator
    from antigravity_tool.services.project_memory_service import ProjectMemoryService
    from antigravity_tool.services.chat_context_manager import ChatContextManager
    from antigravity_tool.services.intent_classifier import IntentClassifier
    from antigravity_tool.services.chat_tool_registry import build_tool_registry

    chat_db_path = proj.path / ".antigravity" / "chat.db"
    chat_db_path.parent.mkdir(parents=True, exist_ok=True)
    chat_session_repo = ChatSessionRepository(str(chat_db_path))
    chat_session_service = ChatSessionService(chat_session_repo)
    project_memory_service = ProjectMemoryService(proj.path)
    intent_classifier = IntentClassifier()
    chat_context_manager = ChatContextManager(
        session_service=chat_session_service,
        memory_service=project_memory_service,
    )

    # Build tool registry from existing services
    from antigravity_tool.repositories.event_sourcing_repo import EventService
    event_service = EventService(proj.path / "event_log.db")
    tool_registry = build_tool_registry(
        kg_service=kg_service,
        container_repo=container_repo,
        project_memory_service=project_memory_service,
        pipeline_service=PipelineService(container_repo, event_service),
        project_path=proj.path,
    )

    # ── Phase L: Cloud Sync System ──────────────────
    from antigravity_tool.services.google_drive_adapter import GoogleDriveAdapter
    from antigravity_tool.services.cloud_sync_service import CloudSyncService
    
    token_path = proj.path / ".antigravity" / "token.json"
    drive_adapter = GoogleDriveAdapter(
        credentials_path=str(proj.path / "credentials.json"),
        token_path=str(token_path)
    )
    cloud_sync_service = CloudSyncService(drive_adapter, indexer)
    cloud_sync_service.start_worker()
    logger.info("Cloud Sync system initialized.")

    chat_orchestrator = ChatOrchestrator(
        session_service=chat_session_service,
        intent_classifier=intent_classifier,
        context_manager=chat_context_manager,
        tool_registry=tool_registry,
        model_config_registry=model_config_registry,
    )
    logger.info("Chat system initialized (db: %s, tools: %s)", chat_db_path, list(tool_registry.keys()))

    # Store on app.state so DI can access the singletons
    app.state.project = proj
    app.state.container_repo = container_repo
    app.state.schema_repo = schema_repo
    app.state.indexer = indexer
    app.state.kg_service = kg_service
    app.state.file_watcher = watcher
    app.state.model_config_registry = model_config_registry
    app.state.chat_session_repo = chat_session_repo
    app.state.chat_session_service = chat_session_service
    app.state.chat_orchestrator = chat_orchestrator
    app.state.project_memory_service = project_memory_service
    app.state.chat_context_manager = chat_context_manager
    app.state.cloud_sync_service = cloud_sync_service

    yield  # ---- application is running ----

    # Shutdown
    watcher.stop()
    indexer.close()
    chat_session_repo.close()
    logger.info("Lifespan shutdown complete")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(title="Antigravity Studio API", version="0.3.0", lifespan=lifespan)

# CORS -- allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Domain error → HTTP response mapping
app.add_exception_handler(AntigravityError, antigravity_error_handler)

# Include all resource routers
app.include_router(project.router)
app.include_router(characters.router)
app.include_router(world.router)
app.include_router(chapters.router)
app.include_router(workflow.router)
app.include_router(director.router)
app.include_router(pipeline.router, prefix="/api/v1")
app.include_router(schemas_router.router)
app.include_router(graph.router)
app.include_router(timeline.router)
app.include_router(writing.router)
app.include_router(storyboard.router)
app.include_router(containers_router.router)

# Phase F additions
app.include_router(projects_router.router)
app.include_router(models_router.router)

# Phase G Track 2
app.include_router(research_router.router)

# Phase I Track 4
app.include_router(export_router.router)

# Phase H Track 3
app.include_router(translation_router.router)

# Phase Next-B
app.include_router(analysis_router.router)

# Phase Next-C
app.include_router(preview_router.router)

# Phase J (Agentic Chat) + Phase K (Unified DAL)
app.include_router(chat_router.router)
app.include_router(db_router.router)

# Phase L (Cloud Sync)
from antigravity_tool.server.routers import sync as sync_router
app.include_router(sync_router.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
