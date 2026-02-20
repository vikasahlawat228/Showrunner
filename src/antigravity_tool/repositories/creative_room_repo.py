"""Creative room repository -- persistence for author-only isolated data."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from antigravity_tool.schemas.creative_room import CreativeRoom, ReaderKnowledgeState
from antigravity_tool.utils.io import read_yaml


CREATIVE_ROOM_MARKER = ".antigravity-secret"


class CreativeRoomRepository:
    """Manages creative room files. Checks isolation marker before access."""

    def __init__(self, creative_room_dir: Path):
        self.room_dir = creative_room_dir

    def is_isolated(self) -> bool:
        """Check if the creative room has its isolation marker."""
        return (self.room_dir / CREATIVE_ROOM_MARKER).exists()

    def get_room(self) -> Optional[CreativeRoom]:
        """Load the full creative room. Returns None if marker is missing."""
        if not self.is_isolated():
            return None
        parts: dict = {}
        for name in [
            "plot_twists", "character_secrets", "true_mechanics",
            "ending_plans", "foreshadowing_map",
        ]:
            path = self.room_dir / f"{name}.yaml"
            if path.exists():
                data = read_yaml(path)
                if name == "ending_plans":
                    parts[name] = data.get("ending_plans", "") if isinstance(data, dict) else str(data)
                else:
                    parts[name] = data if isinstance(data, list) else data.get(name, [])
        return CreativeRoom(**parts)

    def get_reader_knowledge(
        self, chapter_id: str, scene_id: str | None = None
    ) -> Optional[ReaderKnowledgeState]:
        """Load the most recent reader knowledge state at or before the given position."""
        rk_dir = self.room_dir / "reader_knowledge"
        if not rk_dir.exists():
            return None
        # Try exact match first if scene_id provided
        if scene_id:
            exact = rk_dir / f"{chapter_id}-{scene_id}.yaml"
            if exact.exists():
                return ReaderKnowledgeState(**read_yaml(exact))
        # Fall back to latest file matching the chapter
        candidates = sorted(rk_dir.glob(f"{chapter_id}*.yaml"))
        if candidates:
            return ReaderKnowledgeState(**read_yaml(candidates[-1]))
        return None
