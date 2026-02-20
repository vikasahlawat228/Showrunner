"""Scene service -- scene writing and screenplay business logic."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from antigravity_tool.errors import EntityNotFoundError
from antigravity_tool.schemas.scene import Scene
from antigravity_tool.schemas.screenplay import Screenplay
from antigravity_tool.services.base import ServiceContext, PromptResult


class SceneService:
    """Encapsulates scene and screenplay prompt compilation and data access."""

    def __init__(self, ctx: ServiceContext):
        self.ctx = ctx

    def compile_write_prompt(
        self,
        chapter: int,
        scene: int,
        beat_reference: str | None = None,
        scene_type: str | None = None,
    ) -> PromptResult:
        """Compile a scene writing prompt with full context injection."""
        context = self.ctx.compiler.compile_for_step(
            "scene_writing",
            chapter_num=chapter,
            scene_num=scene,
        )
        context["chapter_num"] = chapter
        context["scene_num"] = scene
        if beat_reference:
            context["beat_reference"] = beat_reference
        if scene_type:
            context["scene_type"] = scene_type

        prompt = self.ctx.engine.render("scene/write_scene.md.j2", **context)
        self.ctx.workflow.mark_step_started("scene_writing")
        return PromptResult(
            prompt_text=prompt,
            step="scene_writing",
            template_used="scene/write_scene.md.j2",
            context_keys=list(context.keys()),
        )

    def compile_plan_prompt(self, chapter: int) -> PromptResult:
        """Compile a scene planning prompt for a chapter."""
        context = self.ctx.compiler.compile_for_step("scene_writing", chapter_num=chapter)
        context["chapter_num"] = chapter
        prompt = self.ctx.engine.render("scene/plan_scenes.md.j2", **context)
        return PromptResult(
            prompt_text=prompt,
            step="scene_writing",
            template_used="scene/plan_scenes.md.j2",
            context_keys=list(context.keys()),
        )

    def compile_screenplay_prompt(self, chapter: int, scene: int) -> PromptResult:
        """Compile a screenplay conversion prompt."""
        context = self.ctx.compiler.compile_for_step(
            "screenplay_writing",
            chapter_num=chapter,
            scene_num=scene,
        )
        context["chapter_num"] = chapter
        context["scene_num"] = scene
        prompt = self.ctx.engine.render("screenplay/scene_to_screenplay.md.j2", **context)
        self.ctx.workflow.mark_step_started("screenplay_writing")
        return PromptResult(
            prompt_text=prompt,
            step="screenplay_writing",
            template_used="screenplay/scene_to_screenplay.md.j2",
            context_keys=list(context.keys()),
        )

    def list_scenes(self, chapter: int) -> list[Scene]:
        """List all scenes in a chapter."""
        return self.ctx.project.load_scenes(chapter)

    def get_scene(self, chapter: int, scene_number: int) -> Scene:
        """Load a single scene by chapter and scene number."""
        scenes = self.ctx.project.load_scenes(chapter)
        for s in scenes:
            if s.scene_number == scene_number:
                return s
        raise EntityNotFoundError("Scene", f"chapter-{chapter}-scene-{scene_number}")

    def update_scene(self, chapter: int, scene_number: int, updates: dict) -> Scene:
        """Apply partial updates to a scene and persist to disk."""
        scene = self.get_scene(chapter, scene_number)
        for key, value in updates.items():
            if hasattr(scene, key):
                setattr(scene, key, value)
        scene.updated_at = datetime.now(timezone.utc)
        self.ctx.project.save_scene(scene, chapter)
        return scene

    def list_screenplays(self, chapter: int) -> list[Screenplay]:
        """List all screenplays in a chapter."""
        return self.ctx.project.load_screenplays(chapter)
