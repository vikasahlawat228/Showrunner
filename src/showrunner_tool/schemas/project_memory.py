"""Project Memory schemas for persistent project-level knowledge (Phase J)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from showrunner_tool.schemas.base import ShowrunnerBase


class MemoryScope(str, Enum):
    """Where a memory entry applies."""
    GLOBAL = "global"
    CHAPTER = "chapter"
    SCENE = "scene"
    CHARACTER = "character"


class MemoryEntry(BaseModel):
    """A single persistent memory entry."""
    key: str
    value: str
    scope: MemoryScope = MemoryScope.GLOBAL
    scope_id: Optional[str] = None
    source: str = "user_decision"
    auto_inject: bool = True
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ProjectMemory(ShowrunnerBase):
    """Persistent project-level memory — auto-injected into every chat context."""
    entries: List[MemoryEntry] = Field(default_factory=list)

    def get_auto_inject_entries(
        self,
        scope: Optional[MemoryScope] = None,
        scope_id: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Get all entries that should be auto-injected, optionally filtered by scope."""
        results = [e for e in self.entries if e.auto_inject]
        if scope is not None:
            results = [e for e in results if e.scope == scope]
        if scope_id is not None:
            results = [e for e in results if e.scope_id == scope_id]
        return results

    def to_context_string(self) -> str:
        """Render all auto-inject entries as a formatted context block."""
        auto = self.get_auto_inject_entries()
        if not auto:
            return ""
        lines = ["## Project Memory"]
        for entry in auto:
            scope_info = f" [{entry.scope.value}]" if entry.scope != MemoryScope.GLOBAL else ""
            lines.append(f"- **{entry.key}**{scope_info}: {entry.value}")
        return "\n".join(lines)
