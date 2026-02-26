"""showrunner decide — persistent decision logging."""

from __future__ import annotations

from typing import Optional

import typer

from showrunner_tool.core.project import Project
from showrunner_tool.core.session_manager import DecisionLog
from showrunner_tool.utils.display import console, print_success, print_info, create_table

app = typer.Typer(help="Log and manage author decisions that persist across sessions.")


@app.command("add")
def add_decision(
    decision: str = typer.Argument(..., help="The decision to record"),
    category: str = typer.Option(
        "meta", "--category", "-t",
        help="Category: style, tone, character, plot, visual, pacing, world, meta"
    ),
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Scope to chapter N"),
    scene: Optional[int] = typer.Option(None, "--scene", help="Scope to scene N (requires --chapter)"),
    character: Optional[str] = typer.Option(None, "--character", help="Scope to a character"),
) -> None:
    """Record a persistent author decision."""
    project = Project.find()
    dl = DecisionLog(project.path)
    entry = dl.add(decision, category, chapter=chapter, scene=scene, character_name=character)

    scope_label = entry.scope.level
    if entry.scope.chapter:
        scope_label = f"chapter {entry.scope.chapter}"
    if entry.scope.scene:
        scope_label += f" scene {entry.scope.scene}"
    if entry.scope.character_name:
        scope_label = f"character: {entry.scope.character_name}"

    print_success(f"Decision logged [{entry.category.value}] ({scope_label}): {decision}")


@app.command("list")
def list_decisions(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Filter by chapter"),
    category: Optional[str] = typer.Option(None, "--category", "-t", help="Filter by category"),
    all_decisions: bool = typer.Option(False, "--all", "-a", help="Include inactive decisions"),
) -> None:
    """List all recorded decisions."""
    project = Project.find()
    dl = DecisionLog(project.path)
    results = dl.query(chapter=chapter, category=category, active_only=not all_decisions)

    if not results:
        print_info("No decisions found.")
        return

    table = create_table("Author Decisions", [
        ("#", ""), ("Category", ""), ("Scope", ""), ("Decision", ""), ("Active", ""),
    ])
    for i, d in enumerate(results):
        scope_label = d.scope.level
        if d.scope.chapter:
            scope_label = f"ch {d.scope.chapter}"
        if d.scope.scene:
            scope_label += f" sc {d.scope.scene}"
        if d.scope.character_name:
            scope_label = d.scope.character_name
        active = "[green]yes[/]" if d.active else "[dim]no[/]"
        table.add_row(str(i), d.category.value, scope_label, d.decision, active)

    console.print(table)


@app.command("remove")
def deactivate_decision(
    index: int = typer.Argument(..., help="Decision index to deactivate (from 'decide list')"),
) -> None:
    """Deactivate a decision (mark as no longer active)."""
    project = Project.find()
    dl = DecisionLog(project.path)
    if index < 0 or index >= len(dl.decisions):
        console.print(f"[red]Invalid index {index}. Run 'showrunner decide list --all' to see indices.[/]")
        raise typer.Exit(1)
    dl.deactivate(index)
    print_success(f"Decision #{index} deactivated.")
