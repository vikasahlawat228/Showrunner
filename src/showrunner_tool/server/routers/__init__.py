"""API routers -- one per resource group."""

from showrunner_tool.server.routers import (
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
    # Phase F additions
    projects,
    models,
    # Phase G Track 2
    research,
    # Phase I Track 4
    export,
    # Phase L IDE integration
    git_router,
    search_router,
    chat,
    db,
    sync,
    containers,
    analysis,
)

__all__ = [
    "project",
    "characters",
    "world",
    "chapters",
    "workflow",
    "director",
    "pipeline",
    "schemas_router",
    "graph",
    "timeline",
    "writing",
    "storyboard",
    # Phase F additions
    "projects",
    "models",
    # Phase G Track 2
    "research",
    # Phase I Track 4
    "export",
    # Phase L IDE integration
    "git_router",
    "search_router",
    "chat",
    "db",
    "sync",
    "containers",
    "analysis",
]
