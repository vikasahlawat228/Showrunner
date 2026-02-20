"""Character repository -- CRUD for character YAML files."""

from __future__ import annotations

from pathlib import Path

from antigravity_tool.repositories.base import YAMLRepository
from antigravity_tool.schemas.character import Character


class CharacterRepository(YAMLRepository[Character]):
    """Manages character YAML files in the characters/ directory."""

    def __init__(self, characters_dir: Path):
        super().__init__(characters_dir, Character)

    def _slug(self, name: str) -> str:
        return name.lower().replace(" ", "_")

    def get(self, name: str) -> Character | None:
        """Load a character by name. Returns None if not found."""
        slug = self._slug(name)
        path = self.base_dir / f"{slug}.yaml"
        return self._load_file_optional(path)

    def get_all(self, filter_secrets: bool = True) -> list[Character]:
        """Load all characters, optionally filtering hidden relationships."""
        characters = []
        for f in self._list_files():
            char = self._load_file(f)
            if filter_secrets:
                char.relationships = [
                    r for r in char.relationships if r.known_to_reader
                ]
            characters.append(char)
        return characters

    def save(self, character: Character) -> Path:
        """Save a character to disk. File name derived from character name."""
        slug = self._slug(character.name)
        path = self.base_dir / f"{slug}.yaml"
        return self._save_file(path, character)
