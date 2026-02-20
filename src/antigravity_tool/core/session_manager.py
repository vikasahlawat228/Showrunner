"""Session and decision persistence across Claude Code sessions.

This module provides the cross-session memory that makes Antigravity
a full-stack tool. Decisions persist as YAML. Session logs accumulate.
The briefing generator reads these to produce context for new sessions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from antigravity_tool.schemas.session import (
    Decision,
    DecisionCategory,
    DecisionScope,
    SessionAction,
    SessionEntry,
)
from antigravity_tool.utils.io import read_yaml, write_yaml


class DecisionLog:
    """Persistent decision store — carries author preferences across sessions."""

    def __init__(self, project_path: Path):
        self.state_dir = project_path / ".antigravity"
        self.decisions_file = self.state_dir / "decisions.yaml"
        self._decisions: list[Decision] | None = None

    @property
    def decisions(self) -> list[Decision]:
        if self._decisions is None:
            self._decisions = self._load()
        return self._decisions

    def _load(self) -> list[Decision]:
        if not self.decisions_file.exists():
            return []
        raw = read_yaml(self.decisions_file)
        if not isinstance(raw, list):
            return []
        return [Decision(**d) for d in raw]

    def save(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        write_yaml(
            self.decisions_file,
            [d.model_dump(mode="json") for d in self.decisions],
        )

    def add(
        self,
        decision: str,
        category: str = "meta",
        *,
        chapter: int | None = None,
        scene: int | None = None,
        character_name: str | None = None,
    ) -> Decision:
        """Add a new decision to the log."""
        # Determine scope
        if character_name:
            scope = DecisionScope(level="character", character_name=character_name)
        elif scene is not None and chapter is not None:
            scope = DecisionScope(level="scene", chapter=chapter, scene=scene)
        elif chapter is not None:
            scope = DecisionScope(level="chapter", chapter=chapter)
        else:
            scope = DecisionScope(level="global")

        entry = Decision(
            decision=decision,
            category=DecisionCategory(category),
            scope=scope,
        )
        self.decisions.append(entry)
        self.save()
        return entry

    def deactivate(self, index: int) -> None:
        """Mark a decision as no longer active."""
        if 0 <= index < len(self.decisions):
            self.decisions[index].active = False
            self.save()

    def query(
        self,
        *,
        chapter: int | None = None,
        scene: int | None = None,
        character: str | None = None,
        category: str | None = None,
        active_only: bool = True,
    ) -> list[Decision]:
        """Get decisions matching the given context."""
        results = []
        for d in self.decisions:
            if active_only and not d.active:
                continue
            if category and d.category.value != category:
                continue
            if d.scope.matches(chapter=chapter, scene=scene, character=character):
                results.append(d)
        return results

    def format_for_prompt(
        self,
        *,
        chapter: int | None = None,
        scene: int | None = None,
        character: str | None = None,
    ) -> str:
        """Format applicable decisions as a text block for prompt injection."""
        relevant = self.query(chapter=chapter, scene=scene, character=character)
        if not relevant:
            return ""
        lines = ["## Author Decisions", ""]
        for d in relevant:
            scope_label = d.scope.level
            if d.scope.chapter:
                scope_label = f"chapter {d.scope.chapter}"
            if d.scope.scene:
                scope_label += f" scene {d.scope.scene}"
            if d.scope.character_name:
                scope_label = f"character: {d.scope.character_name}"
            lines.append(f"- [{d.category.value}] ({scope_label}) {d.decision}")
        return "\n".join(lines)


class SessionLog:
    """Tracks what happened in each working session."""

    def __init__(self, project_path: Path):
        self.sessions_dir = project_path / ".antigravity" / "sessions"

    def _ensure_dir(self) -> None:
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def start_session(self) -> SessionEntry:
        """Create a new session entry for the current date."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # Find next sequence number for today
        existing = sorted(self.sessions_dir.glob(f"session-{today}-*.yaml")) if self.sessions_dir.exists() else []
        seq = len(existing) + 1
        entry = SessionEntry(session_date=today)
        entry.notes = f"session-{today}-{seq:03d}"
        return entry

    def save_session(self, entry: SessionEntry) -> Path:
        """Persist a session entry to disk."""
        self._ensure_dir()
        label = entry.notes or entry.session_date
        filename = f"{label}.yaml"
        path = self.sessions_dir / filename
        write_yaml(path, entry.model_dump(mode="json"))
        return path

    def load_latest(self, count: int = 1) -> list[SessionEntry]:
        """Load the N most recent session logs."""
        if not self.sessions_dir.exists():
            return []
        files = sorted(self.sessions_dir.glob("session-*.yaml"), reverse=True)
        results = []
        for f in files[:count]:
            data = read_yaml(f)
            if data:
                results.append(SessionEntry(**data))
        return results

    def load_all(self) -> list[SessionEntry]:
        """Load all session logs chronologically."""
        if not self.sessions_dir.exists():
            return []
        files = sorted(self.sessions_dir.glob("session-*.yaml"))
        results = []
        for f in files:
            data = read_yaml(f)
            if data:
                results.append(SessionEntry(**data))
        return results

    def record_action(self, session: SessionEntry, action: str, command: str = "",
                      files_created: list[str] | None = None,
                      files_modified: list[str] | None = None) -> None:
        """Append an action to the current session."""
        session.actions.append(SessionAction(
            action=action,
            command=command,
            files_created=files_created or [],
            files_modified=files_modified or [],
        ))
