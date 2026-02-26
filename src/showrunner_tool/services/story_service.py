"""Story service -- story structure business logic."""

from __future__ import annotations

from typing import Optional, Any

from showrunner_tool.schemas.story_structure import StoryStructure, SubArc, SubArcType
from showrunner_tool.services.base import ServiceContext, PromptResult
from showrunner_tool.utils.io import write_yaml


class StoryService:
    """Encapsulates story structure prompt compilation and data access."""

    def __init__(self, ctx: ServiceContext):
        self.ctx = ctx

    def compile_outline_prompt(self, structure_type: str = "save_the_cat") -> PromptResult:
        """Compile a story outline prompt."""
        context = self.ctx.compiler.compile_for_step("story_structure")
        context["structure_type"] = structure_type
        prompt = self.ctx.engine.render("story/outline_beats.md.j2", **context)
        self.ctx.workflow.mark_step_started("story_structure")
        return PromptResult(
            prompt_text=prompt,
            step="story_structure",
            template_used="story/outline_beats.md.j2",
            context_keys=list(context.keys()),
        )

    def compile_plan_arcs_prompt(self) -> PromptResult:
        """Compile a character arc planning prompt."""
        context = self.ctx.compiler.compile_for_step("story_structure")
        prompt = self.ctx.engine.render("story/plan_arc.md.j2", **context)
        return PromptResult(
            prompt_text=prompt,
            step="story_structure",
            template_used="story/plan_arc.md.j2",
            context_keys=list(context.keys()),
        )

    def compile_sub_arc_prompt(
        self,
        sub_arc_name: str,
        arc_type: str = "custom",
        chapter_start: int | None = None,
        chapter_end: int | None = None,
    ) -> PromptResult:
        """Compile a sub-arc planning prompt."""
        context = self.ctx.compiler.compile_for_step("story_structure")
        context["sub_arc_name"] = sub_arc_name
        context["sub_arc_type"] = arc_type
        context["chapter_start"] = chapter_start
        context["chapter_end"] = chapter_end
        context["parent_beat"] = None
        prompt = self.ctx.engine.render("story/plan_sub_arc.md.j2", **context)
        return PromptResult(
            prompt_text=prompt,
            step="story_structure",
            template_used="story/plan_sub_arc.md.j2",
            context_keys=list(context.keys()),
        )

    def add_sub_arc(
        self,
        name: str,
        arc_type: str = "custom",
        description: str = "",
        chapter_start: int | None = None,
        chapter_end: int | None = None,
    ) -> SubArc:
        """Add a sub-arc to the story structure and persist."""
        structure = self.ctx.project.load_story_structure()
        if not structure:
            from showrunner_tool.errors import WorkflowError
            raise WorkflowError("No story structure found. Run 'showrunner story outline' first.")

        try:
            sub_arc_type = SubArcType(arc_type)
        except ValueError:
            sub_arc_type = SubArcType.CUSTOM

        sub_arc = SubArc(
            name=name,
            arc_type=sub_arc_type,
            description=description,
            chapter_start=chapter_start,
            chapter_end=chapter_end,
        )
        structure.sub_arcs.append(sub_arc)

        structure_path = self.ctx.project.path / "story" / "structure.yaml"
        write_yaml(structure_path, structure.model_dump(mode="json"))
        return sub_arc

    def get_structure(self) -> Optional[StoryStructure]:
        """Load the current story structure."""
        return self.ctx.project.load_story_structure()
