"""Pacing analysis engine: compute metrics and detect pacing issues."""

from __future__ import annotations

from typing import Optional

from antigravity_tool.core.project import Project
from antigravity_tool.schemas.pacing import PacingMetrics, PacingIssue, PacingReport
from antigravity_tool.schemas.scene import Scene, SceneType


class PacingAnalyzer:
    """Analyzes pacing across scenes and chapters."""

    def __init__(self, project: Project):
        self.project = project

    def analyze_chapter(self, chapter_num: int) -> PacingReport:
        """Analyze pacing for a single chapter."""
        scenes = self.project.load_scenes(chapter_num)
        panels = self.project.load_panels(chapter_num)

        metrics = self._compute_metrics(scenes, len(panels), chapter_num)
        issues = self._detect_pacing_issues(metrics, scenes)
        recommendations = self._generate_recommendations(metrics, issues)

        return PacingReport(
            chapter_num=chapter_num,
            metrics=metrics,
            issues=issues,
            recommendations=recommendations,
        )

    def analyze_story(self) -> PacingReport:
        """Analyze pacing across the entire story."""
        all_scenes: list[Scene] = []
        total_panels = 0

        chapters_dir = self.project.chapters_dir
        if chapters_dir.exists():
            for d in sorted(chapters_dir.iterdir()):
                if d.is_dir() and d.name.startswith("chapter-"):
                    try:
                        ch_num = int(d.name.split("-")[1])
                        all_scenes.extend(self.project.load_scenes(ch_num))
                        total_panels += len(self.project.load_panels(ch_num))
                    except (IndexError, ValueError):
                        pass

        metrics = self._compute_metrics(all_scenes, total_panels)
        issues = self._detect_pacing_issues(metrics, all_scenes)
        recommendations = self._generate_recommendations(metrics, issues)

        return PacingReport(
            metrics=metrics,
            issues=issues,
            recommendations=recommendations,
        )

    def _compute_metrics(
        self, scenes: list[Scene], total_panels: int, chapter_num: Optional[int] = None
    ) -> PacingMetrics:
        """Compute pacing metrics from scenes."""
        if not scenes:
            return PacingMetrics(chapter_num=chapter_num)

        # Scene type distribution
        type_dist: dict[str, int] = {}
        for scene in scenes:
            st = scene.scene_type.value if hasattr(scene.scene_type, "value") else str(scene.scene_type)
            type_dist[st] = type_dist.get(st, 0) + 1

        # Tension metrics
        tensions = [s.tension_level for s in scenes]
        avg_tension = sum(tensions) / len(tensions) if tensions else 0
        variance = sum((t - avg_tension) ** 2 for t in tensions) / len(tensions) if tensions else 0

        # Density
        dialogue_count = type_dist.get("dialogue", 0)
        action_count = type_dist.get("action", 0) + type_dist.get("confrontation", 0) + type_dist.get("chase", 0)
        emotional_count = type_dist.get("emotional", 0) + type_dist.get("calm_before_storm", 0)

        total = len(scenes)

        # Estimated panels per scene
        estimated_panels = [s.estimated_panels or 0 for s in scenes if s.estimated_panels]
        avg_panels = sum(estimated_panels) / len(estimated_panels) if estimated_panels else 0
        panel_variance = (
            sum((p - avg_panels) ** 2 for p in estimated_panels) / len(estimated_panels)
            if estimated_panels else 0
        )

        return PacingMetrics(
            chapter_num=chapter_num,
            total_scenes=total,
            total_panels=total_panels,
            dialogue_density=dialogue_count / total if total else 0,
            action_density=action_count / total if total else 0,
            emotional_density=emotional_count / total if total else 0,
            scene_type_distribution=type_dist,
            avg_tension=avg_tension,
            min_tension=min(tensions) if tensions else 0,
            max_tension=max(tensions) if tensions else 0,
            tension_variance=variance,
            tension_progression=tensions,
            avg_scene_panels=avg_panels,
            scene_length_variance=panel_variance,
        )

    def _detect_pacing_issues(
        self, metrics: PacingMetrics, scenes: list[Scene]
    ) -> list[PacingIssue]:
        """Detect pacing problems from metrics."""
        issues: list[PacingIssue] = []

        # Flat tension: variance too low over many scenes
        if metrics.total_scenes > 3 and metrics.tension_variance < 2.0:
            issues.append(PacingIssue(
                issue_type="flat_tension",
                description=f"Tension variance is very low ({metrics.tension_variance:.1f}). Scenes feel monotonous.",
                suggestion="Introduce higher peaks and lower valleys. Alternate high-tension and cool-down scenes.",
                location=f"Chapter {metrics.chapter_num}" if metrics.chapter_num else "Story-wide",
            ))

        # All action, no rest
        if metrics.action_density > 0.6 and metrics.total_scenes > 4:
            issues.append(PacingIssue(
                issue_type="action_fatigue",
                description=f"Action density is {metrics.action_density:.0%}. Risk of reader fatigue.",
                suggestion="Add dialogue, emotional, or worldbuilding scenes between action sequences.",
                location=f"Chapter {metrics.chapter_num}" if metrics.chapter_num else "Story-wide",
            ))

        # All dialogue, no action
        if metrics.dialogue_density > 0.6 and metrics.total_scenes > 4:
            issues.append(PacingIssue(
                issue_type="dialogue_heavy",
                description=f"Dialogue density is {metrics.dialogue_density:.0%}. Pacing may feel slow.",
                suggestion="Break up dialogue scenes with action beats or visual set-pieces.",
                location=f"Chapter {metrics.chapter_num}" if metrics.chapter_num else "Story-wide",
            ))

        # Consecutive same-type scenes
        if len(scenes) >= 3:
            for i in range(2, len(scenes)):
                if (scenes[i].scene_type == scenes[i-1].scene_type == scenes[i-2].scene_type
                        and scenes[i].scene_type != SceneType.CUSTOM):
                    issues.append(PacingIssue(
                        issue_type="repetitive_type",
                        description=f"Three consecutive {scenes[i].scene_type.value} scenes ({scenes[i-2].scene_number}-{scenes[i].scene_number}).",
                        suggestion="Vary scene types for better rhythm.",
                        location=f"Scenes {scenes[i-2].scene_number}-{scenes[i].scene_number}",
                    ))
                    break

        # Tension never peaks
        if metrics.max_tension <= 6 and metrics.total_scenes > 5:
            issues.append(PacingIssue(
                issue_type="no_peak",
                description=f"Maximum tension is only {metrics.max_tension}/10. No dramatic high point.",
                suggestion="Add a climactic scene with tension level 8-10.",
                location=f"Chapter {metrics.chapter_num}" if metrics.chapter_num else "Story-wide",
            ))

        return issues

    def _generate_recommendations(
        self, metrics: PacingMetrics, issues: list[PacingIssue]
    ) -> list[str]:
        """Generate actionable recommendations."""
        recs = []

        if not issues:
            recs.append("Pacing looks balanced! No major issues detected.")
            return recs

        issue_types = {i.issue_type for i in issues}

        if "flat_tension" in issue_types:
            recs.append("Consider adding a reveal or confrontation scene to spike tension.")

        if "action_fatigue" in issue_types:
            recs.append("Insert a 'calm before the storm' or emotional scene after every 2-3 action scenes.")

        if "dialogue_heavy" in issue_types:
            recs.append("Add a training or chase scene to inject physical energy.")

        if "no_peak" in issue_types:
            recs.append("Plan a climactic confrontation or revelation scene for this chapter.")

        # General recommendations based on metrics
        if metrics.total_scenes > 0 and metrics.emotional_density < 0.1:
            recs.append("Consider adding emotional beats — character vulnerability creates reader investment.")

        return recs
