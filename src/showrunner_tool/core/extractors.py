"""Auto-extraction utilities for pulling structured data from prose."""

from __future__ import annotations

from showrunner_tool.core.project import Project
from showrunner_tool.core.template_engine import TemplateEngine


class AppearanceExtractor:
    """Generates prompts to extract visual character descriptions from prose."""

    def __init__(self, project: Project):
        self.project = project
        self.template_engine = TemplateEngine(project.user_prompts_dir)

    def generate_extraction_prompt(
        self,
        scene_text: str,
        character_names: list[str],
    ) -> str:
        """Generate a prompt to extract character appearances from scene prose.

        The user/agent sends this prompt to their LLM and gets back structured
        character appearance data that can update Character DNA blocks.
        """
        existing_dna = {}
        for name in character_names:
            char = self.project.load_character(name)
            if char and char.dna.face.face_shape:
                existing_dna[name] = char.dna.to_prompt_block()

        ctx = {
            "scene_text": scene_text,
            "character_names": character_names,
            "existing_dna": existing_dna,
        }

        return self.template_engine.render(
            "character/extract_appearance.md.j2", **ctx
        )


class KnowledgeExtractor:
    """Generates prompts to extract reader knowledge state after a scene."""

    def __init__(self, project: Project):
        self.project = project
        self.template_engine = TemplateEngine(project.user_prompts_dir)

    def generate_extraction_prompt(
        self,
        chapter_num: int,
        scene_num: int,
    ) -> str:
        """Generate a prompt to extract what the reader learned from a scene.

        This auto-updates the reader knowledge state in the creative room.
        """
        scenes = self.project.load_scenes(chapter_num)
        target = next((s for s in scenes if s.scene_number == scene_num), None)

        # Load previous knowledge state
        chapter_id = f"chapter-{chapter_num:02d}"
        prev_knowledge = self.project.load_reader_knowledge(chapter_id)

        ctx = {
            "scene": target.model_dump(mode="json") if target else {},
            "previous_knowledge": prev_knowledge.model_dump(mode="json") if prev_knowledge else {},
            "chapter_num": chapter_num,
            "scene_num": scene_num,
        }

        return self.template_engine.render(
            "creative_room/extract_knowledge.md.j2", **ctx
        )
