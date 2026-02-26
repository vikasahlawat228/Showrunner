"""showrunner character - character management commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import yaml

from showrunner_tool.core.project import Project
from showrunner_tool.services.base import ServiceContext
from showrunner_tool.services.character_service import CharacterService
from showrunner_tool.utils.display import (
    console, print_success, print_info, print_prompt_output,
    print_yaml, create_table,
)

app = typer.Typer(help="Character management commands.")


@app.command("create")
def create(
    name: str = typer.Argument(..., help="Character name"),
    role: str = typer.Option("supporting", "--role", "-r", help="Character role"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a character creation prompt."""
    project = Project.find()
    svc = CharacterService(ServiceContext.from_project(project))
    result = svc.compile_create_prompt(name, role)

    if output:
        Path(output).write_text(result.prompt_text)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(result.prompt_text, f"Create Character: {name}")


@app.command("generate-dna")
def generate_dna(
    name: str = typer.Argument(..., help="Character name"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate/regenerate a Character DNA block for image consistency."""
    project = Project.find()
    svc = CharacterService(ServiceContext.from_project(project))
    result = svc.compile_dna_prompt(name)

    if output:
        Path(output).write_text(result.prompt_text)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(result.prompt_text, f"Generate DNA: {name}")


@app.command("show-dna")
def show_dna(
    name: str = typer.Argument(..., help="Character name"),
) -> None:
    """Display a character's DNA prompt block."""
    project = Project.find()
    svc = CharacterService(ServiceContext.from_project(project))
    char = svc.get(name)
    if not char:
        print_info(f"Character '{name}' not found.")
        return
    if not char.dna.face.face_shape:
        print_info(f"No DNA block for '{name}'. Run 'showrunner character generate-dna {name}'.")
        return
    console.print()
    console.print(f"[bold]Character DNA: {char.name}[/]")
    console.print()
    console.print(char.dna.to_prompt_block())
    console.print()


@app.command("list")
def list_characters() -> None:
    """List all characters in the project."""
    project = Project.find()
    svc = CharacterService(ServiceContext.from_project(project))
    characters = svc.list_all(filter_secrets=False)
    if not characters:
        print_info("No characters found. Run 'showrunner character create' first.")
        return

    table = create_table("Characters", [
        ("Name", "cyan"),
        ("Role", "green"),
        ("One-line", ""),
        ("Has DNA", "yellow"),
    ])
    for char in characters:
        has_dna = "Yes" if char.dna.face.face_shape else "No"
        table.add_row(char.name, char.role.value, char.one_line[:50], has_dna)
    console.print(table)


@app.command("show")
def show(
    name: str = typer.Argument(..., help="Character name"),
) -> None:
    """Display full character details."""
    project = Project.find()
    svc = CharacterService(ServiceContext.from_project(project))
    char = svc.get(name)
    if not char:
        print_info(f"Character '{name}' not found.")
        return
    print_yaml(
        yaml.dump(char.model_dump(mode="json"), default_flow_style=False, sort_keys=False),
        f"Character: {char.name}"
    )
