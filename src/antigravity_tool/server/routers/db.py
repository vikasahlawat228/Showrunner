"""DB maintenance router — health, reindex, consistency check (Phase K-5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from antigravity_tool.schemas.dal import ConsistencyIssue, DBHealthReport

router = APIRouter(prefix="/api/v1/db", tags=["database"])


# ── Response Models ───────────────────────────────────────────────


class DBStatsResponse(BaseModel):
    """Lightweight DB stats for dashboard display."""
    entity_counts: Dict[str, int] = Field(default_factory=dict)
    total_yaml_files: int = 0
    total_indexed: int = 0
    sync_metadata_count: int = 0


class ConsistencyReport(BaseModel):
    """Result of a consistency check."""
    issues: List[ConsistencyIssue] = Field(default_factory=list)
    total_issues: int = 0
    auto_fixable: int = 0


class ReindexResult(BaseModel):
    """Result of a reindex operation."""
    entities_migrated: int = 0
    total_indexed: int = 0


# ── Endpoints ─────────────────────────────────────────────────────


@router.get("/health", response_model=DBHealthReport)
async def db_health(request: Request):
    """Comprehensive health check of the persistence layer."""
    indexer = _get_indexer(request)
    project_path = _get_project_path(request)

    counts = indexer.get_entity_count_by_type()
    total_indexed = sum(counts.values())
    yaml_count = sum(1 for _ in project_path.rglob("*.yaml") if not _.name.startswith("_"))
    sync_rows = indexer.get_sync_metadata()

    # Check for orphaned indexes
    orphaned = sum(
        1 for e in indexer.query_entities()
        if e.get("yaml_path") and not Path(e["yaml_path"]).exists()
    )

    return DBHealthReport(
        entity_counts=counts,
        total_yaml_files=yaml_count,
        total_indexed=total_indexed,
        orphaned_indexes=orphaned,
    )


@router.get("/stats", response_model=DBStatsResponse)
async def db_stats(request: Request):
    """Lightweight entity counts and sync metadata stats."""
    indexer = _get_indexer(request)
    project_path = _get_project_path(request)

    counts = indexer.get_entity_count_by_type()
    yaml_count = sum(1 for _ in project_path.rglob("*.yaml") if not _.name.startswith("_"))
    sync_rows = indexer.get_sync_metadata()

    return DBStatsResponse(
        entity_counts=counts,
        total_yaml_files=yaml_count,
        total_indexed=sum(counts.values()),
        sync_metadata_count=len(sync_rows),
    )


@router.post("/check", response_model=ConsistencyReport)
async def db_check(request: Request):
    """Run YAML <-> SQLite consistency check."""
    indexer = _get_indexer(request)
    project_path = _get_project_path(request)

    from antigravity_tool.commands.db import _find_consistency_issues
    issues = _find_consistency_issues(project_path, indexer)

    return ConsistencyReport(
        issues=issues,
        total_issues=len(issues),
        auto_fixable=sum(1 for i in issues if i.auto_fixable),
    )


@router.post("/reindex", response_model=ReindexResult)
async def db_reindex(request: Request):
    """Rebuild the entity index from containers table."""
    indexer = _get_indexer(request)

    migrated = indexer.migrate_containers_to_entities()
    counts = indexer.get_entity_count_by_type()

    return ReindexResult(
        entities_migrated=migrated,
        total_indexed=sum(counts.values()),
    )


# ── Internal helpers ──────────────────────────────────────────────


def _get_indexer(request: Request):
    """Get SQLiteIndexer from app state."""
    return request.app.state.indexer


def _get_project_path(request: Request) -> Path:
    """Get project path from app state."""
    return request.app.state.project.path
