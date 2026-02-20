"""antigravity evaluate - evaluation commands."""

from __future__ import annotations

from typing import Optional

import typer

from antigravity_tool.core.project import Project
from antigravity_tool.services.base import ServiceContext
from antigravity_tool.services.evaluation_service import EvaluationService
from antigravity_tool.utils.display import print_success, print_prompt_output

app = typer.Typer(help="Story and panel evaluation commands.")


@app.command("scene")
def evaluate_scene(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    scene: int = typer.Option(..., "--scene", "-s", help="Scene number"),
    criteria: str = typer.Option(
        "all", "--criteria", help="Criteria: pacing,dialogue,consistency,emotional_arc,all"
    ),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a scene evaluation prompt (with author-level context)."""
    project = Project.find()
    svc = EvaluationService(ServiceContext.from_project(project))

    criteria_list = None
    if criteria != "all":
        criteria_list = [c.strip() for c in criteria.split(",")]

    prompt = svc.evaluate_scene(chapter, scene, criteria_list)

    if output:
        with open(output, "w") as f:
            f.write(prompt)
        print_success(f"Evaluation prompt saved to {output}")
    else:
        print_prompt_output(prompt, f"Evaluate Scene: Ch.{chapter} Sc.{scene}")


@app.command("panel-sequence")
def evaluate_panels(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Evaluate visual variety and flow across panels in a chapter."""
    project = Project.find()
    svc = EvaluationService(ServiceContext.from_project(project))

    prompt = svc.evaluate_panel_sequence(chapter)

    if output:
        with open(output, "w") as f:
            f.write(prompt)
        print_success(f"Evaluation prompt saved to {output}")
    else:
        print_prompt_output(prompt, f"Evaluate Panel Sequence: Chapter {chapter}")


@app.command("consistency")
def evaluate_consistency(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a cross-reference consistency check prompt."""
    project = Project.find()
    svc = EvaluationService(ServiceContext.from_project(project))

    prompt = svc.evaluate_consistency(chapter)

    if output:
        with open(output, "w") as f:
            f.write(prompt)
        print_success(f"Evaluation prompt saved to {output}")
    else:
        print_prompt_output(prompt, f"Consistency Check: Chapter {chapter}")


@app.command("dramatic-irony")
def evaluate_dramatic_irony(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    scene: int = typer.Option(..., "--scene", "-s", help="Scene number"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Analyze dramatic irony opportunities by comparing reader knowledge vs secrets."""
    project = Project.find()
    svc = EvaluationService(ServiceContext.from_project(project))

    prompt = svc.evaluate_dramatic_irony(chapter, scene)

    if output:
        with open(output, "w") as f:
            f.write(prompt)
        print_success(f"Evaluation prompt saved to {output}")
    else:
        print_prompt_output(prompt, f"Dramatic Irony: Ch.{chapter} Sc.{scene}")
