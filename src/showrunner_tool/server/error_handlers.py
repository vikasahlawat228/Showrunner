"""Error handler middleware -- maps domain errors to HTTP status codes."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from showrunner_tool.errors import (
    ShowrunnerError,
    EntityNotFoundError,
    SchemaValidationError,
    ContextIsolationError,
    ProjectError,
    WorkflowError,
    PersistenceError,
)


_STATUS_MAP = {
    EntityNotFoundError: 404,
    WorkflowError: 409,
    SchemaValidationError: 422,
    ContextIsolationError: 403,
    ProjectError: 500,
    PersistenceError: 500,
}


async def showrunner_error_handler(request: Request, exc: ShowrunnerError) -> JSONResponse:
    """Convert domain errors to structured JSON error responses."""
    status_code = _STATUS_MAP.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": str(exc),
            "error_type": type(exc).__name__,
            "context": exc.context,
        },
    )
