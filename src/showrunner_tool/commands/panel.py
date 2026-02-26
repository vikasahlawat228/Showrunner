"""showrunner panel - panel division commands."""

from __future__ import annotations

from typing import Optional

import typer

from showrunner_tool.core.project import Project
from showrunner_tool.services.base import ServiceContext
from showrunner_tool.services.panel_service import PanelService
from showrunner_tool.services.scene_service import SceneService
from showrunner_tool.utils.display import console, print_success, print_info, print_prompt_output, create_table

app = typer.Typer(help="Panel division commands.")


@app.command("divide")
def divide(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    scene: int = typer.Option(..., "--scene", "-s", help="Scene number"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Divide a screenplay into panel compositions."""
    project = Project.find()
    svc = PanelService(ServiceContext.from_project(project))
    result = svc.compile_divide_prompt(chapter, scene)

    if output:
        with open(output, "w") as f:
            f.write(result.prompt_text)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(result.prompt_text, f"Panel Division: Ch.{chapter} Sc.{scene}")


@app.command("batch")
def batch(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir"),
) -> None:
    """Divide all screenplays in a chapter into panels."""
    project = Project.find()
    ctx = ServiceContext.from_project(project)
    panel_svc = PanelService(ctx)
    scene_svc = SceneService(ctx)
    screenplays = scene_svc.list_screenplays(chapter)

    if not screenplays:
        print_info(f"No screenplays found in chapter {chapter}.")
        return

    for i, sp in enumerate(screenplays, 1):
        result = panel_svc.compile_divide_prompt(chapter, i)

        if output_dir:
            from pathlib import Path
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            p = out / f"panels-ch{chapter:02d}-sc{i:02d}.md"
            p.write_text(result.prompt_text)
            print_success(f"Saved: {p}")
        else:
            print_prompt_output(result.prompt_text, f"Panel Division: Ch.{chapter} Sc.{i}")


@app.command("list")
def list_panels(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
) -> None:
    """List all panels in a chapter."""
    project = Project.find()
    svc = PanelService(ServiceContext.from_project(project))
    panels = svc.list_panels(chapter)

    if not panels:
        print_info(f"No panels found in chapter {chapter}.")
        return

    table = create_table(f"Chapter {chapter} Panels", [
        ("Page", "dim"),
        ("Panel", "cyan"),
        ("Shot", "green"),
        ("Angle", "yellow"),
        ("Characters", ""),
        ("Has Prompt", "magenta"),
    ])
    for p in panels:
        table.add_row(
            str(p.page_number),
            str(p.panel_number),
            p.shot_type.value,
            p.camera_angle.value,
            str(len(p.characters)),
            "Yes" if p.image_prompt else "No",
        )
    console.print(table)
