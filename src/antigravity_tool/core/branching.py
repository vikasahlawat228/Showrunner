"""Branching narratives: fork scenes into alternative branches."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from antigravity_tool.core.project import Project
from antigravity_tool.schemas.scene import Scene
from antigravity_tool.utils.io import read_yaml, write_yaml, ensure_dir
from antigravity_tool.utils.ids import generate_id


class BranchManager:
    """Manages alternative narrative branches for scenes."""

    def __init__(self, project: Project):
        self.project = project

    def create_branch(
        self,
        chapter_num: int,
        scene_num: int,
        label: str,
    ) -> Scene:
        """Fork a scene into a new branch."""
        scenes = self.project.load_scenes(chapter_num)
        original = next((s for s in scenes if s.scene_number == scene_num and s.is_canonical), None)

        if not original:
            raise ValueError(f"No canonical scene {scene_num} in chapter {chapter_num}")

        branch_id = generate_id()

        branch = original.model_copy(deep=True)
        branch.id = generate_id()
        branch.branch_id = branch_id
        branch.branch_parent_scene_id = original.id
        branch.branch_label = label
        branch.is_canonical = False
        branch.title = f"[BRANCH: {label}] {original.title}"
        # Reset content fields for rewriting
        branch.key_events = []
        branch.closing_state = ""
        branch.cliffhanger = None

        # Save to branches subdirectory
        branches_dir = ensure_dir(
            self.project.chapter_dir(chapter_num) / "scenes" / "branches"
        )
        filename = f"scene-{scene_num:02d}-branch-{branch_id[:8]}.yaml"
        write_yaml(branches_dir / filename, branch.model_dump(mode="json"))

        return branch

    def list_branches(
        self, chapter_num: int, scene_num: Optional[int] = None
    ) -> list[Scene]:
        """List all branches for a chapter or specific scene."""
        branches_dir = self.project.chapter_dir(chapter_num) / "scenes" / "branches"
        if not branches_dir.exists():
            return []

        branches = []
        for f in sorted(branches_dir.glob("*.yaml")):
            scene = Scene(**read_yaml(f))
            if scene_num is None or scene.scene_number == scene_num:
                branches.append(scene)
        return branches

    def compare_branches(
        self, chapter_num: int, scene_num: int
    ) -> dict:
        """Compare the canonical scene with all its branches."""
        scenes = self.project.load_scenes(chapter_num)
        canonical = next(
            (s for s in scenes if s.scene_number == scene_num and s.is_canonical),
            None,
        )

        branches = [
            b for b in self.list_branches(chapter_num, scene_num)
        ]

        return {
            "canonical": canonical.model_dump(mode="json") if canonical else None,
            "branches": [b.model_dump(mode="json") for b in branches],
            "branch_count": len(branches),
        }

    def promote_branch(
        self, chapter_num: int, branch_id: str
    ) -> Optional[Scene]:
        """Promote a branch to canonical, demoting the current canonical."""
        # Find the branch
        branches = self.list_branches(chapter_num)
        target = next((b for b in branches if b.branch_id and b.branch_id.startswith(branch_id)), None)

        if not target:
            return None

        scene_num = target.scene_number

        # Demote current canonical
        scenes = self.project.load_scenes(chapter_num)
        current_canonical = next(
            (s for s in scenes if s.scene_number == scene_num and s.is_canonical),
            None,
        )

        if current_canonical:
            current_canonical.is_canonical = False
            current_canonical.branch_label = current_canonical.branch_label or "original"
            # Move to branches dir
            branches_dir = ensure_dir(
                self.project.chapter_dir(chapter_num) / "scenes" / "branches"
            )
            demoted_id = current_canonical.branch_id or generate_id()[:8]
            write_yaml(
                branches_dir / f"scene-{scene_num:02d}-branch-{demoted_id[:8]}.yaml",
                current_canonical.model_dump(mode="json"),
            )

        # Promote the target
        target.is_canonical = True
        target.title = target.title.replace(f"[BRANCH: {target.branch_label}] ", "")
        self.project.save_scene(target, chapter_num)

        # Remove from branches dir
        branches_dir = self.project.chapter_dir(chapter_num) / "scenes" / "branches"
        for f in branches_dir.glob(f"*-branch-{target.branch_id[:8]}*"):
            f.unlink()

        return target
