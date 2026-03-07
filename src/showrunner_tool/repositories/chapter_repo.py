"""Chapter repository -- CRUD for scenes, screenplays, and panels within chapters."""

from __future__ import annotations

from pathlib import Path

from showrunner_tool.repositories.base import YAMLRepository
from showrunner_tool.schemas.scene import Scene
from showrunner_tool.schemas.screenplay import Screenplay
from showrunner_tool.schemas.panel import Panel


class ChapterRepository:
    """Manages chapter content (scenes, screenplays, panels) in chapters/ directory.

    Supports both flat structure (chapter-01/) and season-namespaced (s1/chapter-01/).
    """

    def __init__(self, chapters_dir: Path):
        self.chapters_dir = chapters_dir

    def chapter_dir(self, chapter_num: int, season: int = 1) -> Path:
        """Get the directory for a specific chapter, optionally namespaced by season.

        Args:
            chapter_num: Chapter number (1-indexed, will be zero-padded to 2 digits)
            season: Season number (default 1 for flat structure)

        Returns:
            Path to the chapter directory
        """
        if season > 1:
            return self.chapters_dir / f"s{season}" / f"chapter-{chapter_num:02d}"
        return self.chapters_dir / f"chapter-{chapter_num:02d}"

    def get_chapters(self, season: int = 1) -> list[int]:
        """Get all chapter numbers for a season."""
        season_dir = self.chapters_dir / f"s{season}" if season > 1 else self.chapters_dir
        if not season_dir.exists():
            return []
        chapters = []
        for d in sorted(season_dir.glob("chapter-*")):
            if d.is_dir():
                try:
                    chapter_num = int(d.name.replace("chapter-", ""))
                    chapters.append(chapter_num)
                except ValueError:
                    continue
        return chapters

    def get_seasons(self) -> list[int]:
        """Get all season numbers in the project."""
        seasons = set()
        # Check for flat chapters (season 1)
        if any((self.chapters_dir / "chapter-*").parent.glob("chapter-*")):
            seasons.add(1)
        # Check for season directories
        for d in self.chapters_dir.glob("s*"):
            if d.is_dir() and d.name.startswith("s"):
                try:
                    season_num = int(d.name[1:])
                    seasons.add(season_num)
                except ValueError:
                    continue
        return sorted(seasons)

    # ── Scenes ────────────────────────────────────────────────────

    def get_scenes(self, chapter_num: int, season: int = 1) -> list[Scene]:
        """Load all scenes for a chapter."""
        scenes_dir = self.chapter_dir(chapter_num, season) / "scenes"
        repo = YAMLRepository(scenes_dir, Scene)
        return [repo._load_file(f) for f in repo._list_files()]

    def save_scene(self, scene: Scene, chapter_num: int, season: int = 1) -> Path:
        """Save a scene to the chapter's scenes directory."""
        scenes_dir = self.chapter_dir(chapter_num, season) / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)
        path = scenes_dir / f"scene-{scene.scene_number:02d}.yaml"
        repo = YAMLRepository(scenes_dir, Scene)
        return repo._save_file(path, scene)

    # ── Screenplays ───────────────────────────────────────────────

    def get_screenplays(self, chapter_num: int, season: int = 1) -> list[Screenplay]:
        """Load all screenplays for a chapter."""
        sp_dir = self.chapter_dir(chapter_num, season) / "screenplay"
        repo = YAMLRepository(sp_dir, Screenplay)
        return [repo._load_file(f) for f in repo._list_files()]

    def save_screenplay(self, screenplay: Screenplay, chapter_num: int, season: int = 1) -> Path:
        """Save a screenplay to the chapter's screenplay directory."""
        sp_dir = self.chapter_dir(chapter_num, season) / "screenplay"
        sp_dir.mkdir(parents=True, exist_ok=True)
        path = sp_dir / f"screenplay-{screenplay.scene_id}.yaml"
        repo = YAMLRepository(sp_dir, Screenplay)
        return repo._save_file(path, screenplay)

    # ── Panels ────────────────────────────────────────────────────

    def get_panels(self, chapter_num: int, season: int = 1) -> list[Panel]:
        """Load all panels for a chapter."""
        panels_dir = self.chapter_dir(chapter_num, season) / "panels"
        repo = YAMLRepository(panels_dir, Panel)
        return [repo._load_file(f) for f in repo._list_files()]

    def save_panel(self, panel: Panel, chapter_num: int, season: int = 1) -> Path:
        """Save a panel to the chapter's panels directory."""
        panels_dir = self.chapter_dir(chapter_num, season) / "panels"
        panels_dir.mkdir(parents=True, exist_ok=True)
        path = panels_dir / f"page-{panel.page_number:02d}-panel-{panel.panel_number:02d}.yaml"
        repo = YAMLRepository(panels_dir, Panel)
        return repo._save_file(path, panel)
