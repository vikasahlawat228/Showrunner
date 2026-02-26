"""Project discovery, loading, and validation.

The Project class is the main facade for accessing project data.
It delegates all file I/O to repository classes while preserving
a backward-compatible public API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from showrunner_tool.errors import ProjectError  # noqa: F401 (re-exported for backward compat)
from showrunner_tool.repositories.character_repo import CharacterRepository
from showrunner_tool.repositories.world_repo import WorldRepository
from showrunner_tool.repositories.chapter_repo import ChapterRepository
from showrunner_tool.repositories.story_repo import StoryRepository
from showrunner_tool.repositories.style_repo import StyleRepository
from showrunner_tool.repositories.creative_room_repo import CreativeRoomRepository
from showrunner_tool.schemas.character import Character
from showrunner_tool.schemas.world import WorldSettings, Faction
from showrunner_tool.schemas.scene import Scene
from showrunner_tool.schemas.screenplay import Screenplay
from showrunner_tool.schemas.panel import Panel
from showrunner_tool.schemas.style_guide import VisualStyleGuide, NarrativeStyleGuide
from showrunner_tool.schemas.story_structure import StoryStructure
from showrunner_tool.schemas.creative_room import CreativeRoom, ReaderKnowledgeState
from showrunner_tool.utils.io import read_yaml


MANIFEST_FILE = "showrunner.yaml"
CREATIVE_ROOM_MARKER = ".showrunner-secret"


class Project:
    """Represents an Showrunner project on disk.

    Acts as a facade over entity-specific repositories for backward
    compatibility. All load_*/save_* methods delegate to repositories.
    """

    def __init__(self, path: Path):
        self.path = path.resolve()
        self.manifest_path = self.path / MANIFEST_FILE
        self._manifest: Optional[dict] = None

        # Repositories -- lazy-instantiated from directory paths
        self._character_repo = CharacterRepository(self.characters_dir)
        self._world_repo = WorldRepository(self.world_dir)
        self._chapter_repo = ChapterRepository(self.chapters_dir)
        self._story_repo = StoryRepository(self.story_dir)
        self._style_repo = StyleRepository(self.style_guide_dir)
        self._creative_room_repo = CreativeRoomRepository(self.creative_room_dir)

    @classmethod
    def find(cls, start: Path | None = None) -> Project:
        """Walk up from `start` (default cwd) to find the nearest showrunner.yaml."""
        current = (start or Path.cwd()).resolve()
        while current != current.parent:
            if (current / MANIFEST_FILE).exists():
                return cls(current)
            current = current.parent
        raise ProjectError(
            f"No {MANIFEST_FILE} found. Run 'showrunner init' to create a project."
        )

    @property
    def manifest(self) -> dict:
        if self._manifest is None:
            if not self.manifest_path.exists():
                raise ProjectError(f"No {MANIFEST_FILE} at {self.manifest_path}")
            self._manifest = read_yaml(self.manifest_path)
        return self._manifest

    @property
    def name(self) -> str:
        return self.manifest.get("name", "Untitled")

    @property
    def variables(self) -> dict:
        return self.manifest.get("variables", {})

    # ── Repository accessors (for direct use by services) ─────────

    @property
    def characters(self) -> CharacterRepository:
        return self._character_repo

    @property
    def world(self) -> WorldRepository:
        return self._world_repo

    @property
    def chapters(self) -> ChapterRepository:
        return self._chapter_repo

    @property
    def stories(self) -> StoryRepository:
        return self._story_repo

    @property
    def styles(self) -> StyleRepository:
        return self._style_repo

    @property
    def creative_room(self) -> CreativeRoomRepository:
        return self._creative_room_repo

    # ── Directory accessors ──────────────────────────────────────

    @property
    def world_dir(self) -> Path:
        return self.path / "world"

    @property
    def characters_dir(self) -> Path:
        return self.path / "characters"

    @property
    def story_dir(self) -> Path:
        return self.path / "story"

    @property
    def chapters_dir(self) -> Path:
        return self.path / "chapters"

    @property
    def style_guide_dir(self) -> Path:
        return self.path / "style_guide"

    @property
    def creative_room_dir(self) -> Path:
        return self.path / "creative_room"

    @property
    def exports_dir(self) -> Path:
        return self.path / "exports"

    @property
    def user_prompts_dir(self) -> Path:
        return self.path / "prompts"

    # ── Loaders (delegate to repositories) ────────────────────────

    def load_world_settings(self) -> Optional[WorldSettings]:
        return self._world_repo.get_settings()

    def load_world_rules(self, filter_hidden: bool = True) -> list[dict]:
        return self._world_repo.get_rules(filter_hidden=filter_hidden)

    def load_world_history(self, filter_hidden: bool = True) -> list[dict]:
        return self._world_repo.get_history(filter_hidden=filter_hidden)

    def load_factions(self) -> list[Faction]:
        return self._world_repo.get_factions()

    def load_character(self, name: str) -> Optional[Character]:
        return self._character_repo.get(name)

    def load_all_characters(self, filter_secrets: bool = True) -> list[Character]:
        return self._character_repo.get_all(filter_secrets=filter_secrets)

    def load_story_structure(self) -> Optional[StoryStructure]:
        return self._story_repo.get_structure()

    def load_visual_style_guide(self) -> Optional[VisualStyleGuide]:
        return self._style_repo.get_visual()

    def load_narrative_style_guide(self) -> Optional[NarrativeStyleGuide]:
        return self._style_repo.get_narrative()

    def chapter_dir(self, chapter_num: int) -> Path:
        return self._chapter_repo.chapter_dir(chapter_num)

    def load_scenes(self, chapter_num: int) -> list[Scene]:
        return self._chapter_repo.get_scenes(chapter_num)

    def load_screenplays(self, chapter_num: int) -> list[Screenplay]:
        return self._chapter_repo.get_screenplays(chapter_num)

    def load_panels(self, chapter_num: int) -> list[Panel]:
        return self._chapter_repo.get_panels(chapter_num)

    def load_creative_room(self) -> Optional[CreativeRoom]:
        return self._creative_room_repo.get_room()

    def load_reader_knowledge(
        self, chapter_id: str, scene_id: str | None = None
    ) -> Optional[ReaderKnowledgeState]:
        return self._creative_room_repo.get_reader_knowledge(chapter_id, scene_id)

    # ── Savers (delegate to repositories) ─────────────────────────

    def save_character(self, character: Character) -> Path:
        return self._character_repo.save(character)

    def save_scene(self, scene: Scene, chapter_num: int) -> Path:
        return self._chapter_repo.save_scene(scene, chapter_num)

    def save_screenplay(self, screenplay: Screenplay, chapter_num: int) -> Path:
        return self._chapter_repo.save_screenplay(screenplay, chapter_num)

    def save_panel(self, panel: Panel, chapter_num: int) -> Path:
        return self._chapter_repo.save_panel(panel, chapter_num)

    # ── Validation ───────────────────────────────────────────────

    def is_valid(self) -> tuple[bool, list[str]]:
        """Validate project structure. Returns (ok, errors)."""
        errors = []
        if not self.manifest_path.exists():
            errors.append(f"Missing {MANIFEST_FILE}")
        if not self.world_dir.exists():
            errors.append("Missing world/ directory")
        if not self.characters_dir.exists():
            errors.append("Missing characters/ directory")
        if not self.creative_room_dir.exists():
            errors.append("Missing creative_room/ directory")
        elif not (self.creative_room_dir / CREATIVE_ROOM_MARKER).exists():
            errors.append(f"Missing {CREATIVE_ROOM_MARKER} in creative_room/")
        return (len(errors) == 0, errors)

    def is_creative_room_path(self, path: Path) -> bool:
        """Check if a path is inside the creative room."""
        try:
            path.resolve().relative_to(self.creative_room_dir.resolve())
            return True
        except ValueError:
            return False
