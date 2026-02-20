"""Workflow step orchestration and state tracking."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from antigravity_tool.utils.io import read_yaml, write_yaml


WORKFLOW_STEPS = [
    "world_building",
    "character_creation",
    "story_structure",
    "scene_writing",
    "screenplay_writing",
    "panel_division",
    "image_prompt_generation",
]

STEP_LABELS = {
    "world_building": "World Building",
    "character_creation": "Character Creation",
    "story_structure": "Story Structure",
    "scene_writing": "Scene Writing",
    "screenplay_writing": "Screenplay Writing",
    "panel_division": "Panel Division",
    "image_prompt_generation": "Image Prompt Generation",
}


class WorkflowState:
    """Tracks progress through the workflow pipeline."""

    def __init__(self, project_path: Path):
        self.state_dir = project_path / ".antigravity"
        self.state_file = self.state_dir / "workflow_state.yaml"
        self._state: Optional[dict] = None

    @property
    def state(self) -> dict:
        if self._state is None:
            if self.state_file.exists():
                self._state = read_yaml(self.state_file)
            else:
                self._state = self._default_state()
        return self._state

    def _default_state(self) -> dict:
        return {
            "current_step": "world_building",
            "current_chapter": 1,
            "current_scene": None,
            "steps": {
                step: {"status": "pending", "last_run": None, "outputs": []}
                for step in WORKFLOW_STEPS
            },
        }

    def save(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        write_yaml(self.state_file, self.state)

    def mark_step_started(self, step: str) -> None:
        self.state["current_step"] = step
        self.state["steps"][step]["status"] = "in_progress"
        self.state["steps"][step]["last_run"] = datetime.now(timezone.utc).isoformat()
        self.save()

    def mark_step_complete(self, step: str, outputs: list[str] | None = None) -> None:
        self.state["steps"][step]["status"] = "complete"
        if outputs:
            self.state["steps"][step]["outputs"] = outputs
        self.save()

    def set_position(self, chapter: int | None = None, scene: int | None = None) -> None:
        """Update the current chapter/scene position."""
        if chapter is not None:
            self.state["current_chapter"] = chapter
        if scene is not None:
            self.state["current_scene"] = scene
        self.save()

    def get_step_status(self, step: str) -> str:
        return self.state["steps"].get(step, {}).get("status", "unknown")

    def get_current_step(self) -> str:
        return self.state.get("current_step", "world_building")

    def get_current_chapter(self) -> int | None:
        return self.state.get("current_chapter")

    def get_current_scene(self) -> int | None:
        return self.state.get("current_scene")

    def get_progress_summary(self) -> list[tuple[str, str, str]]:
        """Return list of (step_name, label, status) for display."""
        result = []
        for step in WORKFLOW_STEPS:
            status = self.get_step_status(step)
            label = STEP_LABELS.get(step, step)
            result.append((step, label, status))
        return result
