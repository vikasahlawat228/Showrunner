"""Reading time estimator based on manga reading speed research.

Research-based constants:
- Dialogue panel: ~3.75 seconds average
- Action panel: ~2.0 seconds average
- Splash/full-page panel: ~4.0 seconds
- Narration panel: ~4.5 seconds
"""

from __future__ import annotations

from typing import Optional

from antigravity_tool.core.project import Project
from antigravity_tool.schemas.panel import Panel, PanelSize


# Time per panel type in seconds
PANEL_READ_TIMES = {
    "dialogue": 3.75,
    "action": 2.0,
    "splash": 4.0,
    "narration": 4.5,
    "default": 3.0,
}


class ReadingTimeEstimator:
    """Estimates reading time based on panel count and types."""

    def __init__(self, project: Project):
        self.project = project

    def estimate_panel(self, panel: Panel) -> float:
        """Estimate reading time for a single panel in seconds."""
        base_time = PANEL_READ_TIMES["default"]

        # Dialogue panels take longer
        if panel.dialogue_bubbles:
            word_count = sum(
                len(b.text.split()) for b in panel.dialogue_bubbles
            )
            base_time = PANEL_READ_TIMES["dialogue"]
            # Add time for extra words (~0.2s per word beyond 10)
            if word_count > 10:
                base_time += (word_count - 10) * 0.2

        # Narration adds time
        if panel.narration_box:
            word_count = len(panel.narration_box.split())
            base_time += word_count * 0.2

        # Splash pages get lingered on
        if panel.panel_size in (PanelSize.FULL_PAGE, PanelSize.DOUBLE_PAGE):
            base_time = max(base_time, PANEL_READ_TIMES["splash"])

        # Action-focused panels are faster
        if not panel.dialogue_bubbles and not panel.narration_box:
            base_time = min(base_time, PANEL_READ_TIMES["action"])

        return base_time

    def estimate_chapter(self, chapter_num: int) -> dict:
        """Estimate reading time for a chapter."""
        panels = self.project.load_panels(chapter_num)
        total_seconds = sum(self.estimate_panel(p) for p in panels)

        return {
            "chapter_num": chapter_num,
            "panel_count": len(panels),
            "total_seconds": total_seconds,
            "total_minutes": total_seconds / 60,
            "formatted": self._format_time(total_seconds),
        }

    def estimate_story(self) -> dict:
        """Estimate reading time for the full story."""
        total_seconds = 0.0
        total_panels = 0
        chapters = []

        if self.project.chapters_dir.exists():
            for d in sorted(self.project.chapters_dir.iterdir()):
                if d.is_dir() and d.name.startswith("chapter-"):
                    try:
                        ch_num = int(d.name.split("-")[1])
                        ch_data = self.estimate_chapter(ch_num)
                        total_seconds += ch_data["total_seconds"]
                        total_panels += ch_data["panel_count"]
                        chapters.append(ch_data)
                    except (IndexError, ValueError):
                        pass

        return {
            "total_seconds": total_seconds,
            "total_minutes": total_seconds / 60,
            "total_panels": total_panels,
            "chapter_count": len(chapters),
            "chapters": chapters,
            "formatted": self._format_time(total_seconds),
        }

    def _format_time(self, seconds: float) -> str:
        """Format seconds into human-readable string."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        if minutes < 60:
            return f"{minutes}m {secs}s"
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"
