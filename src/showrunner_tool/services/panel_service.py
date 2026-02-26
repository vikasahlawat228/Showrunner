"""Panel service -- panel division and image prompt business logic."""

from __future__ import annotations

from showrunner_tool.schemas.panel import Panel
from showrunner_tool.services.base import ServiceContext, PromptResult


class PanelService:
    """Encapsulates panel division prompt compilation and data access."""

    def __init__(self, ctx: ServiceContext):
        self.ctx = ctx

    def compile_divide_prompt(self, chapter: int, scene: int) -> PromptResult:
        """Compile a panel division prompt."""
        context = self.ctx.compiler.compile_for_step(
            "panel_division",
            chapter_num=chapter,
            scene_num=scene,
        )
        context["chapter_num"] = chapter
        context["scene_num"] = scene
        prompt = self.ctx.engine.render("panel/divide_panels.md.j2", **context)
        self.ctx.workflow.mark_step_started("panel_division")
        return PromptResult(
            prompt_text=prompt,
            step="panel_division",
            template_used="panel/divide_panels.md.j2",
            context_keys=list(context.keys()),
        )

    def compile_image_prompt(self, chapter: int) -> PromptResult:
        """Compile an image prompt generation prompt."""
        context = self.ctx.compiler.compile_for_step(
            "image_prompt_generation",
            chapter_num=chapter,
        )
        prompt = self.ctx.engine.render("panel/panel_to_image_prompt.md.j2", **context)
        self.ctx.workflow.mark_step_started("image_prompt_generation")
        return PromptResult(
            prompt_text=prompt,
            step="image_prompt_generation",
            template_used="panel/panel_to_image_prompt.md.j2",
            context_keys=list(context.keys()),
        )

    def list_panels(self, chapter: int) -> list[Panel]:
        """List all panels in a chapter."""
        return self.ctx.project.load_panels(chapter)
