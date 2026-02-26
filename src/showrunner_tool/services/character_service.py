"""Character service -- character management business logic."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from showrunner_tool.schemas.character import Character
from showrunner_tool.services.base import ServiceContext, PromptResult


class CharacterService:
    """Encapsulates character prompt compilation and data access."""

    def __init__(self, ctx: ServiceContext):
        self.ctx = ctx

    def compile_create_prompt(self, name: str, role: str = "supporting") -> PromptResult:
        """Compile a character creation prompt."""
        context = self.ctx.compiler.compile_for_step("character_creation")
        context["new_character_name"] = name
        context["new_character_role"] = role
        prompt = self.ctx.engine.render("character/create_character.md.j2", **context)
        self.ctx.workflow.mark_step_started("character_creation")
        return PromptResult(
            prompt_text=prompt,
            step="character_creation",
            template_used="character/create_character.md.j2",
            context_keys=list(context.keys()),
        )

    def compile_dna_prompt(self, name: str) -> PromptResult:
        """Compile a Character DNA generation prompt."""
        char = self.ctx.project.load_character(name)
        context = {
            "character": char.model_dump(mode="json") if char else {"name": name},
            "project_name": self.ctx.project.name,
        }
        prompt = self.ctx.engine.render("character/generate_dna_block.md.j2", **context)
        return PromptResult(
            prompt_text=prompt,
            step="character_creation",
            template_used="character/generate_dna_block.md.j2",
            context_keys=list(context.keys()),
        )

    def get(self, name: str) -> Optional[Character]:
        """Load a character by name."""
        return self.ctx.project.load_character(name)

    def list_all(self, filter_secrets: bool = True) -> list[Character]:
        """List all characters."""
        return self.ctx.project.load_all_characters(filter_secrets=filter_secrets)

    def save(self, character: Character) -> Path:
        """Save a character to disk."""
        return self.ctx.project.save_character(character)
