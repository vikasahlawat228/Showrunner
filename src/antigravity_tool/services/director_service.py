"""Director service -- task-based director that returns structured results.

Unlike the original Director agent (which prints to console and returns None),
this service returns DirectorResult objects that can be consumed by both
CLI commands and API endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import yaml

from antigravity_tool.core.workflow import WorkflowState
from antigravity_tool.services.base import ServiceContext


@dataclass
class DirectorResult:
    """Structured result from a Director action."""

    step_executed: str
    status: str  # "success", "skipped", "error"
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    content_generated: Optional[str] = None
    next_step: Optional[str] = None
    message: str = ""


class DirectorService:
    """Task-based director that returns results instead of printing.

    Can be used by both the CLI (which prints results) and the API
    (which returns them as JSON).
    """

    def __init__(self, ctx: ServiceContext, writer=None):
        self.ctx = ctx
        self.workflow = WorkflowState(ctx.project.path)
        self.writer = writer

    def get_current_step(self) -> str:
        """Get the current workflow step."""
        return self.workflow.get_current_step()

    def act(self, step_override: str | None = None) -> DirectorResult:
        """Analyze state and perform the next action. Returns structured result."""
        step = step_override or self.workflow.get_current_step()

        handlers = {
            "world_building": self._handle_world_building,
            "character_creation": self._handle_character_creation,
            "story_structure": self._handle_story_structure,
            "scene_writing": self._handle_scene_writing,
            "screenplay_writing": self._handle_screenplay_writing,
            "panel_division": self._handle_panel_division,
        }

        handler = handlers.get(step)
        if handler is None:
            return DirectorResult(
                step_executed=step,
                status="error",
                message=f"Unknown step or workflow complete: {step}",
            )

        try:
            return handler()
        except Exception as e:
            return DirectorResult(
                step_executed=step,
                status="error",
                message=f"Director error in {step}: {e}",
            )

    def _parse_yaml_content(self, content: str) -> dict:
        """Shared YAML parsing -- replaces repeated inline code across handlers."""
        clean = content.replace("```yaml", "").replace("```", "").strip()
        return yaml.safe_load(clean)

    def _handle_world_building(self) -> DirectorResult:
        """Handle world building step."""
        if self.ctx.project.load_world_settings():
            self.workflow.mark_step_complete("world_building")
            self.workflow.mark_step_started("character_creation")
            return DirectorResult(
                step_executed="world_building",
                status="skipped",
                next_step="character_creation",
                message="World settings already exist. Moving to character creation.",
            )

        if not self.writer:
            return DirectorResult(
                step_executed="world_building",
                status="error",
                message="No writer agent configured. Cannot generate content.",
            )

        context = self.ctx.compiler.compile_for_step("world_building")
        prompt = self.ctx.engine.render("world/build_setting.md.j2", **context)
        content = self.writer.write(prompt, task_type="World Building")

        from antigravity_tool.utils.io import write_yaml
        try:
            data = self._parse_yaml_content(content)
            output_path = self.ctx.project.world_dir / "settings.yaml"
            self.ctx.project.world_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(output_path, data)
            self.workflow.mark_step_complete("world_building")
            self.workflow.mark_step_started("character_creation")
            return DirectorResult(
                step_executed="world_building",
                status="success",
                files_created=[str(output_path)],
                content_generated=content,
                next_step="character_creation",
                message="World settings generated and saved.",
            )
        except Exception as e:
            return DirectorResult(
                step_executed="world_building",
                status="error",
                content_generated=content,
                message=f"Failed to parse/save world settings: {e}",
            )

    def _handle_character_creation(self) -> DirectorResult:
        """Handle character creation step."""
        chars = self.ctx.project.load_all_characters(filter_secrets=False)
        if chars:
            self.workflow.mark_step_complete("character_creation")
            self.workflow.mark_step_started("story_structure")
            return DirectorResult(
                step_executed="character_creation",
                status="skipped",
                next_step="story_structure",
                message=f"Found {len(chars)} characters. Moving to story structure.",
            )

        if not self.writer:
            return DirectorResult(
                step_executed="character_creation",
                status="error",
                message="No writer agent configured.",
            )

        context = self.ctx.compiler.compile_for_step("character_creation")
        context["new_character_name"] = "Hero"
        context["new_character_role"] = "protagonist"
        prompt = self.ctx.engine.render("character/create_character.md.j2", **context)
        content = self.writer.write(prompt, task_type="Character Creation")

        from antigravity_tool.utils.io import write_yaml
        try:
            data = self._parse_yaml_content(content)
            name = data.get("name", "Hero")
            slug = name.lower().replace(" ", "_")
            output_path = self.ctx.project.characters_dir / f"{slug}.yaml"
            self.ctx.project.characters_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(output_path, data)
            self.workflow.mark_step_complete("character_creation")
            self.workflow.mark_step_started("story_structure")
            return DirectorResult(
                step_executed="character_creation",
                status="success",
                files_created=[str(output_path)],
                content_generated=content,
                next_step="story_structure",
                message=f"Character '{name}' created.",
            )
        except Exception as e:
            return DirectorResult(
                step_executed="character_creation",
                status="error",
                content_generated=content,
                message=f"Failed to save character: {e}",
            )

    def _handle_story_structure(self) -> DirectorResult:
        """Handle story structure step."""
        if self.ctx.project.load_story_structure():
            self.workflow.mark_step_complete("story_structure")
            self.workflow.mark_step_started("scene_writing")
            return DirectorResult(
                step_executed="story_structure",
                status="skipped",
                next_step="scene_writing",
                message="Story structure exists. Moving to scene writing.",
            )

        if not self.writer:
            return DirectorResult(
                step_executed="story_structure",
                status="error",
                message="No writer agent configured.",
            )

        context = self.ctx.compiler.compile_for_step("story_structure")
        context["structure_type"] = "save_the_cat"
        prompt = self.ctx.engine.render("story/outline_beats.md.j2", **context)
        content = self.writer.write(prompt, task_type="Story Outline")

        from antigravity_tool.utils.io import write_yaml
        try:
            data = self._parse_yaml_content(content)
            output_path = self.ctx.project.story_dir / "structure.yaml"
            self.ctx.project.story_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(output_path, data)
            self.workflow.mark_step_complete("story_structure")
            self.workflow.mark_step_started("scene_writing")
            return DirectorResult(
                step_executed="story_structure",
                status="success",
                files_created=[str(output_path)],
                content_generated=content,
                next_step="scene_writing",
                message="Story structure generated and saved.",
            )
        except Exception as e:
            return DirectorResult(
                step_executed="story_structure",
                status="error",
                content_generated=content,
                message=f"Failed to save story structure: {e}",
            )

    def _handle_scene_writing(self) -> DirectorResult:
        """Handle scene writing step."""
        scenes = self.ctx.project.load_scenes(1)
        if scenes:
            self.workflow.mark_step_complete("scene_writing")
            self.workflow.mark_step_started("screenplay_writing")
            return DirectorResult(
                step_executed="scene_writing",
                status="skipped",
                next_step="screenplay_writing",
                message="Chapter 1 scenes exist. Moving to screenplay.",
            )

        if not self.writer:
            return DirectorResult(
                step_executed="scene_writing",
                status="error",
                message="No writer agent configured.",
            )

        context = self.ctx.compiler.compile_for_step("scene_writing", chapter_num=1, scene_num=1)
        context["chapter_num"] = 1
        context["scene_num"] = 1
        prompt = self.ctx.engine.render("scene/write_scene.md.j2", **context)
        content = self.writer.write(prompt, task_type="Scene Writing")

        from antigravity_tool.utils.io import write_yaml
        try:
            data = self._parse_yaml_content(content)
            output_path = self.ctx.project.chapter_dir(1) / "scenes" / "scene-01.yaml"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_yaml(output_path, data)
            self.workflow.mark_step_complete("scene_writing")
            self.workflow.mark_step_started("screenplay_writing")
            return DirectorResult(
                step_executed="scene_writing",
                status="success",
                files_created=[str(output_path)],
                content_generated=content,
                next_step="screenplay_writing",
                message="Scene 1 written and saved.",
            )
        except Exception as e:
            return DirectorResult(
                step_executed="scene_writing",
                status="error",
                content_generated=content,
                message=f"Failed to save scene: {e}",
            )

    def _handle_screenplay_writing(self) -> DirectorResult:
        """Handle screenplay writing step."""
        existing = self.ctx.project.load_screenplays(1)
        if existing:
            self.workflow.mark_step_complete("screenplay_writing")
            self.workflow.mark_step_started("panel_division")
            return DirectorResult(
                step_executed="screenplay_writing",
                status="skipped",
                next_step="panel_division",
                message="Screenplay exists. Moving to panel division.",
            )

        if not self.writer:
            return DirectorResult(
                step_executed="screenplay_writing",
                status="error",
                message="No writer agent configured.",
            )

        context = self.ctx.compiler.compile_for_step("screenplay_writing", chapter_num=1, scene_num=1)
        context["chapter_num"] = 1
        context["scene_num"] = 1
        prompt = self.ctx.engine.render("screenplay/scene_to_screenplay.md.j2", **context)
        content = self.writer.write(prompt, task_type="Screenplay")

        from antigravity_tool.utils.io import write_yaml
        try:
            data = self._parse_yaml_content(content)
            output_path = self.ctx.project.chapter_dir(1) / "screenplay" / "scene-01.yaml"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_yaml(output_path, data)
            self.workflow.mark_step_complete("screenplay_writing")
            self.workflow.mark_step_started("panel_division")
            return DirectorResult(
                step_executed="screenplay_writing",
                status="success",
                files_created=[str(output_path)],
                content_generated=content,
                next_step="panel_division",
                message="Screenplay generated and saved.",
            )
        except Exception as e:
            return DirectorResult(
                step_executed="screenplay_writing",
                status="error",
                content_generated=content,
                message=f"Failed to save screenplay: {e}",
            )

    def _handle_panel_division(self) -> DirectorResult:
        """Handle panel division step."""
        existing = self.ctx.project.load_panels(1)
        if existing:
            self.workflow.mark_step_complete("panel_division")
            return DirectorResult(
                step_executed="panel_division",
                status="skipped",
                message="Panels exist. Workflow complete.",
            )

        if not self.writer:
            return DirectorResult(
                step_executed="panel_division",
                status="error",
                message="No writer agent configured.",
            )

        context = self.ctx.compiler.compile_for_step("panel_division", chapter_num=1, scene_num=1)
        context["chapter_num"] = 1
        context["scene_num"] = 1
        prompt = self.ctx.engine.render("panel/divide_panels.md.j2", **context)
        content = self.writer.write(prompt, task_type="Panel Division")

        from antigravity_tool.utils.io import write_yaml
        try:
            data = self._parse_yaml_content(content)
            output_path = self.ctx.project.chapter_dir(1) / "panels" / "scene-01.yaml"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_yaml(output_path, data)
            self.workflow.mark_step_complete("panel_division")
            return DirectorResult(
                step_executed="panel_division",
                status="success",
                files_created=[str(output_path)],
                content_generated=content,
                message="Panels generated and saved.",
            )
        except Exception as e:
            return DirectorResult(
                step_executed="panel_division",
                status="error",
                content_generated=content,
                message=f"Failed to save panels: {e}",
            )
