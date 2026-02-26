"""Style repository -- CRUD for visual and narrative style guides."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from showrunner_tool.schemas.style_guide import VisualStyleGuide, NarrativeStyleGuide
from showrunner_tool.utils.io import read_yaml


class StyleRepository:
    """Manages style guide files in the style_guide/ directory."""

    def __init__(self, style_dir: Path):
        self.style_dir = style_dir

    def get_visual(self) -> Optional[VisualStyleGuide]:
        """Load the visual style guide. Returns None if not found."""
        path = self.style_dir / "visual.yaml"
        if not path.exists():
            return None
        return VisualStyleGuide(**read_yaml(path))

    def get_narrative(self) -> Optional[NarrativeStyleGuide]:
        """Load the narrative style guide. Returns None if not found."""
        path = self.style_dir / "narrative.yaml"
        if not path.exists():
            return None
        return NarrativeStyleGuide(**read_yaml(path))
