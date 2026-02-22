"""Data Access Layer schemas — caching, sync, batch loading, maintenance."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Sync & Indexing ─────────────────────────────────────────────

class SyncMetadata(BaseModel):
    """Tracks the last-indexed state of a YAML file for incremental sync."""
    yaml_path: str
    entity_id: str
    entity_type: str
    content_hash: str
    mtime: float
    indexed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    file_size: int


# ── Caching ────────────────────────────────────────────────────

class CacheEntry(BaseModel, Generic[T]):
    """A single cached entity with mtime-based invalidation metadata."""
    entity: Any
    path: str
    mtime: float
    accessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    size_bytes: int = 0


class CacheStats(BaseModel):
    """Cache performance metrics."""
    size: int = 0
    max_size: int = 500
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    hit_rate: float = 0.0


# ── Context Assembly ────────────────────────────────────────────

class ContextScope(BaseModel):
    """Defines what context to assemble and how to render it."""
    step: str
    access_level: Literal["story", "author"] = "story"
    chapter: Optional[int] = None
    scene: Optional[int] = None
    character_name: Optional[str] = None
    token_budget: int = 100_000
    output_format: Literal["template", "structured", "raw"] = "template"
    include_relationships: bool = True
    semantic_query: Optional[str] = None


class ProjectSnapshot(BaseModel):
    """Pre-loaded batch of entities for a given context scope."""
    world: Optional[Dict[str, Any]] = None
    characters: List[Dict[str, Any]] = Field(default_factory=list)
    story_structure: Optional[Dict[str, Any]] = None
    scenes: List[Dict[str, Any]] = Field(default_factory=list)
    screenplays: List[Dict[str, Any]] = Field(default_factory=list)
    panels: List[Dict[str, Any]] = Field(default_factory=list)
    style_guides: Dict[str, Any] = Field(default_factory=dict)
    decisions: List[Dict[str, Any]] = Field(default_factory=list)
    reader_knowledge: Optional[Dict[str, Any]] = None
    creative_room: Optional[Dict[str, Any]] = None

    # Load metrics (Glass Box)
    load_time_ms: int = 0
    entities_loaded: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


# ── Unit of Work ────────────────────────────────────────────────

class UnitOfWorkEntry(BaseModel):
    """A single buffered mutation in a UnitOfWork transaction."""
    operation: Literal["save", "delete"]
    entity_id: str
    entity_type: str
    yaml_path: str
    data: Optional[Dict[str, Any]] = None
    event_type: Optional[Literal["CREATE", "UPDATE", "DELETE"]] = None
    event_payload: Optional[Dict[str, Any]] = None
    branch_id: str = "main"


# ── DB Maintenance ──────────────────────────────────────────────

class DBHealthReport(BaseModel):
    """Comprehensive health check of the persistence layer."""
    entity_counts: Dict[str, int] = Field(default_factory=dict)
    total_yaml_files: int = 0
    total_indexed: int = 0
    orphaned_indexes: int = 0
    stale_entries: int = 0
    mismatched_hashes: int = 0
    disk_usage_bytes: int = 0
    index_size_bytes: int = 0
    chroma_doc_count: int = 0
    event_count: int = 0
    last_full_sync: Optional[datetime] = None
    last_incremental_sync: Optional[datetime] = None
    cache_stats: Optional[CacheStats] = None


class ConsistencyIssue(BaseModel):
    """A single YAML ↔ SQLite consistency issue found by db check."""
    issue_type: Literal["orphaned_index", "stale_file", "hash_mismatch", "missing_entity"]
    yaml_path: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    description: str
    auto_fixable: bool = True
