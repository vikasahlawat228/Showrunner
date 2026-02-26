"""Session service -- wraps DecisionLog, SessionLog, and BriefingGenerator."""

from __future__ import annotations

from typing import Optional

from showrunner_tool.core.session_manager import DecisionLog, SessionLog
from showrunner_tool.core.briefing import BriefingGenerator
from showrunner_tool.schemas.session import Decision, SessionEntry, ProjectBrief
from showrunner_tool.services.base import ServiceContext


class SessionService:
    """Unified access to decisions, sessions, and briefings."""

    def __init__(self, ctx: ServiceContext):
        self.ctx = ctx
        self._decision_log = DecisionLog(ctx.project.path)
        self._session_log = SessionLog(ctx.project.path)
        self._briefing = BriefingGenerator(ctx.project)

    # ── Decisions ─────────────────────────────────────────────────

    def add_decision(
        self,
        decision: str,
        category: str = "meta",
        chapter: int | None = None,
        scene: int | None = None,
        character_name: str | None = None,
    ) -> Decision:
        """Add a new decision to the log."""
        return self._decision_log.add(
            decision, category,
            chapter=chapter, scene=scene, character_name=character_name,
        )

    def list_decisions(
        self,
        category: str | None = None,
        active_only: bool = True,
    ) -> list[Decision]:
        """List decisions, optionally filtered."""
        return self._decision_log.query(category=category, active_only=active_only)

    def deactivate_decision(self, index: int) -> None:
        """Deactivate a decision by index."""
        self._decision_log.deactivate(index)

    # ── Sessions ──────────────────────────────────────────────────

    def start_session(self) -> SessionEntry:
        """Start a new working session."""
        return self._session_log.start_session()

    def end_session(self, entry: SessionEntry) -> None:
        """Save and close a session."""
        self._session_log.save_session(entry)

    def get_recent_sessions(self, count: int = 5) -> list[SessionEntry]:
        """Load the N most recent session logs."""
        return self._session_log.load_latest(count)

    def get_all_sessions(self) -> list[SessionEntry]:
        """Load all session logs."""
        return self._session_log.load_all()

    # ── Briefing ──────────────────────────────────────────────────

    def generate_brief(self) -> ProjectBrief:
        """Generate a project brief for the current state."""
        return self._briefing.generate()

    def render_brief_markdown(self) -> str:
        """Render the project brief as markdown for display or CLAUDE.md."""
        return self._briefing.render_markdown()
