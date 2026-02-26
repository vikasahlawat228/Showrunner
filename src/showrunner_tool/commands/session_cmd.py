"""showrunner session — session lifecycle management."""

from __future__ import annotations

from typing import Optional

import typer

from showrunner_tool.core.project import Project
from showrunner_tool.core.session_manager import SessionLog
from showrunner_tool.core.workflow import WorkflowState
from showrunner_tool.schemas.session import SessionEntry
from showrunner_tool.utils.display import console, print_success, print_info, create_table

app = typer.Typer(help="Session tracking for cross-session continuity.")


@app.command("start")
def start_session(
    focus: Optional[str] = typer.Option(None, "--focus", "-f", help="What this session focuses on"),
) -> None:
    """Start a new working session (records the beginning of a work block)."""
    project = Project.find()
    sl = SessionLog(project.path)
    wf = WorkflowState(project.path)

    entry = sl.start_session()
    entry.workflow_step_start = wf.get_current_step()
    if focus:
        entry.summary = f"Focus: {focus}"

    path = sl.save_session(entry)
    print_success(f"Session started: {entry.notes}")
    print_info(f"Current workflow step: {wf.get_current_step()}")
    console.print(f"[dim]Log: {path}[/]")


@app.command("end")
def end_session(
    summary: str = typer.Argument(..., help="Brief summary of what was accomplished"),
    next_steps: Optional[str] = typer.Option(None, "--next", "-n", help="What to do next session"),
) -> None:
    """End the current session with a summary."""
    project = Project.find()
    sl = SessionLog(project.path)
    wf = WorkflowState(project.path)

    # Load the most recent session to update it
    recent = sl.load_latest(1)
    if recent:
        entry = recent[0]
        entry.summary = summary
        entry.workflow_step_end = wf.get_current_step()
        if next_steps:
            entry.next_steps = next_steps
        sl.save_session(entry)
        print_success("Session ended and saved.")
    else:
        # No active session — create one with just the end summary
        entry = sl.start_session()
        entry.summary = summary
        entry.workflow_step_end = wf.get_current_step()
        if next_steps:
            entry.next_steps = next_steps
        sl.save_session(entry)
        print_success("Session summary saved (no active session found, created retroactively).")

    # Auto-update CLAUDE.md
    from showrunner_tool.core.briefing import BriefingGenerator
    gen = BriefingGenerator(project)
    brief = gen.generate()
    dynamic_section = gen.render_markdown(brief)

    claude_md_path = project.path / "CLAUDE.md"
    if claude_md_path.exists():
        content = claude_md_path.read_text()
        start_marker = "<!-- DYNAMIC:START -->"
        end_marker = "<!-- DYNAMIC:END -->"
        if start_marker in content and end_marker in content:
            before = content[:content.index(start_marker) + len(start_marker)]
            after = content[content.index(end_marker):]
            claude_md_path.write_text(f"{before}\n\n{dynamic_section}\n{after}")
            print_info("CLAUDE.md updated with session state.")


@app.command("history")
def session_history(
    count: int = typer.Option(5, "--count", "-n", help="Number of sessions to show"),
) -> None:
    """Show recent session history."""
    project = Project.find()
    sl = SessionLog(project.path)
    sessions = sl.load_latest(count)

    if not sessions:
        print_info("No session history found.")
        return

    table = create_table("Session History", [
        ("Date", ""), ("Summary", ""), ("Step", ""), ("Next Steps", ""),
    ])
    for s in sessions:
        step = s.workflow_step_end or s.workflow_step_start or "?"
        table.add_row(
            s.session_date,
            s.summary[:60] + "..." if len(s.summary) > 60 else s.summary,
            step,
            (s.next_steps[:40] + "...") if s.next_steps and len(s.next_steps) > 40 else (s.next_steps or ""),
        )

    console.print(table)
