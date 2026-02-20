"""Evaluation service -- wraps Evaluator, ContinuityChecker, PacingAnalyzer."""

from __future__ import annotations

from antigravity_tool.core.evaluator import Evaluator
from antigravity_tool.services.base import ServiceContext


class EvaluationService:
    """Unified access to evaluation, continuity, and pacing analysis."""

    def __init__(self, ctx: ServiceContext):
        self.ctx = ctx
        self._evaluator = Evaluator(ctx.project)

    def evaluate_scene(
        self,
        chapter_num: int,
        scene_num: int,
        criteria: list[str] | None = None,
    ) -> str:
        """Generate a scene evaluation prompt with author-level context."""
        return self._evaluator.evaluate_scene(chapter_num, scene_num, criteria)

    def evaluate_panel_sequence(self, chapter_num: int) -> str:
        """Generate a panel sequence evaluation prompt."""
        return self._evaluator.evaluate_panel_sequence(chapter_num)

    def evaluate_consistency(self, chapter_num: int) -> str:
        """Generate a consistency check prompt."""
        return self._evaluator.evaluate_consistency(chapter_num)

    def evaluate_dramatic_irony(self, chapter_num: int, scene_num: int) -> str:
        """Generate a dramatic irony evaluation prompt."""
        return self._evaluator.evaluate_dramatic_irony(chapter_num, scene_num)
