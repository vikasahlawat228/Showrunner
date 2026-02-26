"""Context compiler: assembles the right data for each workflow step.

CRITICAL RULE: Never include creative_room data unless the calling code
explicitly requests author-level access. Story prompts must only see
what the reader knows.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

from showrunner_tool.core.project import Project


class ContextCompiler:
    """Assembles context dictionaries for prompt templates.

    Each workflow step gets a tailored context dict containing only
    the data relevant to that step, with creative room isolation enforced.
    Author decisions from the DecisionLog are automatically injected.
    """

    def __init__(self, project: Project):
        self.project = project
        self._decision_log = None

    @property
    def decision_log(self):
        if self._decision_log is None:
            from showrunner_tool.core.session_manager import DecisionLog
            self._decision_log = DecisionLog(self.project.path)
        return self._decision_log

    def _inject_decisions(self, ctx: dict[str, Any], *,
                          chapter: int | None = None,
                          scene: int | None = None,
                          character: str | None = None) -> None:
        """Inject applicable decisions into the context dict."""
        decisions_text = self.decision_log.format_for_prompt(
            chapter=chapter, scene=scene, character=character,
        )
        if decisions_text:
            ctx["author_decisions"] = decisions_text

    def compile_for_step(
        self,
        step: str,
        *,
        access_level: str = "story",
        chapter_num: int | None = None,
        scene_num: int | None = None,
        character_name: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Route to the appropriate compiler method.

        access_level: "story" (default, creative room excluded) or "author" (full access).
        """
        compilers = {
            "world_building": self._compile_world_context,
            "character_creation": self._compile_character_context,
            "story_structure": self._compile_story_context,
            "scene_writing": self._compile_scene_context,
            "screenplay_writing": self._compile_screenplay_context,
            "panel_division": self._compile_panel_context,
            "image_prompt_generation": self._compile_prompt_context,
            "evaluation": self._compile_evaluation_context,
            "creative_room": self._compile_creative_room_context,
        }

        compiler = compilers.get(step)
        if not compiler:
            raise ValueError(f"Unknown workflow step: {step}")

        return compiler(
            access_level=access_level,
            chapter_num=chapter_num,
            scene_num=scene_num,
            character_name=character_name,
            **kwargs,
        )

    def _base_context(self) -> dict[str, Any]:
        """Common context available to all steps."""
        return {
            "project_name": self.project.name,
            "project_variables": self.project.variables,
        }

    def _compile_world_context(self, **kwargs: Any) -> dict[str, Any]:
        ctx = self._base_context()
        ctx["narrative_style"] = self._load_narrative_style()
        # For world building, we also include existing world data for expansion
        ws = self.project.load_world_settings()
        if ws:
            ctx["existing_world"] = ws.model_dump(mode="json")
        self._inject_decisions(ctx)
        return ctx

    def _compile_character_context(self, **kwargs: Any) -> dict[str, Any]:
        ctx = self._base_context()
        ctx["world_summary"] = self._load_world_summary()
        ctx["existing_characters"] = [
            c.model_dump(mode="json")
            for c in self.project.load_all_characters(filter_secrets=True)
        ]
        ctx["narrative_style"] = self._load_narrative_style()
        character_name = kwargs.get("character_name")
        self._inject_decisions(ctx, character=character_name)
        return ctx

    def _compile_story_context(self, **kwargs: Any) -> dict[str, Any]:
        ctx = self._base_context()
        ctx["world_summary"] = self._load_world_summary()
        ctx["characters"] = [
            {"name": c.name, "role": c.role.value, "one_line": c.one_line}
            for c in self.project.load_all_characters(filter_secrets=True)
        ]
        ctx["narrative_style"] = self._load_narrative_style()
        existing = self.project.load_story_structure()
        if existing:
            ctx["existing_structure"] = existing.model_dump(mode="json")
        self._inject_decisions(ctx)
        return ctx

    def _compile_scene_context(
        self,
        *,
        chapter_num: int | None = None,
        scene_num: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        ctx = self._base_context()
        ctx["world_summary"] = self._load_world_summary()
        ctx["narrative_style"] = self._load_narrative_style()

        # Load characters (filtered - no secrets)
        ctx["characters"] = [
            c.model_dump(mode="json")
            for c in self.project.load_all_characters(filter_secrets=True)
        ]

        # Story structure for beat reference
        structure = self.project.load_story_structure()
        if structure:
            ctx["story_structure"] = structure.model_dump(mode="json")

        # Reader knowledge state (constrain what this scene can reference)
        if chapter_num:
            chapter_id = f"chapter-{chapter_num:02d}"
            rk = self.project.load_reader_knowledge(chapter_id)
            if rk:
                ctx["reader_knowledge"] = rk.model_dump(mode="json")

            # Previous scenes for continuity
            scenes = self.project.load_scenes(chapter_num)
            if scenes:
                ctx["previous_scenes"] = [
                    {"title": s.title, "closing_state": s.closing_state, "reveals": s.reveals}
                    for s in scenes
                ]

        self._inject_decisions(ctx, chapter=chapter_num, scene=scene_num)
        return ctx

    def _compile_screenplay_context(
        self,
        *,
        chapter_num: int | None = None,
        scene_num: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        ctx = self._base_context()

        # Load the scene to convert
        if chapter_num and scene_num:
            scenes = self.project.load_scenes(chapter_num)
            target = next((s for s in scenes if s.scene_number == scene_num), None)
            if target:
                ctx["scene"] = target.model_dump(mode="json")

        # Characters with speech patterns
        ctx["characters"] = [
            {
                "name": c.name,
                "id": c.id,
                "speech_pattern": c.personality.speech_pattern,
                "verbal_tics": c.personality.verbal_tics,
                "traits": c.personality.traits,
            }
            for c in self.project.load_all_characters(filter_secrets=True)
        ]

        ctx["narrative_style"] = self._load_narrative_style()
        self._inject_decisions(ctx, chapter=chapter_num, scene=scene_num)
        return ctx

    def _compile_panel_context(
        self,
        *,
        chapter_num: int | None = None,
        scene_num: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        ctx = self._base_context()

        # Screenplay to divide
        if chapter_num:
            screenplays = self.project.load_screenplays(chapter_num)
            if scene_num and screenplays:
                target = next(
                    (sp for sp in screenplays if sp.scene_id == f"scene-{scene_num:02d}"),
                    screenplays[0] if screenplays else None,
                )
                if target:
                    ctx["screenplay"] = target.model_dump(mode="json")

        # Visual style guide
        ctx["visual_style"] = self._load_visual_style()

        # Character DNA blocks for the image prompts
        ctx["character_dna_blocks"] = {
            c.name: c.dna.to_prompt_block()
            for c in self.project.load_all_characters(filter_secrets=False)
            if c.dna.face.face_shape  # Only include characters with DNA
        }

        self._inject_decisions(ctx, chapter=chapter_num, scene=scene_num)
        return ctx

    def _compile_prompt_context(
        self,
        *,
        chapter_num: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        ctx = self._base_context()

        if chapter_num:
            ctx["panels"] = [
                p.model_dump(mode="json")
                for p in self.project.load_panels(chapter_num)
            ]

        # Visual style for tokens
        ctx["visual_style"] = self._load_visual_style()

        # All character DNA blocks
        ctx["character_dna_blocks"] = {
            c.name: c.dna.to_prompt_block()
            for c in self.project.load_all_characters(filter_secrets=False)
            if c.dna.face.face_shape
        }

        return ctx

    def _compile_evaluation_context(
        self,
        *,
        access_level: str = "author",
        chapter_num: int | None = None,
        scene_num: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Evaluation gets FULL access including creative room."""
        ctx = self._base_context()
        ctx["world_summary"] = self._load_world_summary()
        ctx["characters"] = [
            c.model_dump(mode="json")
            for c in self.project.load_all_characters(filter_secrets=False)
        ]
        ctx["narrative_style"] = self._load_narrative_style()
        ctx["visual_style"] = self._load_visual_style()

        structure = self.project.load_story_structure()
        if structure:
            ctx["story_structure"] = structure.model_dump(mode="json")

        # AUTHOR-LEVEL: Include creative room
        if access_level == "author":
            creative_room = self.project.load_creative_room()
            if creative_room:
                ctx["creative_room"] = creative_room.model_dump(mode="json")

            if chapter_num:
                chapter_id = f"chapter-{chapter_num:02d}"
                rk = self.project.load_reader_knowledge(chapter_id)
                if rk:
                    ctx["reader_knowledge"] = rk.model_dump(mode="json")

        return ctx

    def _compile_creative_room_context(self, **kwargs: Any) -> dict[str, Any]:
        """Full creative room access for author-only commands."""
        ctx = self._base_context()
        creative_room = self.project.load_creative_room()
        if creative_room:
            ctx["creative_room"] = creative_room.model_dump(mode="json")
        ctx["characters"] = [
            c.model_dump(mode="json")
            for c in self.project.load_all_characters(filter_secrets=False)
        ]
        ctx["world_summary"] = self._load_world_summary()
        return ctx

    # ── Helpers ───────────────────────────────────────────────────

    def _load_world_summary(self) -> dict[str, Any]:
        ws = self.project.load_world_settings()
        if not ws:
            return {}
        return {
            "name": ws.name,
            "genre": ws.genre,
            "time_period": ws.time_period,
            "tone": ws.tone,
            "description": ws.description,
            "technology_level": ws.technology_level,
            "rules": self.project.load_world_rules(filter_hidden=True),
        }

    def _load_narrative_style(self) -> dict[str, Any]:
        ns = self.project.load_narrative_style_guide()
        if not ns:
            return {}
        return ns.model_dump(mode="json")

    def _load_visual_style(self) -> dict[str, Any]:
        vs = self.project.load_visual_style_guide()
        if not vs:
            return {}
        return vs.model_dump(mode="json")
