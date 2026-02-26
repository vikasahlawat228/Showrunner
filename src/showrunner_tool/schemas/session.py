"""Schemas for cross-session persistence: decisions, session logs, and briefings."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from showrunner_tool.schemas.base import ShowrunnerBase


# ── Decision Log ──────────────────────────────────────────────────


class DecisionCategory(str, Enum):
    STYLE = "style"
    TONE = "tone"
    CHARACTER = "character"
    PLOT = "plot"
    VISUAL = "visual"
    PACING = "pacing"
    WORLD = "world"
    META = "meta"


class DecisionScope(BaseModel):
    """Where a decision applies: global, chapter-level, scene-level, or character."""

    level: str = "global"  # global | chapter | scene | character
    chapter: Optional[int] = None
    scene: Optional[int] = None
    character_name: Optional[str] = None

    def matches(self, *, chapter: int | None = None, scene: int | None = None,
                character: str | None = None) -> bool:
        """Check if this scope applies to the given context."""
        if self.level == "global":
            return True
        if self.level == "chapter" and chapter is not None:
            return self.chapter == chapter
        if self.level == "scene" and chapter is not None and scene is not None:
            return self.chapter == chapter and self.scene == scene
        if self.level == "character" and character is not None:
            return self.character_name == character
        return False


class Decision(BaseModel):
    """A persistent author decision that carries across sessions."""

    decision: str
    category: DecisionCategory = DecisionCategory.META
    scope: DecisionScope = Field(default_factory=DecisionScope)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = True


# ── Session Log ───────────────────────────────────────────────────


class SessionAction(BaseModel):
    """A single action performed during a session."""

    action: str  # e.g. "Generated world settings"
    command: str = ""  # e.g. "showrunner world build"
    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SessionEntry(ShowrunnerBase):
    """Log of a single working session."""

    session_date: str = ""  # YYYY-MM-DD
    summary: str = ""
    workflow_step_start: str = ""
    workflow_step_end: str = ""
    actions: list[SessionAction] = Field(default_factory=list)
    decisions_made: list[str] = Field(default_factory=list)
    next_steps: str = ""
    chapter_focus: Optional[int] = None
    scene_focus: Optional[int] = None


# ── Project Briefing ──────────────────────────────────────────────


class ChapterSummary(BaseModel):
    """Compact summary of a chapter's state."""

    chapter_number: int
    title: str = ""
    status: str = "planned"  # planned | in_progress | drafted | complete
    scene_count: int = 0
    screenplay_count: int = 0
    panel_count: int = 0
    key_events: list[str] = Field(default_factory=list)


class ProjectBrief(ShowrunnerBase):
    """Dynamic briefing for a new Claude Code session.

    This is the bridge between sessions. It captures everything a new
    agent session needs to know to continue working on the project.
    """

    project_name: str = ""
    one_line: str = ""
    template: str = "manhwa"
    structure_type: str = "save_the_cat"

    # Current state
    current_step: str = ""
    current_step_label: str = ""
    current_chapter: Optional[int] = None
    current_scene: Optional[int] = None

    # Progress
    total_characters: int = 0
    character_names: list[str] = Field(default_factory=list)
    story_beats_filled: str = ""  # e.g. "8/15"
    chapter_summaries: list[ChapterSummary] = Field(default_factory=list)

    # Decisions (active only, scoped to current work)
    active_decisions: list[str] = Field(default_factory=list)

    # Recent history
    last_session_summary: str = ""
    last_session_next_steps: str = ""

    # What to do next
    suggested_next_action: str = ""
    suggested_command: str = ""
