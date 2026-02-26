"""showrunner scene - scene writing commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from showrunner_tool.core.project import Project
from showrunner_tool.services.base import ServiceContext
from showrunner_tool.services.scene_service import SceneService
from showrunner_tool.utils.display import (
    console, print_success, print_info, print_prompt_output,
    create_table,
)

app = typer.Typer(help="Scene writing commands.")


@app.command("write")
def write(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    scene: int = typer.Option(..., "--scene", "-s", help="Scene number"),
    beat: Optional[str] = typer.Option(None, "--beat", "-b", help="Story beat reference"),
    scene_type: Optional[str] = typer.Option(None, "--type", help="Scene type: action, dialogue, flashback, montage, training, reveal, confrontation, chase, calm_before_storm, transition, emotional, worldbuilding"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a scene writing prompt with full context injection."""
    project = Project.find()
    svc = SceneService(ServiceContext.from_project(project))
    result = svc.compile_write_prompt(chapter, scene, beat_reference=beat, scene_type=scene_type)

    if output:
        Path(output).write_text(result.prompt_text)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(result.prompt_text, f"Write Scene: Ch.{chapter} Sc.{scene}")

    console.print("[dim]After writing the scene, run the knowledge extraction prompt below[/]")
    console.print("[dim]to auto-update the reader knowledge state:[/]")
    console.print()


@app.command("plan")
def plan(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a prompt to plan scenes for a chapter."""
    project = Project.find()
    svc = SceneService(ServiceContext.from_project(project))
    result = svc.compile_plan_prompt(chapter)

    if output:
        Path(output).write_text(result.prompt_text)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(result.prompt_text, f"Plan Scenes: Chapter {chapter}")


@app.command("list")
def list_scenes(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
) -> None:
    """List all scenes in a chapter."""
    project = Project.find()
    svc = SceneService(ServiceContext.from_project(project))
    scenes = svc.list_scenes(chapter)
    if not scenes:
        print_info(f"No scenes in chapter {chapter}.")
        return

    table = create_table(f"Chapter {chapter} Scenes", [
        ("#", "dim"),
        ("Title", "cyan"),
        ("Type", "magenta"),
        ("Location", "green"),
        ("Mood", "yellow"),
        ("Tension", "red"),
        ("Characters", ""),
    ])
    for s in scenes:
        tension_bar = "\u2588" * (s.tension_level // 2) + "\u2591" * (5 - s.tension_level // 2)
        table.add_row(
            str(s.scene_number),
            s.title,
            s.scene_type.value if hasattr(s.scene_type, "value") else str(s.scene_type),
            s.location_name,
            s.mood,
            f"{s.tension_level} [{tension_bar}]",
            str(len(s.characters_present)),
        )
    console.print(table)
