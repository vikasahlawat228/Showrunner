"""Chat router — REST + SSE endpoints for the agentic chat system (Phase J)."""

from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from antigravity_tool.schemas.chat import (
    ChatMessage,
    ChatSession,
    ChatSessionSummary,
    SessionState,
    AutonomyLevel,
)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


# ── Request/Response Models ───────────────────────────────────────


class CreateSessionRequest(BaseModel):
    """Request body for creating a new chat session."""
    name: str = ""
    project_id: str = ""
    autonomy_level: int = 1
    context_budget: int = 100_000
    tags: List[str] = Field(default_factory=list)


class SendMessageRequest(BaseModel):
    """Request body for sending a message."""
    content: str
    mentioned_entity_ids: List[str] = Field(default_factory=list)
    context_payload: Optional[dict] = None


class SessionResponse(BaseModel):
    """Response for a single session."""
    id: str
    name: str
    project_id: str
    state: str
    autonomy_level: int
    message_count: int
    token_usage: int
    context_budget: int
    created_at: str
    updated_at: str
    tags: List[str] = Field(default_factory=list)


class MessageResponse(BaseModel):
    """Response for a single message."""
    id: str
    session_id: str
    role: str
    content: str
    action_traces: list = Field(default_factory=list)
    artifacts: list = Field(default_factory=list)
    mentioned_entity_ids: List[str] = Field(default_factory=list)
    created_at: str


# ── Dependency stubs (wired in deps.py later) ─────────────────────


def _get_chat_session_service():
    """Placeholder — will be wired via deps.py in lifespan."""
    raise NotImplementedError("Chat session service not configured")


def _get_chat_orchestrator():
    """Placeholder — will be wired via deps.py in lifespan."""
    raise NotImplementedError("Chat orchestrator not configured")


# ── Session Endpoints ─────────────────────────────────────────────


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(body: CreateSessionRequest, request: Request):
    """Create a new chat session."""
    from antigravity_tool.server.deps import get_chat_deps

    svc = get_chat_deps(request)
    session = svc.create_session(
        project_id=body.project_id,
        name=body.name,
        autonomy_level=AutonomyLevel(body.autonomy_level),
        context_budget=body.context_budget,
        tags=body.tags,
    )
    return _session_to_response(session, svc)


@router.get("/sessions", response_model=List[ChatSessionSummary])
async def list_sessions(
    request: Request,
    project_id: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List chat sessions with summaries."""
    from antigravity_tool.server.deps import get_chat_deps

    svc = get_chat_deps(request)
    state_enum = SessionState(state) if state else None
    return svc.list_sessions(
        project_id=project_id, state=state_enum, limit=limit, offset=offset
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, request: Request):
    """Get a single chat session by ID."""
    from antigravity_tool.server.deps import get_chat_deps

    svc = get_chat_deps(request)
    session = svc.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_response(session, svc)


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str, request: Request):
    """End and delete a chat session."""
    from antigravity_tool.server.deps import get_chat_deps

    svc = get_chat_deps(request)
    if not svc.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/sessions/{session_id}/resume", response_model=SessionResponse)
async def resume_session(session_id: str, request: Request):
    """Resume an ended chat session."""
    from antigravity_tool.server.deps import get_chat_deps

    svc = get_chat_deps(request)
    session = svc.resume_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_response(session, svc)


@router.post("/sessions/{session_id}/end", response_model=SessionResponse)
async def end_session(session_id: str, request: Request):
    """End an active chat session."""
    from antigravity_tool.server.deps import get_chat_deps

    svc = get_chat_deps(request)
    session = svc.end_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_response(session, svc)


# ── Message Endpoints ─────────────────────────────────────────────


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, body: SendMessageRequest, request: Request):
    """Send a message and receive SSE response stream."""
    from antigravity_tool.server.deps import get_chat_deps, get_chat_orchestrator_dep

    svc = get_chat_deps(request)
    session = svc.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    orchestrator = get_chat_orchestrator_dep(request)

    async def event_stream():
        async for event in orchestrator.handle_message(
            session_id=session_id,
            content=body.content,
            mentioned_entity_ids=body.mentioned_entity_ids,
            context_payload=body.context_payload,
        ):
            yield f"data: {json.dumps(event.model_dump())}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: str,
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get message history for a session."""
    from antigravity_tool.server.deps import get_chat_deps

    svc = get_chat_deps(request)
    session = svc.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = svc.get_messages(session_id, limit=limit, offset=offset)
    return [
        MessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            action_traces=[t.model_dump() for t in m.action_traces],
            artifacts=[a.model_dump() for a in m.artifacts],
            mentioned_entity_ids=m.mentioned_entity_ids,
            created_at=m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at),
        )
        for m in messages
    ]


# ── Helpers ───────────────────────────────────────────────────────


def _session_to_response(session: ChatSession, svc) -> SessionResponse:
    """Convert a ChatSession to a SessionResponse."""
    return SessionResponse(
        id=session.id,
        name=session.name,
        project_id=session.project_id,
        state=session.state.value,
        autonomy_level=session.autonomy_level.value,
        message_count=svc.get_message_count(session.id),
        token_usage=session.token_usage,
        context_budget=session.context_budget,
        created_at=session.created_at.isoformat() if hasattr(session.created_at, "isoformat") else str(session.created_at),
        updated_at=session.updated_at.isoformat() if hasattr(session.updated_at, "isoformat") else str(session.updated_at),
        tags=session.tags,
    )
