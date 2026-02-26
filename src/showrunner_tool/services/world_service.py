"""World service -- world building business logic."""

from __future__ import annotations

from typing import Optional

from showrunner_tool.schemas.world import WorldSettings
from showrunner_tool.services.base import ServiceContext, PromptResult


class WorldService:
    """Encapsulates world-building prompt compilation and data access."""

    def __init__(self, ctx: ServiceContext):
        self.ctx = ctx

    def compile_build_prompt(self) -> PromptResult:
        """Compile the world-building prompt."""
        context = self.ctx.compiler.compile_for_step("world_building")
        prompt = self.ctx.engine.render("world/build_setting.md.j2", **context)
        self.ctx.workflow.mark_step_started("world_building")
        return PromptResult(
            prompt_text=prompt,
            step="world_building",
            template_used="world/build_setting.md.j2",
            context_keys=list(context.keys()),
        )

    def compile_add_location_prompt(self, location_name: str) -> PromptResult:
        """Compile a prompt to add a new location."""
        context = self.ctx.compiler.compile_for_step("world_building")
        context["new_location_name"] = location_name
        prompt = self.ctx.engine.render("world/add_location.md.j2", **context)
        return PromptResult(
            prompt_text=prompt,
            step="world_building",
            template_used="world/add_location.md.j2",
            context_keys=list(context.keys()),
        )

    def compile_add_rule_prompt(self, rule_name: str, category: str = "magic") -> PromptResult:
        """Compile a prompt to add a new world rule."""
        context = self.ctx.compiler.compile_for_step("world_building")
        context["new_rule_name"] = rule_name
        context["new_rule_category"] = category
        prompt = self.ctx.engine.render("world/define_rules.md.j2", **context)
        return PromptResult(
            prompt_text=prompt,
            step="world_building",
            template_used="world/define_rules.md.j2",
            context_keys=list(context.keys()),
        )

    def get_settings(self) -> Optional[WorldSettings]:
        """Load current world settings."""
        return self.ctx.project.load_world_settings()
