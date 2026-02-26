"""Creative Room isolation enforcement and reader knowledge management."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from showrunner_tool.core.project import Project, CREATIVE_ROOM_MARKER
from showrunner_tool.schemas.creative_room import (
    CreativeRoom,
    PlotTwist,
    CharacterSecret,
    ForeshadowingEntry,
    TrueMechanic,
    ReaderKnowledgeState,
)
from showrunner_tool.utils.io import read_yaml, write_yaml
from showrunner_tool.utils.ids import generate_id


class CreativeRoomManager:
    """Manages the creative room: isolation enforcement and CRUD operations."""

    def __init__(self, project: Project):
        self.project = project
        self.room_dir = project.creative_room_dir

    def ensure_isolation_marker(self) -> None:
        """Ensure the .showrunner-secret marker exists."""
        marker = self.room_dir / CREATIVE_ROOM_MARKER
        if not marker.exists():
            self.room_dir.mkdir(parents=True, exist_ok=True)
            marker.touch()

    def is_isolated(self) -> bool:
        """Check if the creative room has its isolation marker."""
        return (self.room_dir / CREATIVE_ROOM_MARKER).exists()

    # ── Plot Twists ──────────────────────────────────────────────

    def add_plot_twist(self, twist: PlotTwist) -> Path:
        if not twist.id:
            twist.id = generate_id()
        p = self.room_dir / "plot_twists.yaml"
        existing = self._load_list(p)
        existing.append(twist.model_dump(mode="json"))
        write_yaml(p, existing)
        return p

    def list_plot_twists(self) -> list[PlotTwist]:
        p = self.room_dir / "plot_twists.yaml"
        data = self._load_list(p)
        return [PlotTwist(**d) for d in data]

    # ── Character Secrets ────────────────────────────────────────

    def add_character_secret(self, secret: CharacterSecret) -> Path:
        p = self.room_dir / "character_secrets.yaml"
        existing = self._load_list(p)
        existing.append(secret.model_dump(mode="json"))
        write_yaml(p, existing)
        return p

    def list_character_secrets(self) -> list[CharacterSecret]:
        p = self.room_dir / "character_secrets.yaml"
        data = self._load_list(p)
        return [CharacterSecret(**d) for d in data]

    # ── Foreshadowing ────────────────────────────────────────────

    def add_foreshadowing(self, entry: ForeshadowingEntry) -> Path:
        if not entry.id:
            entry.id = generate_id()
        p = self.room_dir / "foreshadowing_map.yaml"
        existing = self._load_list(p)
        existing.append(entry.model_dump(mode="json"))
        write_yaml(p, existing)
        return p

    def list_foreshadowing(self) -> list[ForeshadowingEntry]:
        p = self.room_dir / "foreshadowing_map.yaml"
        data = self._load_list(p)
        return [ForeshadowingEntry(**d) for d in data]

    # ── True Mechanics ───────────────────────────────────────────

    def add_true_mechanic(self, mechanic: TrueMechanic) -> Path:
        p = self.room_dir / "true_mechanics.yaml"
        existing = self._load_list(p)
        existing.append(mechanic.model_dump(mode="json"))
        write_yaml(p, existing)
        return p

    # ── Ending Plans ─────────────────────────────────────────────

    def set_ending_plans(self, plans: str) -> Path:
        p = self.room_dir / "ending_plans.yaml"
        write_yaml(p, {"ending_plans": plans})
        return p

    def get_ending_plans(self) -> str:
        p = self.room_dir / "ending_plans.yaml"
        if not p.exists():
            return ""
        data = read_yaml(p)
        return data.get("ending_plans", "") if isinstance(data, dict) else ""

    # ── Reader Knowledge State ───────────────────────────────────

    def save_reader_knowledge(self, state: ReaderKnowledgeState) -> Path:
        rk_dir = self.room_dir / "reader_knowledge"
        rk_dir.mkdir(parents=True, exist_ok=True)
        label = state.position_label.replace(" ", "_").lower()
        p = rk_dir / f"{label}.yaml"
        write_yaml(p, state.model_dump(mode="json"))
        return p

    def load_reader_knowledge_at(
        self, chapter_id: str, scene_id: str | None = None
    ) -> Optional[ReaderKnowledgeState]:
        return self.project.load_reader_knowledge(chapter_id, scene_id)

    def list_knowledge_states(self) -> list[ReaderKnowledgeState]:
        rk_dir = self.room_dir / "reader_knowledge"
        if not rk_dir.exists():
            return []
        states = []
        for f in sorted(rk_dir.glob("*.yaml")):
            states.append(ReaderKnowledgeState(**read_yaml(f)))
        return states

    # ── Helpers ──────────────────────────────────────────────────

    def _load_list(self, path: Path) -> list[dict]:
        if not path.exists():
            return []
        data = read_yaml(path)
        if isinstance(data, list):
            return data
        return []
