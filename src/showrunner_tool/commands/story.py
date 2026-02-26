"""showrunner story - story structure commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from showrunner_tool.core.project import Project
from showrunner_tool.services.base import ServiceContext
from showrunner_tool.services.story_service import StoryService
from showrunner_tool.utils.display import (
    console, print_success, print_info, print_error, print_prompt_output,
    create_table,
)

app = typer.Typer(help="Story structure commands.")


@app.command("outline")
def outline(
    structure: str = typer.Option(
        "save_the_cat", "--structure", "-s",
        help="Structure framework: save_the_cat, heros_journey, story_circle, kishotenketsu, custom"
    ),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a story outline prompt using the chosen structure framework."""
    project = Project.find()
    svc = StoryService(ServiceContext.from_project(project))
    result = svc.compile_outline_prompt(structure)

    if output:
        Path(output).write_text(result.prompt_text)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(result.prompt_text, f"Story Outline ({structure})")


@app.command("plan-arcs")
def plan_arcs(
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate character arc beats aligned with the story structure."""
    project = Project.find()
    svc = StoryService(ServiceContext.from_project(project))
    result = svc.compile_plan_arcs_prompt()

    if output:
        Path(output).write_text(result.prompt_text)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(result.prompt_text, "Character Arc Planning")


@app.command("show")
def show() -> None:
    """Display the current story structure."""
    project = Project.find()
    svc = StoryService(ServiceContext.from_project(project))
    structure = svc.get_structure()
    if not structure:
        print_info("No story structure found. Run 'showrunner story outline' first.")
        return

    console.print(f"\n[bold]{structure.title}[/] ({structure.structure_type.value})")
    console.print(f"[dim]Logline:[/] {structure.logline}")
    console.print(f"[dim]Premise:[/] {structure.premise}\n")

    if structure.beats:
        table = create_table("Story Beats", [
            ("#", "dim"),
            ("Beat", "cyan"),
            ("Act", "green"),
            ("%", "yellow"),
            ("Content", ""),
            ("Status", "magenta"),
        ])
        for beat in structure.beats:
            table.add_row(
                str(beat.beat_number),
                beat.beat_name,
                beat.act,
                f"{beat.target_percentage:.0%}",
                beat.content[:60] + "..." if len(beat.content) > 60 else beat.content,
                beat.status,
            )
        console.print(table)

    if structure.sub_arcs:
        console.print()
        arc_table = create_table("Sub-Arcs", [
            ("Name", "cyan"),
            ("Type", "magenta"),
            ("Chapters", "green"),
            ("Beats", "yellow"),
            ("Status", ""),
        ])
        for arc in structure.sub_arcs:
            ch_range = ""
            if arc.chapter_start is not None and arc.chapter_end is not None:
                ch_range = f"{arc.chapter_start}-{arc.chapter_end}"
            elif arc.chapter_start is not None:
                ch_range = f"{arc.chapter_start}+"
            arc_table.add_row(
                arc.name,
                arc.arc_type.value if hasattr(arc.arc_type, "value") else str(arc.arc_type),
                ch_range,
                str(len(arc.beats)),
                arc.status,
            )
        console.print(arc_table)


@app.command("add-arc")
def add_arc(
    name: str = typer.Argument(..., help="Sub-arc name"),
    arc_type: str = typer.Option("custom", "--type", "-t", help="Arc type: training, tournament, flashback, romance, investigation, quest, revelation, custom"),
    start_chapter: Optional[int] = typer.Option(None, "--start-chapter", help="Starting chapter"),
    end_chapter: Optional[int] = typer.Option(None, "--end-chapter", help="Ending chapter"),
    description: str = typer.Option("", "--desc", "-d", help="Arc description"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save planning prompt to file"),
) -> None:
    """Add a sub-arc to the story structure and generate a planning prompt."""
    project = Project.find()
    svc = StoryService(ServiceContext.from_project(project))

    try:
        svc.add_sub_arc(name, arc_type, description, start_chapter, end_chapter)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    print_success(f"Added sub-arc '{name}' ({arc_type})")

    result = svc.compile_sub_arc_prompt(name, arc_type, start_chapter, end_chapter)
    if output:
        Path(output).write_text(result.prompt_text)
        print_success(f"Planning prompt saved to {output}")
    else:
        print_prompt_output(result.prompt_text, f"Plan Sub-Arc: {name}")


@app.command("list-arcs")
def list_arcs() -> None:
    """List all sub-arcs in the story structure."""
    project = Project.find()
    svc = StoryService(ServiceContext.from_project(project))
    structure = svc.get_structure()
    if not structure or not structure.sub_arcs:
        print_info("No sub-arcs defined. Use 'showrunner story add-arc' to create one.")
        return

    table = create_table("Sub-Arcs", [
        ("Name", "cyan"),
        ("Type", "magenta"),
        ("Chapters", "green"),
        ("Description", ""),
        ("Beats", "yellow"),
        ("Status", ""),
    ])
    for arc in structure.sub_arcs:
        ch_range = ""
        if arc.chapter_start is not None and arc.chapter_end is not None:
            ch_range = f"{arc.chapter_start}-{arc.chapter_end}"
        elif arc.chapter_start is not None:
            ch_range = f"{arc.chapter_start}+"
        table.add_row(
            arc.name,
            arc.arc_type.value if hasattr(arc.arc_type, "value") else str(arc.arc_type),
            ch_range,
            arc.description[:50] + "..." if len(arc.description) > 50 else arc.description,
            str(len(arc.beats)),
            arc.status,
        )
    console.print(table)


@app.command("show-arc")
def show_arc(
    name: str = typer.Argument(..., help="Sub-arc name"),
) -> None:
    """Display details of a specific sub-arc."""
    project = Project.find()
    svc = StoryService(ServiceContext.from_project(project))
    structure = svc.get_structure()
    if not structure or not structure.sub_arcs:
        print_info("No sub-arcs defined.")
        return

    arc = next((a for a in structure.sub_arcs if a.name.lower() == name.lower()), None)
    if not arc:
        print_error(f"Sub-arc '{name}' not found.")
        raise typer.Exit(1)

    console.print(f"\n[bold]{arc.name}[/] ({arc.arc_type.value})")
    if arc.description:
        console.print(f"[dim]{arc.description}[/]")
    ch_range = ""
    if arc.chapter_start is not None and arc.chapter_end is not None:
        ch_range = f"Chapters {arc.chapter_start}-{arc.chapter_end}"
    elif arc.chapter_start is not None:
        ch_range = f"Starting Chapter {arc.chapter_start}"
    if ch_range:
        console.print(f"[dim]{ch_range}[/]")
    console.print(f"[dim]Status:[/] {arc.status}\n")

    if arc.beats:
        table = create_table(f"{arc.name} -- Beats", [
            ("#", "dim"),
            ("Beat", "cyan"),
            ("Content", ""),
            ("Status", "magenta"),
        ])
        for beat in arc.beats:
            table.add_row(
                str(beat.beat_number),
                beat.beat_name,
                beat.content[:60] + "..." if len(beat.content) > 60 else beat.content,
                beat.status,
            )
        console.print(table)
    else:
        print_info("No beats defined yet. Generate them with 'showrunner story add-arc' planning prompt.")
