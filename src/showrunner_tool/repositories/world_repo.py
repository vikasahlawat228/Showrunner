"""World repository -- CRUD for world settings, rules, history, factions."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from showrunner_tool.errors import PersistenceError
from showrunner_tool.schemas.world import WorldSettings, Faction
from showrunner_tool.utils.io import read_yaml, write_yaml


class WorldRepository:
    """Manages world data files in the world/ directory."""

    def __init__(self, world_dir: Path):
        self.world_dir = world_dir

    def _ensure_dir(self) -> None:
        self.world_dir.mkdir(parents=True, exist_ok=True)

    def get_settings(self) -> Optional[WorldSettings]:
        """Load world settings. Returns None if not found."""
        path = self.world_dir / "settings.yaml"
        if not path.exists():
            return None
        return WorldSettings(**read_yaml(path))

    def save_settings(self, settings: WorldSettings) -> Path:
        """Save world settings to disk."""
        self._ensure_dir()
        path = self.world_dir / "settings.yaml"
        write_yaml(path, settings.model_dump(mode="json"))
        return path

    def get_rules(self, filter_hidden: bool = True) -> list[dict]:
        """Load world rules. Optionally filters rules hidden from readers."""
        path = self.world_dir / "rules.yaml"
        if not path.exists():
            return []
        data = read_yaml(path)
        rules = data if isinstance(data, list) else data.get("rules", [])
        if filter_hidden:
            rules = [r for r in rules if r.get("known_to_reader", True)]
        return rules

    def get_history(self, filter_hidden: bool = True) -> list[dict]:
        """Load world history events. Optionally filters hidden events."""
        path = self.world_dir / "history.yaml"
        if not path.exists():
            return []
        data = read_yaml(path)
        events = data if isinstance(data, list) else data.get("events", [])
        if filter_hidden:
            events = [e for e in events if e.get("known_to_reader", True)]
        return events

    def get_factions(self) -> list[Faction]:
        """Load all faction files from world/factions/."""
        factions_dir = self.world_dir / "factions"
        if not factions_dir.exists():
            return []
        factions = []
        for f in sorted(factions_dir.glob("*.yaml")):
            if f.name.startswith("_"):
                continue
            try:
                factions.append(Faction(**read_yaml(f)))
            except Exception as e:
                raise PersistenceError(
                    f"Failed to load faction {f}: {e}",
                    context={"path": str(f)},
                )
        return factions
