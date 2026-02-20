"""Auto-continuity checker: validates character states, scene flow, and consistency."""

from __future__ import annotations

from typing import Optional

from antigravity_tool.core.project import Project
from antigravity_tool.schemas.continuity import (
    ContinuityIssue,
    ContinuityReport,
    IssueSeverity,
    IssueCategory,
)
from antigravity_tool.schemas.scene import Scene
from antigravity_tool.utils.io import read_yaml


class ContinuityChecker:
    """Validates data consistency across scenes, characters, and relationships."""

    def __init__(self, project: Project):
        self.project = project

    def full_check(self, chapter_num: Optional[int] = None) -> ContinuityReport:
        """Run all continuity checks for a chapter or the whole project."""
        issues: list[ContinuityIssue] = []
        checked_scenes = 0
        checked_characters = 0

        if chapter_num:
            chapters = [chapter_num]
        else:
            # Find all chapters
            chapters = []
            if self.project.chapters_dir.exists():
                for d in sorted(self.project.chapters_dir.iterdir()):
                    if d.is_dir() and d.name.startswith("chapter-"):
                        try:
                            chapters.append(int(d.name.split("-")[1]))
                        except (IndexError, ValueError):
                            pass

        for ch in chapters:
            scenes = self.project.load_scenes(ch)
            checked_scenes += len(scenes)
            issues.extend(self.check_character_continuity(ch, scenes))
            issues.extend(self.check_scene_flow(ch, scenes))

        # Cross-chapter checks
        issues.extend(self.check_relationship_consistency())

        if chapter_num:
            issues.extend(self.check_reader_knowledge(chapter_num))

        characters = self.project.load_all_characters(filter_secrets=False)
        checked_characters = len(characters)

        return ContinuityReport(
            chapter_num=chapter_num,
            issues=issues,
            checked_scenes=checked_scenes,
            checked_characters=checked_characters,
        )

    def check_character_continuity(
        self, chapter_num: int, scenes: list[Scene]
    ) -> list[ContinuityIssue]:
        """Check character state transitions between consecutive scenes."""
        issues: list[ContinuityIssue] = []
        states_dir = self.project.chapter_dir(chapter_num) / "character_states"

        if not states_dir.exists():
            return issues

        # Load character states per scene
        scene_states: dict[int, dict[str, dict]] = {}
        for scene in scenes:
            state_file = states_dir / f"scene-{scene.scene_number:02d}.yaml"
            if state_file.exists():
                data = read_yaml(state_file)
                states = data if isinstance(data, list) else [data]
                scene_states[scene.scene_number] = {
                    s.get("character_name", ""): s for s in states if isinstance(s, dict)
                }

        # Compare consecutive scenes
        sorted_scene_nums = sorted(scene_states.keys())
        for i in range(1, len(sorted_scene_nums)):
            prev_num = sorted_scene_nums[i - 1]
            curr_num = sorted_scene_nums[i]
            prev_states = scene_states[prev_num]
            curr_states = scene_states[curr_num]
            loc = f"Chapter {chapter_num}, Scene {prev_num} → Scene {curr_num}"

            for char_name, curr_state in curr_states.items():
                if char_name not in prev_states:
                    continue
                prev_state = prev_states[char_name]

                # Outfit continuity: outfit shouldn't change without explanation
                prev_outfit = prev_state.get("current_outfit", "default")
                curr_outfit = curr_state.get("current_outfit", "default")
                if prev_outfit and curr_outfit and prev_outfit != curr_outfit:
                    issues.append(ContinuityIssue(
                        severity=IssueSeverity.WARNING,
                        category=IssueCategory.OUTFIT_CONTINUITY,
                        location=loc,
                        description=f"{char_name}'s outfit changed from '{prev_outfit}' to '{curr_outfit}' between scenes.",
                        suggestion="Add a scene beat showing the outfit change, or revert to the previous outfit.",
                        character_name=char_name,
                        field="current_outfit",
                        expected_value=prev_outfit,
                        actual_value=curr_outfit,
                    ))

                # Injury continuity: injuries shouldn't disappear
                prev_injuries = set(prev_state.get("injuries", []))
                curr_injuries = set(curr_state.get("injuries", []))
                disappeared = prev_injuries - curr_injuries
                if disappeared:
                    issues.append(ContinuityIssue(
                        severity=IssueSeverity.ERROR,
                        category=IssueCategory.INJURY_CONTINUITY,
                        location=loc,
                        description=f"{char_name}'s injuries disappeared: {', '.join(disappeared)}.",
                        suggestion="Either show healing/treatment or carry injuries forward.",
                        character_name=char_name,
                        field="injuries",
                        expected_value=str(list(prev_injuries)),
                        actual_value=str(list(curr_injuries)),
                    ))

                # Location continuity: character must travel if location changes
                prev_loc = prev_state.get("location", "")
                curr_loc = curr_state.get("location", "")
                if prev_loc and curr_loc and prev_loc != curr_loc:
                    # This is info-level — location changes are normal but should be noted
                    issues.append(ContinuityIssue(
                        severity=IssueSeverity.INFO,
                        category=IssueCategory.LOCATION_CONTINUITY,
                        location=loc,
                        description=f"{char_name} moved from '{prev_loc}' to '{curr_loc}'.",
                        suggestion="Ensure travel between locations is shown or implied.",
                        character_name=char_name,
                        field="location",
                        expected_value=prev_loc,
                        actual_value=curr_loc,
                    ))

        return issues

    def check_scene_flow(
        self, chapter_num: int, scenes: list[Scene]
    ) -> list[ContinuityIssue]:
        """Check scene-level flow: time progression, character availability."""
        issues: list[ContinuityIssue] = []

        time_order = [
            "dawn", "morning", "midday", "afternoon",
            "dusk", "evening", "night", "late_night",
        ]

        for i in range(1, len(scenes)):
            prev = scenes[i - 1]
            curr = scenes[i]
            loc = f"Chapter {chapter_num}, Scene {prev.scene_number} → Scene {curr.scene_number}"

            # Time regression check (within same chapter, time should generally advance)
            prev_time_idx = time_order.index(prev.time_of_day.value) if prev.time_of_day.value in time_order else -1
            curr_time_idx = time_order.index(curr.time_of_day.value) if curr.time_of_day.value in time_order else -1

            if prev_time_idx >= 0 and curr_time_idx >= 0 and curr_time_idx < prev_time_idx:
                # Check if scene is a flashback
                if curr.scene_type.value != "flashback":
                    issues.append(ContinuityIssue(
                        severity=IssueSeverity.WARNING,
                        category=IssueCategory.TIME_CONTINUITY,
                        location=loc,
                        description=f"Time went backwards: {prev.time_of_day.value} → {curr.time_of_day.value}.",
                        suggestion="Mark as flashback scene or adjust time_of_day.",
                    ))

            # Tension flow check: large sudden drops may indicate pacing issues
            if prev.tension_level - curr.tension_level > 5:
                issues.append(ContinuityIssue(
                    severity=IssueSeverity.INFO,
                    category=IssueCategory.SCENE_FLOW,
                    location=loc,
                    description=f"Tension dropped sharply from {prev.tension_level} to {curr.tension_level}.",
                    suggestion="Consider a transition scene to ease the tension shift.",
                ))

        return issues

    def check_reader_knowledge(self, chapter_num: int) -> list[ContinuityIssue]:
        """Check that scenes don't reference information the reader doesn't know yet."""
        issues: list[ContinuityIssue] = []
        chapter_id = f"chapter-{chapter_num:02d}"
        rk = self.project.load_reader_knowledge(chapter_id)

        if not rk:
            return issues

        known_chars = set(rk.known_characters)
        known_locations = set(rk.known_locations)

        scenes = self.project.load_scenes(chapter_num)
        for scene in scenes:
            loc = f"Chapter {chapter_num}, Scene {scene.scene_number}"

            # Check if scene introduces characters the reader doesn't know
            for char_name in scene.characters_present:
                if char_name not in known_chars and scene.scene_number > 1:
                    issues.append(ContinuityIssue(
                        severity=IssueSeverity.INFO,
                        category=IssueCategory.READER_KNOWLEDGE,
                        location=loc,
                        description=f"Character '{char_name}' appears but isn't in reader knowledge state.",
                        suggestion="Update reader knowledge after introducing this character.",
                        character_name=char_name,
                    ))

        return issues

    def check_relationship_consistency(self) -> list[ContinuityIssue]:
        """Check relationship graph consistency against character files."""
        issues: list[ContinuityIssue] = []

        rel_path = self.project.story_dir / "relationships.yaml"
        if not rel_path.exists():
            return issues

        data = read_yaml(rel_path)
        edges = data.get("edges", []) if isinstance(data, dict) else []

        character_names = {
            c.name for c in self.project.load_all_characters(filter_secrets=False)
        }

        for edge in edges:
            if not isinstance(edge, dict):
                continue
            source = edge.get("source_name", "")
            target = edge.get("target_name", "")

            if source and source not in character_names:
                issues.append(ContinuityIssue(
                    severity=IssueSeverity.ERROR,
                    category=IssueCategory.RELATIONSHIP_CONSISTENCY,
                    location="Relationship Graph",
                    description=f"Relationship references unknown character '{source}'.",
                    suggestion=f"Create character '{source}' or fix the relationship edge.",
                    character_name=source,
                ))
            if target and target not in character_names:
                issues.append(ContinuityIssue(
                    severity=IssueSeverity.ERROR,
                    category=IssueCategory.RELATIONSHIP_CONSISTENCY,
                    location="Relationship Graph",
                    description=f"Relationship references unknown character '{target}'.",
                    suggestion=f"Create character '{target}' or fix the relationship edge.",
                    character_name=target,
                ))

        return issues
