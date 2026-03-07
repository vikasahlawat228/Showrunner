"""showrunner backup — Create project backups and exports."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import typer

from showrunner_tool.core.project import Project
from showrunner_tool.services.export_service import ExportService
from showrunner_tool.utils.display import console, print_success, print_info

app = typer.Typer(help="Create and manage project backups.")


@app.command()
def backup(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path (default: story-backup-TIMESTAMP.zip)"),
    include_secrets: bool = typer.Option(False, "--include-secrets", help="Include creative_room data in backup"),
    include_git: bool = typer.Option(True, "--include-git/--no-git", help="Include git bundle in backup (default: yes)"),
) -> None:
    """Create a full project backup with YAML files and optional git history.

    Backups include:
      - All YAML files (characters, world, containers, fragments, etc.)
      - JSON export of all containers and event log
      - Optional git bundle of full repository history
      - Optional creative room secrets

    Backups are saved as .zip files and can be used for:
      - Regular automatic backups
      - Before major revisions
      - Disaster recovery
      - Sharing with collaborators
    """
    project = Project.find()
    svc = ExportService(project)

    # Determine output filename
    if output is None:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output = project.path / f"story-backup-{timestamp}.zip"
    else:
        output = Path(output).absolute()

    console.print()
    print_info(f"Creating backup...")
    print_info(f"  Project: {project.name}")
    print_info(f"  Output: {output}")
    if include_secrets:
        print_info(f"  Including: creative room secrets")
    if include_git:
        print_info(f"  Including: git history bundle")

    try:
        # Create the backup
        result = svc.create_full_backup(
            output_path=output,
            include_git_bundle=include_git,
            include_secrets=include_secrets,
        )

        console.print()
        print_success(f"✓ Backup created successfully")
        print_success(f"  File size: {result.get('file_size', 'unknown')} bytes")
        print_success(f"  Location: {output}")
        console.print()
        print_info(f"Recovery: showrunner restore <backup-file.zip>")

    except Exception as e:
        console.print(f"[red]✗ Backup failed: {e}[/]")
        raise typer.Exit(1)


@app.command()
def list_backups() -> None:
    """List existing backups in the project directory."""
    project = Project.find()
    backups = sorted(project.path.glob("story-backup-*.zip"), reverse=True)

    if not backups:
        print_info("No backups found.")
        return

    console.print()
    console.print(f"[bold]Backups ({len(backups)} found)[/]")
    console.print()

    for backup_file in backups:
        size_mb = backup_file.stat().st_size / (1024 * 1024)
        mtime = backup_file.stat().st_mtime
        import datetime
        date = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        console.print(f"  • {backup_file.name}")
        console.print(f"    Size: {size_mb:.2f} MB | Date: {date}")
    console.print()
