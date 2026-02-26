"""Project analytics: compute comprehensive project statistics."""

from __future__ import annotations

from showrunner_tool.core.project import Project
from showrunner_tool.core.reading_time import ReadingTimeEstimator
from showrunner_tool.schemas.analytics import AnalyticsReport, CharacterStats


class ProjectAnalytics:
    """Computes comprehensive project analytics."""

    def __init__(self, project: Project):
        self.project = project

    def compute(self) -> AnalyticsReport:
        """Compute full analytics report."""
        report = AnalyticsReport(project_name=self.project.name)

        # Characters
        characters = self.project.load_all_characters(filter_secrets=False)
        report.character_count = len(characters)

        char_stats = {c.name: CharacterStats(name=c.name, role=c.role.value) for c in characters}

        # Chapters, scenes, panels
        total_scenes = 0
        total_panels = 0
        total_words = 0
        images_generated = 0
        images_composited = 0
        scene_types: dict[str, int] = {}
        chapters_complete = 0

        if self.project.chapters_dir.exists():
            chapter_dirs = sorted(
                d for d in self.project.chapters_dir.iterdir()
                if d.is_dir() and d.name.startswith("chapter-")
            )
            report.total_chapters = len(chapter_dirs)

            for d in chapter_dirs:
                try:
                    ch_num = int(d.name.split("-")[1])
                except (IndexError, ValueError):
                    continue

                scenes = self.project.load_scenes(ch_num)
                total_scenes += len(scenes)

                # Track scene completion
                has_scenes = len(scenes) > 0

                for scene in scenes:
                    st = scene.scene_type.value if hasattr(scene.scene_type, "value") else str(scene.scene_type)
                    scene_types[st] = scene_types.get(st, 0) + 1

                    # Character appearances
                    for char_name in scene.characters_present:
                        if char_name in char_stats:
                            char_stats[char_name].scene_appearances += 1

                    # Count words in key events and summaries
                    for event in scene.key_events:
                        total_words += len(event.split())
                    if scene.summary:
                        total_words += len(scene.summary.split())

                panels = self.project.load_panels(ch_num)
                total_panels += len(panels)

                for panel in panels:
                    # Character appearances in panels
                    for char_in_panel in panel.characters:
                        if char_in_panel.character_name in char_stats:
                            char_stats[char_in_panel.character_name].panel_appearances += 1

                    # Dialogue stats
                    for bubble in panel.dialogue_bubbles:
                        if bubble.character_name in char_stats:
                            char_stats[bubble.character_name].dialogue_count += 1
                            char_stats[bubble.character_name].total_words += len(bubble.text.split())
                        total_words += len(bubble.text.split())

                    if panel.narration_box:
                        total_words += len(panel.narration_box.split())

                # Check for images
                images_dir = d / "images"
                if images_dir.exists():
                    images_generated += len(list(images_dir.glob("*.png")))

                composited_dir = d / "composited"
                if composited_dir.exists():
                    images_composited += len(list(composited_dir.glob("*.png")))

                # Check chapter completion
                if has_scenes and len(panels) > 0:
                    chapters_complete += 1

        report.total_scenes = total_scenes
        report.total_panels = total_panels
        report.total_words = total_words
        report.images_generated = images_generated
        report.images_composited = images_composited
        report.chapters_complete = chapters_complete
        report.scenes_written = total_scenes
        report.panels_with_images = images_generated
        report.scene_type_distribution = scene_types

        # Completion percentage
        if report.total_chapters > 0:
            report.completion_percentage = (chapters_complete / report.total_chapters) * 100

        # Character stats sorted by appearances
        report.character_stats = sorted(
            char_stats.values(),
            key=lambda s: s.scene_appearances + s.panel_appearances,
            reverse=True,
        )

        # Reading time
        estimator = ReadingTimeEstimator(self.project)
        time_data = estimator.estimate_story()
        report.estimated_reading_time = time_data["formatted"]
        report.estimated_reading_seconds = time_data["total_seconds"]

        return report
