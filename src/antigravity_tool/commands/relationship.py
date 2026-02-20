"""antigravity relationship - character relationship graph management."""

from __future__ import annotations

from typing import Optional

import typer
import yaml

from antigravity_tool.core.project import Project
from antigravity_tool.schemas.character import RelationshipEdge, RelationshipEvolution, RelationshipGraph
from antigravity_tool.utils.display import console, create_table, print_success, print_info, print_error
from antigravity_tool.utils.io import read_yaml, write_yaml

app = typer.Typer(help="Character relationship graph management.")


def _load_graph(project: Project) -> RelationshipGraph:
    path = project.path / "story" / "relationships.yaml"
    if path.exists():
        data = read_yaml(path)
        if data:
            return RelationshipGraph(**data)
    return RelationshipGraph()


def _save_graph(project: Project, graph: RelationshipGraph) -> None:
    path = project.path / "story" / "relationships.yaml"
    write_yaml(path, graph.model_dump(mode="json"))


@app.command("add")
def add_relationship(
    char1: str = typer.Argument(..., help="First character name"),
    char2: str = typer.Argument(..., help="Second character name"),
    type: str = typer.Option("", "--type", "-t", help="Relationship type: ally, rival, mentor_student, romantic, family, enemy"),
    label: str = typer.Option("", "--label", "-l", help="Short description"),
    dynamic: str = typer.Option("", "--dynamic", "-d", help="Current dynamic: growing closer, building tension, etc."),
    intensity: int = typer.Option(5, "--intensity", "-i", help="Intensity 1-10"),
    hidden: bool = typer.Option(False, "--hidden", help="Not yet known to the reader"),
) -> None:
    """Add a relationship edge between two characters."""
    project = Project.find()
    graph = _load_graph(project)

    edge = RelationshipEdge(
        source_name=char1,
        target_name=char2,
        relationship_type=type,
        label=label,
        dynamic=dynamic,
        intensity=intensity,
        known_to_reader=not hidden,
    )
    graph.edges.append(edge)
    _save_graph(project, graph)
    print_success(f"Added relationship: {char1} ↔ {char2} ({type or 'untyped'})")


@app.command("list")
def list_relationships() -> None:
    """List all character relationships."""
    project = Project.find()
    graph = _load_graph(project)

    if not graph.edges:
        print_info("No relationships defined. Use 'antigravity relationship add' to create one.")
        return

    table = create_table("Relationships", [
        ("From", ""),
        ("To", ""),
        ("Type", ""),
        ("Label", ""),
        ("Dynamic", ""),
        ("Intensity", ""),
        ("Visible", ""),
    ])
    for e in graph.edges:
        table.add_row(
            e.source_name, e.target_name, e.relationship_type,
            e.label, e.dynamic, str(e.intensity),
            "[green]yes[/]" if e.known_to_reader else "[red]hidden[/]",
        )
    console.print(table)


@app.command("show")
def show_character_relationships(
    name: str = typer.Argument(..., help="Character name"),
) -> None:
    """Show all relationships for a specific character."""
    project = Project.find()
    graph = _load_graph(project)

    edges = [
        e for e in graph.edges
        if e.source_name.lower() == name.lower() or e.target_name.lower() == name.lower()
    ]
    if not edges:
        print_info(f"No relationships found for '{name}'.")
        return

    console.print(f"\n[bold]{name}[/] — Relationships\n")
    for e in edges:
        other = e.target_name if e.source_name.lower() == name.lower() else e.source_name
        parts = [f"[bold]{other}[/]"]
        if e.relationship_type:
            parts.append(f"({e.relationship_type})")
        if e.label:
            parts.append(f"— {e.label}")
        if e.dynamic:
            parts.append(f"[dim][{e.dynamic}][/]")
        console.print(f"  {'↔' if e.known_to_reader else '⊘'} {' '.join(parts)}")

    # Show evolution
    evolutions = [
        ev for ev in graph.evolution
        if ev.source_name.lower() == name.lower() or ev.target_name.lower() == name.lower()
    ]
    if evolutions:
        console.print(f"\n[bold]Evolution:[/]")
        for ev in evolutions:
            other = ev.target_name if ev.source_name.lower() == name.lower() else ev.source_name
            console.print(f"  Ch{ev.chapter}: {other} — {ev.change_description}")

    console.print()


@app.command("graph")
def show_graph() -> None:
    """Display an ASCII visualization of the relationship graph."""
    project = Project.find()
    graph = _load_graph(project)

    if not graph.edges:
        print_info("No relationships to visualize.")
        return

    # Collect all characters
    chars = set()
    for e in graph.edges:
        chars.add(e.source_name)
        chars.add(e.target_name)

    console.print("\n[bold]Character Relationship Graph[/]\n")

    # Simple adjacency display
    for char in sorted(chars):
        console.print(f"  [bold]{char}[/]")
        edges = [e for e in graph.edges if e.source_name == char or e.target_name == char]
        for e in edges:
            other = e.target_name if e.source_name == char else e.source_name
            arrow = "──" if e.known_to_reader else "╌╌"
            type_label = f" ({e.relationship_type})" if e.relationship_type else ""
            intensity_bar = "█" * (e.intensity // 2) + "░" * (5 - e.intensity // 2)
            console.print(f"    {arrow}▶ {other}{type_label} [{intensity_bar}]")
        console.print()


@app.command("evolve")
def evolve_relationship(
    char1: str = typer.Argument(..., help="First character"),
    char2: str = typer.Argument(..., help="Second character"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    change: str = typer.Option(..., "--change", help="Description of how the relationship changed"),
    scene: Optional[int] = typer.Option(None, "--scene", "-s"),
    trigger: str = typer.Option("", "--trigger", help="What triggered the change"),
    new_dynamic: str = typer.Option("", "--dynamic", "-d", help="New relationship dynamic"),
) -> None:
    """Record a relationship evolution at a specific chapter."""
    project = Project.find()
    graph = _load_graph(project)

    ev = RelationshipEvolution(
        source_name=char1,
        target_name=char2,
        chapter=chapter,
        scene=scene,
        change_description=change,
        new_dynamic=new_dynamic,
        trigger_event=trigger,
    )
    graph.evolution.append(ev)

    # Update the edge's dynamic if provided
    if new_dynamic:
        for e in graph.edges:
            if (
                (e.source_name == char1 and e.target_name == char2)
                or (e.source_name == char2 and e.target_name == char1)
            ):
                e.dynamic = new_dynamic
                break

    _save_graph(project, graph)
    print_success(f"Recorded evolution: {char1} ↔ {char2} at Ch{chapter} — {change}")
