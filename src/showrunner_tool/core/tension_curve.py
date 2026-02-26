"""Tension curve visualization: ASCII/Unicode charts for tension across scenes."""

from __future__ import annotations

from typing import Optional

from showrunner_tool.core.project import Project
from showrunner_tool.schemas.scene import Scene


class TensionCurveRenderer:
    """Renders tension curves as ASCII art."""

    BLOCK_CHARS = " ▁▂▃▄▅▆▇█"
    SPARKLINE_CHARS = "▁▂▃▄▅▆▇█"

    def __init__(self, project: Project):
        self.project = project

    def compute_curve(
        self, chapter_num: Optional[int] = None
    ) -> list[dict]:
        """Compute tension data points."""
        if chapter_num:
            scenes = self.project.load_scenes(chapter_num)
            return [
                {
                    "chapter": chapter_num,
                    "scene": s.scene_number,
                    "tension": s.tension_level,
                    "type": s.scene_type.value if hasattr(s.scene_type, "value") else str(s.scene_type),
                    "title": s.title,
                }
                for s in scenes
            ]

        # All chapters
        points = []
        if self.project.chapters_dir.exists():
            for d in sorted(self.project.chapters_dir.iterdir()):
                if d.is_dir() and d.name.startswith("chapter-"):
                    try:
                        ch = int(d.name.split("-")[1])
                        scenes = self.project.load_scenes(ch)
                        for s in scenes:
                            points.append({
                                "chapter": ch,
                                "scene": s.scene_number,
                                "tension": s.tension_level,
                                "type": s.scene_type.value if hasattr(s.scene_type, "value") else str(s.scene_type),
                                "title": s.title,
                            })
                    except (IndexError, ValueError):
                        pass
        return points

    def render_ascii(
        self,
        chapter_num: Optional[int] = None,
        *,
        width: int = 60,
        height: int = 12,
        show_beats: bool = False,
    ) -> str:
        """Render a full ASCII tension curve chart."""
        points = self.compute_curve(chapter_num)
        if not points:
            return "No tension data available."

        tensions = [p["tension"] for p in points]
        max_t = max(tensions) if tensions else 10
        min_t = min(tensions) if tensions else 0

        lines = []
        title = f"Tension Curve" + (f" — Chapter {chapter_num}" if chapter_num else " — Full Story")
        lines.append(title)
        lines.append("─" * width)

        # Render chart
        range_t = max(max_t - min_t, 1)
        for row in range(height, 0, -1):
            threshold = min_t + (row / height) * range_t
            label = f"{int(threshold):>2} │"
            bar = ""
            for i, t in enumerate(tensions):
                if i >= width - 5:
                    break
                if t >= threshold:
                    bar += "█"
                else:
                    bar += " "
            lines.append(f"{label}{bar}")

        # X axis
        lines.append("   └" + "─" * min(len(tensions), width - 5))

        # Labels
        label_line = "    "
        for i, p in enumerate(points):
            if i >= width - 5:
                break
            if i % 3 == 0:
                label_line += str(p["scene"])
            else:
                label_line += " "
        lines.append(label_line)

        # Beat overlay
        if show_beats:
            structure = self.project.load_story_structure()
            if structure and structure.beats:
                lines.append("")
                lines.append("Story Beats:")
                for beat in structure.beats:
                    if beat.content:
                        lines.append(f"  ▸ {beat.beat_name}: {beat.content[:60]}")

        return "\n".join(lines)

    def render_sparkline(
        self, chapter_num: Optional[int] = None
    ) -> str:
        """Render a compact sparkline tension visualization."""
        points = self.compute_curve(chapter_num)
        if not points:
            return "No data"

        tensions = [p["tension"] for p in points]
        max_t = max(tensions) if tensions else 10
        min_t = min(tensions) if tensions else 0
        range_t = max(max_t - min_t, 1)

        sparkline = ""
        for t in tensions:
            idx = int((t - min_t) / range_t * 7)
            idx = max(0, min(7, idx))
            sparkline += self.SPARKLINE_CHARS[idx]

        return sparkline

    def overlay_beats(
        self, chapter_num: Optional[int] = None
    ) -> str:
        """Render tension curve with story beat markers overlaid."""
        return self.render_ascii(chapter_num, show_beats=True)
