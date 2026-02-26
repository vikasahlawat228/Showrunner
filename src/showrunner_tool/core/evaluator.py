"""Story evaluation engine - generates evaluation prompts with author-level context."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from showrunner_tool.core.project import Project
from showrunner_tool.core.context_compiler import ContextCompiler
from showrunner_tool.core.template_engine import TemplateEngine


class Evaluator:
    """Orchestrates evaluation by assembling context and rendering evaluation prompts."""

    def __init__(self, project: Project):
        self.project = project
        self.compiler = ContextCompiler(project)
        self.template_engine = TemplateEngine(project.user_prompts_dir)

    def evaluate_scene(
        self,
        chapter_num: int,
        scene_num: int,
        criteria: list[str] | None = None,
    ) -> str:
        """Generate an evaluation prompt for a scene. Returns assembled prompt text."""
        if criteria is None:
            criteria = ["pacing", "dialogue", "consistency", "emotional_arc"]

        ctx = self.compiler.compile_for_step(
            "evaluation",
            access_level="author",
            chapter_num=chapter_num,
            scene_num=scene_num,
        )
        ctx["criteria"] = criteria

        # Load the scene content
        scenes = self.project.load_scenes(chapter_num)
        target = next((s for s in scenes if s.scene_number == scene_num), None)
        if target:
            ctx["scene"] = target.model_dump(mode="json")

        return self.template_engine.render("evaluate/evaluate_scene.md.j2", **ctx)

    def evaluate_panel_sequence(self, chapter_num: int) -> str:
        """Generate an evaluation prompt for panel visual variety."""
        panels = self.project.load_panels(chapter_num)

        # Statistical analysis before LLM evaluation
        shot_types = [p.shot_type.value for p in panels]
        angles = [p.camera_angle.value for p in panels]
        sizes = [p.panel_size.value for p in panels]

        stats = {
            "total_panels": len(panels),
            "shot_type_distribution": dict(Counter(shot_types)),
            "angle_distribution": dict(Counter(angles)),
            "size_distribution": dict(Counter(sizes)),
            "consecutive_same_shot": _count_consecutive_repeats(shot_types),
            "consecutive_same_angle": _count_consecutive_repeats(angles),
        }

        ctx = self.compiler.compile_for_step(
            "evaluation",
            access_level="author",
            chapter_num=chapter_num,
        )
        ctx["panels"] = [p.model_dump(mode="json") for p in panels]
        ctx["statistics"] = stats

        return self.template_engine.render(
            "evaluate/evaluate_panel_composition.md.j2", **ctx
        )

    def evaluate_consistency(self, chapter_num: int) -> str:
        """Generate a cross-reference consistency check prompt."""
        ctx = self.compiler.compile_for_step(
            "evaluation",
            access_level="author",
            chapter_num=chapter_num,
        )

        # Load all chapter data for cross-referencing
        scenes = self.project.load_scenes(chapter_num)
        ctx["scenes"] = [s.model_dump(mode="json") for s in scenes]
        ctx["screenplays"] = [
            sp.model_dump(mode="json")
            for sp in self.project.load_screenplays(chapter_num)
        ]

        return self.template_engine.render(
            "evaluate/evaluate_consistency.md.j2", **ctx
        )

    def evaluate_dramatic_irony(self, chapter_num: int, scene_num: int) -> str:
        """Compare reader knowledge vs author secrets for irony opportunities."""
        ctx = self.compiler.compile_for_step(
            "evaluation",
            access_level="author",
            chapter_num=chapter_num,
            scene_num=scene_num,
        )

        # Load the specific scene
        scenes = self.project.load_scenes(chapter_num)
        target = next((s for s in scenes if s.scene_number == scene_num), None)
        if target:
            ctx["scene"] = target.model_dump(mode="json")

        return self.template_engine.render(
            "evaluate/evaluate_dramatic_irony.md.j2", **ctx
        )


def _count_consecutive_repeats(items: list[str]) -> int:
    """Count the maximum number of consecutive identical items."""
    if not items:
        return 0
    max_count = 1
    current_count = 1
    for i in range(1, len(items)):
        if items[i] == items[i - 1]:
            current_count += 1
            max_count = max(max_count, current_count)
        else:
            current_count = 1
    return max_count
