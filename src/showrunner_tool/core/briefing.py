"""Briefing generator: produces a compact context snapshot for new sessions.

When Claude Code opens a new session in an Showrunner project, it reads
the CLAUDE.md. The `showrunner brief` command regenerates the dynamic
portion of CLAUDE.md so that the agent immediately knows:
  - What the story is about
  - Where we are in the pipeline
  - What decisions have been made
  - What to do next
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from showrunner_tool.core.project import Project
from showrunner_tool.core.workflow import WorkflowState, STEP_LABELS, WORKFLOW_STEPS
from showrunner_tool.core.session_manager import DecisionLog, SessionLog
from showrunner_tool.schemas.session import ChapterSummary, ProjectBrief


class BriefingGenerator:
    """Assembles a ProjectBrief from on-disk project state."""

    def __init__(self, project: Project):
        self.project = project
        self.workflow = WorkflowState(project.path)
        self.decisions = DecisionLog(project.path)
        self.sessions = SessionLog(project.path)

    def generate(self) -> ProjectBrief:
        """Build a complete briefing from current project state."""
        manifest = self.project.manifest
        current_step = self.workflow.get_current_step()

        # Characters
        characters = self.project.load_all_characters(filter_secrets=True)
        char_names = [c.name for c in characters]

        # Story beats
        structure = self.project.load_story_structure()
        beats_str = ""
        if structure and structure.beats:
            filled = sum(1 for b in structure.beats if b.content)
            beats_str = f"{filled}/{len(structure.beats)}"

        # Chapter summaries
        chapter_summaries = self._scan_chapters()

        # Current chapter/scene (find the most advanced in-progress chapter)
        current_chapter, current_scene = self._find_current_position(chapter_summaries)

        # Active decisions (scoped to current work)
        active = self.decisions.query(chapter=current_chapter, scene=current_scene)
        decision_strs = [d.decision for d in active]

        # Last session
        recent_sessions = self.sessions.load_latest(1)
        last_summary = ""
        last_next = ""
        if recent_sessions:
            last = recent_sessions[0]
            last_summary = last.summary
            last_next = last.next_steps

        # World one-liner
        world = self.project.load_world_settings()
        one_line = ""
        if world:
            one_line = world.one_line or world.description[:200] if world.description else ""

        # Suggested next action
        suggested_action, suggested_cmd = self._suggest_next(current_step, chapter_summaries)

        return ProjectBrief(
            project_name=self.project.name,
            one_line=one_line,
            template=manifest.get("template", "manhwa"),
            structure_type=manifest.get("story_structure", "save_the_cat"),
            current_step=current_step,
            current_step_label=STEP_LABELS.get(current_step, current_step),
            current_chapter=current_chapter,
            current_scene=current_scene,
            total_characters=len(characters),
            character_names=char_names,
            story_beats_filled=beats_str,
            chapter_summaries=chapter_summaries,
            active_decisions=decision_strs,
            last_session_summary=last_summary,
            last_session_next_steps=last_next,
            suggested_next_action=suggested_action,
            suggested_command=suggested_cmd,
        )

    def _scan_chapters(self) -> list[ChapterSummary]:
        """Scan all chapter directories for status."""
        chapters_dir = self.project.chapters_dir
        if not chapters_dir.exists():
            return []
        summaries = []
        for ch_dir in sorted(chapters_dir.glob("chapter-*")):
            if not ch_dir.is_dir():
                continue
            try:
                num = int(ch_dir.name.split("-")[1])
            except (IndexError, ValueError):
                continue

            # Load meta if available
            from showrunner_tool.utils.io import read_yaml
            meta_path = ch_dir / "meta.yaml"
            title = ""
            status = "planned"
            if meta_path.exists():
                meta = read_yaml(meta_path)
                title = meta.get("title", "")
                status = meta.get("status", "planned")

            scene_count = len(list((ch_dir / "scenes").glob("*.yaml"))) if (ch_dir / "scenes").exists() else 0
            sp_count = len(list((ch_dir / "screenplay").glob("*.yaml"))) if (ch_dir / "screenplay").exists() else 0
            panel_count = len(list((ch_dir / "panels").glob("*.yaml"))) if (ch_dir / "panels").exists() else 0

            summaries.append(ChapterSummary(
                chapter_number=num,
                title=title,
                status=status,
                scene_count=scene_count,
                screenplay_count=sp_count,
                panel_count=panel_count,
            ))
        return summaries

    def _find_current_position(self, chapters: list[ChapterSummary]) -> tuple[Optional[int], Optional[int]]:
        """Find the chapter/scene currently being worked on."""
        if not chapters:
            return 1, 1
        # Find last chapter with any content
        for ch in reversed(chapters):
            if ch.scene_count > 0 or ch.screenplay_count > 0 or ch.panel_count > 0:
                return ch.chapter_number, ch.scene_count
        return 1, None

    def _suggest_next(self, current_step: str, chapters: list[ChapterSummary]) -> tuple[str, str]:
        """Suggest the next action based on workflow state."""
        suggestions = {
            "world_building": ("Build the world settings", "showrunner world build"),
            "character_creation": ("Create characters", "showrunner character create \"Name\" --role protagonist"),
            "story_structure": ("Outline the story structure", "showrunner story outline"),
            "scene_writing": ("Write the next scene", "showrunner scene write --chapter 1 --scene 1"),
            "screenplay_writing": ("Convert scene to screenplay", "showrunner screenplay generate --chapter 1 --scene 1"),
            "panel_division": ("Divide screenplay into panels", "showrunner panel divide --chapter 1 --scene 1"),
            "image_prompt_generation": ("Generate image prompts", "showrunner prompt generate --chapter 1"),
        }
        action, cmd = suggestions.get(current_step, ("Check project status", "showrunner status"))
        return action, cmd

    def render_markdown(self, brief: ProjectBrief | None = None) -> str:
        """Render the briefing as markdown text for CLAUDE.md injection."""
        if brief is None:
            brief = self.generate()

        lines = []
        lines.append("## Current Project State")
        lines.append("")
        if brief.one_line:
            lines.append(f"> {brief.one_line}")
            lines.append("")
        lines.append(f"- **Current step**: {brief.current_step_label}")
        if brief.current_chapter:
            pos = f"Chapter {brief.current_chapter}"
            if brief.current_scene:
                pos += f", Scene {brief.current_scene}"
            lines.append(f"- **Working on**: {pos}")
        lines.append(f"- **Characters**: {brief.total_characters} ({', '.join(brief.character_names[:8])}{'...' if len(brief.character_names) > 8 else ''})")
        if brief.story_beats_filled:
            lines.append(f"- **Story beats**: {brief.story_beats_filled} filled")
        lines.append("")

        # Chapter progress
        if brief.chapter_summaries:
            lines.append("### Chapter Progress")
            lines.append("")
            for ch in brief.chapter_summaries:
                label = f"Ch {ch.chapter_number}"
                if ch.title:
                    label += f": {ch.title}"
                parts = []
                if ch.scene_count:
                    parts.append(f"{ch.scene_count} scenes")
                if ch.screenplay_count:
                    parts.append(f"{ch.screenplay_count} screenplays")
                if ch.panel_count:
                    parts.append(f"{ch.panel_count} panels")
                detail = ", ".join(parts) if parts else "empty"
                lines.append(f"- **{label}** [{ch.status}] — {detail}")
            lines.append("")

        # Active decisions
        if brief.active_decisions:
            lines.append("### Active Author Decisions")
            lines.append("")
            for d in brief.active_decisions:
                lines.append(f"- {d}")
            lines.append("")

        # Last session
        if brief.last_session_summary:
            lines.append("### Last Session")
            lines.append("")
            lines.append(brief.last_session_summary)
            if brief.last_session_next_steps:
                lines.append("")
                lines.append(f"**Planned next**: {brief.last_session_next_steps}")
            lines.append("")

        # Next action
        lines.append("### Next Action")
        lines.append("")
        lines.append(f"**{brief.suggested_next_action}**")
        lines.append(f"```")
        lines.append(brief.suggested_command)
        lines.append(f"```")
        lines.append("")

        return "\n".join(lines)
