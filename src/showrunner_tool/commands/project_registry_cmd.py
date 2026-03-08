"""CLI commands for project registry management."""

from __future__ import annotations

from pathlib import Path

import typer

from showrunner_tool.services.project_registry_service import ProjectRegistryService
from showrunner_tool.utils.display import console, create_table

app = typer.Typer(
    name="project",
    help="Manage registered projects (list, set active, register, remove)",
    no_args_is_help=True,
)


@app.command("list")
def list_projects():
    """List all registered projects."""
    registry = ProjectRegistryService()
    projects = registry.get_all_projects()

    if not projects:
        console.print("[dim]No projects registered yet[/]")
        console.print("\n[bold]Register a project:[/]")
        console.print("  showrunner project register /path/to/project")
        return

    active_id = registry.get_active_project_id()
    table = create_table(
        title="Registered Projects",
        columns=["ID", "Name", "Path", "Status", "Last Opened"],
    )

    for project in projects:
        status = "[green]active[/]" if project.id == active_id else ""
        table.add_row(
            project.id,
            project.name,
            str(Path(project.path).relative_to(Path.home())),
            status,
            project.last_opened[:10] if project.last_opened else "—",
        )

    console.print(table)


@app.command("current")
def current_project():
    """Show the currently active project."""
    registry = ProjectRegistryService()
    project = registry.get_active_project()

    if not project:
        console.print("[yellow]No active project set[/]")
        console.print("\n[bold]Set one:[/]")
        console.print("  showrunner project set <project-id>")
        console.print("\n[bold]Or register a project:[/]")
        console.print("  showrunner project register /path/to/project")
        return

    console.print(f"\n[bold]Active Project[/]")
    console.print(f"  ID: {project.id}")
    console.print(f"  Name: {project.name}")
    console.print(f"  Path: {project.path}")
    console.print(f"  Tags: {', '.join(project.tags) if project.tags else '(none)'}")
    console.print(f"  Last Opened: {project.last_opened}\n")


@app.command("set")
def set_active_project(project_id: str):
    """Set the active project by ID.

    Args:
        project_id: ID of the project to activate
    """
    registry = ProjectRegistryService()

    if not registry.set_active_project(project_id):
        console.print(f"[red]Project not found: {project_id}[/]")
        console.print("\n[bold]Available projects:[/]")
        list_projects()
        raise typer.Exit(1)

    project = registry.get_project_by_id(project_id)
    console.print(f"\n[green]✓ Active project set to:{project_id}[/]")
    console.print(f"  {project.name} ({project.path})\n")


@app.command("register")
def register_project(
    path: str,
    name: typer.Option(None, help="Human-readable project name"),
    tags: typer.Option(None, help="Comma-separated tags"),
):
    """Register a new project.

    Args:
        path: Path to the project directory
    """
    project_path = Path(path).resolve()

    if not project_path.exists():
        console.print(f"[red]Path does not exist: {path}[/]")
        raise typer.Exit(1)

    if not (project_path / "showrunner.yaml").exists():
        console.print(f"[red]Not a Showrunner project (no showrunner.yaml): {path}[/]")
        raise typer.Exit(1)

    registry = ProjectRegistryService()
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    project = registry.register_project(str(project_path), name=name, tags=tag_list)

    console.print(f"\n[green]✓ Project registered[/]")
    console.print(f"  ID: {project.id}")
    console.print(f"  Name: {project.name}")
    console.print(f"  Path: {project.path}\n")

    # Optionally set as active
    set_active = typer.confirm("Set as active project?", default=True)
    if set_active:
        registry.set_active_project(project.id)
        console.print(f"[green]✓ Active project set[/]\n")


@app.command("remove")
def remove_project(
    project_id: str,
    force: typer.Option(False, "--force", help="Skip confirmation"),
):
    """Remove a project from the registry.

    Args:
        project_id: ID of the project to remove
    """
    registry = ProjectRegistryService()
    project = registry.get_project_by_id(project_id)

    if not project:
        console.print(f"[red]Project not found: {project_id}[/]")
        raise typer.Exit(1)

    if not force:
        console.print(f"\n[bold]Remove project?[/]")
        console.print(f"  {project.name} ({project.path})")
        confirm = typer.confirm("Are you sure?", default=False)
        if not confirm:
            raise typer.Exit(0)

    registry.remove_project(project_id)
    console.print(f"[green]✓ Project removed: {project_id}[/]\n")
