"""Project Memory Service — persistent project-level knowledge (Phase J-2).

CRUD for project memories: world rules, decisions, style preferences.
Scoped to global, chapter, scene, or character.
Auto-injected into chat context when flagged.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from antigravity_tool.schemas.project_memory import (
    MemoryEntry,
    MemoryScope,
    ProjectMemory,
)
from antigravity_tool.utils.io import read_yaml, write_yaml

logger = logging.getLogger(__name__)


class ProjectMemoryService:
    """CRUD service for persistent project memories.

    Stores memory in `.antigravity/project_memory.yaml` within the project.
    """

    def __init__(self, project_path: Path):
        self._path = project_path / ".antigravity" / "project_memory.yaml"
        self._memory: Optional[ProjectMemory] = None

    def _load(self) -> ProjectMemory:
        """Load or create the project memory file."""
        if self._memory is not None:
            return self._memory

        if self._path.exists():
            try:
                data = read_yaml(self._path)
                self._memory = ProjectMemory(**data)
            except Exception as e:
                logger.warning("Failed to load project memory: %s", e)
                self._memory = ProjectMemory()
        else:
            self._memory = ProjectMemory()

        return self._memory

    def _save(self) -> None:
        """Persist memory to disk."""
        if self._memory is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        write_yaml(self._path, self._memory.model_dump(mode="json"))

    # ── CRUD ──────────────────────────────────────────────────────

    def add_entry(
        self,
        key: str,
        value: str,
        scope: MemoryScope = MemoryScope.GLOBAL,
        scope_id: Optional[str] = None,
        source: str = "user_decision",
        auto_inject: bool = True,
    ) -> MemoryEntry:
        """Add a new memory entry."""
        memory = self._load()
        entry = MemoryEntry(
            key=key,
            value=value,
            scope=scope,
            scope_id=scope_id,
            source=source,
            auto_inject=auto_inject,
        )
        memory.entries.append(entry)
        self._save()
        return entry

    def get_entries(
        self,
        scope: Optional[MemoryScope] = None,
        scope_id: Optional[str] = None,
        auto_inject_only: bool = False,
    ) -> List[MemoryEntry]:
        """Get memory entries, optionally filtered."""
        memory = self._load()
        results = list(memory.entries)

        if auto_inject_only:
            results = [e for e in results if e.auto_inject]
        if scope is not None:
            results = [e for e in results if e.scope == scope]
        if scope_id is not None:
            results = [e for e in results if e.scope_id == scope_id]

        return results

    def get_entry_by_key(self, key: str) -> Optional[MemoryEntry]:
        """Get a single entry by key."""
        memory = self._load()
        for entry in memory.entries:
            if entry.key == key:
                return entry
        return None

    def update_entry(self, key: str, value: str) -> Optional[MemoryEntry]:
        """Update an existing entry's value by key."""
        memory = self._load()
        for entry in memory.entries:
            if entry.key == key:
                entry.value = value
                self._save()
                return entry
        return None

    def delete_entry(self, key: str) -> bool:
        """Delete a memory entry by key."""
        memory = self._load()
        original_len = len(memory.entries)
        memory.entries = [e for e in memory.entries if e.key != key]
        if len(memory.entries) < original_len:
            self._save()
            return True
        return False

    def to_context_string(self) -> str:
        """Render all auto-inject entries as a context block for chat."""
        memory = self._load()
        return memory.to_context_string()

    def clear_all(self) -> int:
        """Remove all entries. Returns count removed."""
        memory = self._load()
        count = len(memory.entries)
        memory.entries = []
        self._save()
        return count
