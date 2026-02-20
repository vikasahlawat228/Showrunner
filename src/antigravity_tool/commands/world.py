"""antigravity world - world building commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import yaml

from antigravity_tool.core.project import Project
from antigravity_tool.services.base import ServiceContext
from antigravity_tool.services.world_service import WorldService
from antigravity_tool.utils.display import print_success, print_info, print_prompt_output, print_yaml

app = typer.Typer(help="World building commands.")


@app.command("build")
def build(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save prompt to file"),
) -> None:
    """Generate a world-building prompt with current project context."""
    project = Project.find()
    svc = WorldService(ServiceContext.from_project(project))
    result = svc.compile_build_prompt()

    if output:
        Path(output).write_text(result.prompt_text)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(result.prompt_text, "World Building Prompt")


@app.command("show")
def show() -> None:
    """Display current world state."""
    project = Project.find()
    svc = WorldService(ServiceContext.from_project(project))
    ws = svc.get_settings()
    if not ws:
        print_info("No world settings found. Run 'antigravity world build' first.")
        return
    print_yaml(yaml.dump(ws.model_dump(mode="json"), default_flow_style=False, sort_keys=False), "World Settings")


@app.command("add-location")
def add_location(
    name: str = typer.Argument(..., help="Location name"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a prompt to add a new location to the world."""
    project = Project.find()
    svc = WorldService(ServiceContext.from_project(project))
    result = svc.compile_add_location_prompt(name)

    if output:
        Path(output).write_text(result.prompt_text)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(result.prompt_text, f"Add Location: {name}")


@app.command("add-rule")
def add_rule(
    name: str = typer.Argument(..., help="Rule name"),
    category: str = typer.Option("magic", "--category", "-c", help="Rule category"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a prompt to add a new world rule."""
    project = Project.find()
    svc = WorldService(ServiceContext.from_project(project))
    result = svc.compile_add_rule_prompt(name, category)

    if output:
        Path(output).write_text(result.prompt_text)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(result.prompt_text, f"Add Rule: {name}")
