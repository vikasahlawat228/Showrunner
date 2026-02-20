"""Antigravity Studio API -- FastAPI application with router-based architecture."""

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
)

app = FastAPI(title="Antigravity Studio API", version="0.2.0")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
