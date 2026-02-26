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
]
