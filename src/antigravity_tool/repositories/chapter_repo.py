"""Chapter repository -- CRUD for scenes, screenplays, and panels within chapters."""

from __future__ import annotations

from pathlib import Path

from antigravity_tool.repositories.base import YAMLRepository
from antigravity_tool.schemas.scene import Scene
from antigravity_tool.schemas.screenplay import Screenplay
from antigravity_tool.schemas.panel import Panel


class ChapterRepository:
    """Manages chapter content (scenes, screenplays, panels) in chapters/ directory."""

    def __init__(self, chapters_dir: Path):
        self.chapters_dir = chapters_dir

    def chapter_dir(self, chapter_num: int) -> Path:
        """Get the directory for a specific chapter."""
        return self.chapters_dir / f"chapter-{chapter_num:02d}"

    # ── Scenes ────────────────────────────────────────────────────

    def get_scenes(self, chapter_num: int) -> list[Scene]:
        """Load all scenes for a chapter."""
        scenes_dir = self.chapter_dir(chapter_num) / "scenes"
        repo = YAMLRepository(scenes_dir, Scene)
        return [repo._load_file(f) for f in repo._list_files()]

    def save_scene(self, scene: Scene, chapter_num: int) -> Path:
        """Save a scene to the chapter's scenes directory."""
        scenes_dir = self.chapter_dir(chapter_num) / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)
        path = scenes_dir / f"scene-{scene.scene_number:02d}.yaml"
        repo = YAMLRepository(scenes_dir, Scene)
        return repo._save_file(path, scene)

    # ── Screenplays ───────────────────────────────────────────────

    def get_screenplays(self, chapter_num: int) -> list[Screenplay]:
        """Load all screenplays for a chapter."""
        sp_dir = self.chapter_dir(chapter_num) / "screenplay"
        repo = YAMLRepository(sp_dir, Screenplay)
        return [repo._load_file(f) for f in repo._list_files()]

    def save_screenplay(self, screenplay: Screenplay, chapter_num: int) -> Path:
        """Save a screenplay to the chapter's screenplay directory."""
        sp_dir = self.chapter_dir(chapter_num) / "screenplay"
        sp_dir.mkdir(parents=True, exist_ok=True)
        path = sp_dir / f"screenplay-{screenplay.scene_id}.yaml"
        repo = YAMLRepository(sp_dir, Screenplay)
        return repo._save_file(path, screenplay)

    # ── Panels ────────────────────────────────────────────────────

    def get_panels(self, chapter_num: int) -> list[Panel]:
        """Load all panels for a chapter."""
        panels_dir = self.chapter_dir(chapter_num) / "panels"
        repo = YAMLRepository(panels_dir, Panel)
        return [repo._load_file(f) for f in repo._list_files()]

    def save_panel(self, panel: Panel, chapter_num: int) -> Path:
        """Save a panel to the chapter's panels directory."""
        panels_dir = self.chapter_dir(chapter_num) / "panels"
        panels_dir.mkdir(parents=True, exist_ok=True)
        path = panels_dir / f"page-{panel.page_number:02d}-panel-{panel.panel_number:02d}.yaml"
        repo = YAMLRepository(panels_dir, Panel)
        return repo._save_file(path, panel)
