"""Story repository -- CRUD for story structure."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from antigravity_tool.schemas.story_structure import StoryStructure
from antigravity_tool.utils.io import read_yaml, write_yaml


class StoryRepository:
    """Manages story structure files in the story/ directory."""

    def __init__(self, story_dir: Path):
        self.story_dir = story_dir

    def get_structure(self) -> Optional[StoryStructure]:
        """Load the story structure. Returns None if not found."""
        path = self.story_dir / "structure.yaml"
        if not path.exists():
            return None
        return StoryStructure(**read_yaml(path))

    def save_structure(self, structure: StoryStructure) -> Path:
        """Save the story structure to disk."""
        self.story_dir.mkdir(parents=True, exist_ok=True)
        path = self.story_dir / "structure.yaml"
        write_yaml(path, structure.model_dump(mode="json"))
        return path
