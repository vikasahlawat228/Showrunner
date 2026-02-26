"""showrunner reference - reference image management commands."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import typer

from showrunner_tool.core.project import Project
from showrunner_tool.schemas.assets import ReferenceImage, ReferenceLibrary, ReferenceType
from showrunner_tool.utils.display import (
    console, create_table, print_success, print_info, print_error,
)
from showrunner_tool.utils.io import read_yaml, write_yaml, ensure_dir
from showrunner_tool.utils.ids import generate_id

app = typer.Typer(help="Reference image management.")


def _load_library(project: Project) -> ReferenceLibrary:
    p = project.path / "assets" / "references" / "library.yaml"
    if not p.exists():
        return ReferenceLibrary()
    return ReferenceLibrary(**read_yaml(p))


def _save_library(project: Project, library: ReferenceLibrary) -> None:
    ref_dir = ensure_dir(project.path / "assets" / "references")
    write_yaml(ref_dir / "library.yaml", library.model_dump(mode="json"))


@app.command("add")
def add_reference(
    path: str = typer.Argument(..., help="Path to the reference image file"),
    ref_type: str = typer.Option("style", "--type", "-t", help="Reference type: character, location, outfit, mood_board, style, prop, effect"),
    link: Optional[str] = typer.Option(None, "--link", "-l", help="Entity to link to (character name, location name, etc.)"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Description of this reference"),
) -> None:
    """Add a reference image to the project library."""
    project = Project.find()
    source_path = Path(path)

    if not source_path.exists():
        print_error(f"File not found: {path}")
        raise typer.Exit(1)

    # Copy file to references directory
    ref_dir = ensure_dir(project.path / "assets" / "references")
    dest = ref_dir / source_path.name
    if dest.exists():
        dest = ref_dir / f"{source_path.stem}_{generate_id()[:8]}{source_path.suffix}"
    shutil.copy2(source_path, dest)

    # Parse reference type
    try:
        rtype = ReferenceType(ref_type)
    except ValueError:
        print_error(f"Unknown type: {ref_type}. Options: {', '.join(t.value for t in ReferenceType)}")
        raise typer.Exit(1)

    # Create reference entry
    ref = ReferenceImage(
        filename=dest.name,
        reference_type=rtype,
        linked_entity_name=link or "",
        description=description or "",
        source="uploaded",
    )

    library = _load_library(project)
    library.references.append(ref)
    _save_library(project, library)

    print_success(f"Added reference: {dest.name}")
    if link:
        console.print(f"  [dim]Linked to:[/] {link}")
    console.print(f"  [dim]Type:[/] {rtype.value}")


@app.command("list")
def list_references(
    ref_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by type"),
    link: Optional[str] = typer.Option(None, "--link", "-l", help="Filter by linked entity"),
) -> None:
    """List all reference images."""
    project = Project.find()
    library = _load_library(project)

    refs = library.references
    if ref_type:
        try:
            rtype = ReferenceType(ref_type)
            refs = library.get_by_type(rtype)
        except ValueError:
            pass
    if link:
        refs = [r for r in refs if r.linked_entity_name == link]

    if not refs:
        print_info("No reference images found.")
        return

    table = create_table("Reference Library", [
        ("ID", "dim"),
        ("Filename", "cyan"),
        ("Type", "magenta"),
        ("Linked To", "green"),
        ("Description", ""),
    ])

    for ref in refs:
        table.add_row(
            ref.id[:8],
            ref.filename,
            ref.reference_type.value,
            ref.linked_entity_name or "-",
            ref.description[:50] + "..." if len(ref.description) > 50 else ref.description,
        )

    console.print(table)


@app.command("show")
def show_reference(
    name: str = typer.Argument(..., help="Entity name to show references for"),
) -> None:
    """Show all references linked to an entity."""
    project = Project.find()
    library = _load_library(project)

    refs = library.get_for_entity(name)
    if not refs:
        print_info(f"No references found for '{name}'.")
        return

    console.print(f"\n[bold]References for {name}[/]\n")
    for ref in refs:
        ref_path = project.path / "assets" / "references" / ref.filename
        exists = "[green]exists[/]" if ref_path.exists() else "[red]missing[/]"
        console.print(f"  [{ref.reference_type.value}] {ref.filename} ({exists})")
        if ref.description:
            console.print(f"    [dim]{ref.description}[/]")


@app.command("remove")
def remove_reference(
    ref_id: str = typer.Argument(..., help="Reference ID (first 8 chars is enough)"),
    delete_file: bool = typer.Option(False, "--delete-file", help="Also delete the image file"),
) -> None:
    """Remove a reference from the library."""
    project = Project.find()
    library = _load_library(project)

    target = None
    for ref in library.references:
        if ref.id.startswith(ref_id):
            target = ref
            break

    if not target:
        print_error(f"Reference '{ref_id}' not found.")
        raise typer.Exit(1)

    library.references.remove(target)
    _save_library(project, library)

    if delete_file:
        ref_path = project.path / "assets" / "references" / target.filename
        if ref_path.exists():
            ref_path.unlink()
            console.print(f"  [dim]Deleted file: {target.filename}[/]")

    print_success(f"Removed reference: {target.filename}")
