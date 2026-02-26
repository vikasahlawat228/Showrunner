"""showrunner screenplay - screenplay writing commands."""

from __future__ import annotations

from typing import Optional

import typer

from showrunner_tool.core.project import Project
from showrunner_tool.services.base import ServiceContext
from showrunner_tool.services.scene_service import SceneService
from showrunner_tool.utils.display import console, print_success, print_info, print_prompt_output

app = typer.Typer(help="Screenplay writing commands.")


@app.command("generate")
def generate(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    scene: int = typer.Option(..., "--scene", "-s", help="Scene number"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a screenplay from a scene."""
    project = Project.find()
    svc = SceneService(ServiceContext.from_project(project))
    result = svc.compile_screenplay_prompt(chapter, scene)

    if output:
        with open(output, "w") as f:
            f.write(result.prompt_text)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(result.prompt_text, f"Screenplay: Ch.{chapter} Sc.{scene}")


@app.command("batch")
def batch(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", help="Directory to save prompts"),
) -> None:
    """Generate screenplay prompts for all scenes in a chapter."""
    project = Project.find()
    svc = SceneService(ServiceContext.from_project(project))
    scenes = svc.list_scenes(chapter)

    if not scenes:
        print_info(f"No scenes found in chapter {chapter}.")
        return

    for scene in scenes:
        result = svc.compile_screenplay_prompt(chapter, scene.scene_number)

        if output_dir:
            from pathlib import Path
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            p = out / f"screenplay-ch{chapter:02d}-sc{scene.scene_number:02d}.md"
            p.write_text(result.prompt_text)
            print_success(f"Saved: {p}")
        else:
            print_prompt_output(result.prompt_text, f"Screenplay: Ch.{chapter} Sc.{scene.scene_number}")
