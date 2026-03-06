"""CASCADE command — sync related entities when a scene changes.

Usage:
    showrunner cascade update <scene_file_or_id>  # Apply cascade updates
    showrunner cascade config <setting> <value>   # Configure cascade behavior
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from showrunner_tool.core.project import Project
from showrunner_tool.repositories.container_repo import ContainerRepository
from showrunner_tool.services.cascade_update_service import CascadeUpdateService
from showrunner_tool.services.knowledge_graph_service import KnowledgeGraphService
from showrunner_tool.services.agent_dispatcher import AgentDispatcher
from showrunner_tool.repositories.sqlite_indexer import SQLiteIndexer

console = Console()

app = typer.Typer(help="Cascade entity updates when scenes change.")


@app.command("update")
def cascade_update(
    scene_file: str = typer.Argument(..., help="Scene file path or ID (e.g., 'fragment/ch4-sc3.yaml')"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would change without writing"),
) -> None:
    """Analyze a scene and cascade updates to related entities.

    When you write a scene where a character develops, this command detects
    which characters/locations were affected and updates their YAML files.

    Examples:
        showrunner cascade update fragment/ch4-sc3.yaml
        showrunner cascade update fragment/ch4-sc3.yaml --dry-run
    """
    try:
        # Find project
        proj = Project.find(Path.cwd())
        console.print(f"[dim]Project: {proj.name}[/dim]")

        # Initialize services
        container_repo = ContainerRepository(proj.path)
        schema_repo = None  # Not needed for cascade updates

        # Initialize KG
        indexer = SQLiteIndexer(proj.path / "knowledge_graph.db")
        chroma_indexer = None
        try:
            from showrunner_tool.repositories.chroma_indexer import ChromaIndexer
            chroma_dir = proj.path / ".chroma"
            chroma_indexer = ChromaIndexer(persist_dir=chroma_dir)
        except Exception:
            pass

        kg_service = KnowledgeGraphService(
            container_repo, schema_repo, indexer, chroma_indexer=chroma_indexer
        )

        # Initialize agent dispatcher
        skills_dir = Path(__file__).resolve().parent.parent.parent.parent / "agents" / "skills"
        agent_dispatcher = AgentDispatcher(skills_dir)

        # Create cascade service
        cascade_service = CascadeUpdateService(
            kg_service=kg_service,
            container_repo=container_repo,
            agent_dispatcher=agent_dispatcher,
        )

        # Resolve file path
        scene_path: Path
        if "/" in scene_file or "\\" in scene_file:
            # It's a file path
            scene_path = proj.path / scene_file
            if not scene_path.exists():
                console.print(f"[red]✗ File not found: {scene_file}[/red]")
                raise typer.Exit(1)
        else:
            # Try to find by ID
            containers = kg_service.find_containers(filters={"id": scene_file})
            if containers:
                entity = containers[0]
                # Find the file path
                file_path = container_repo.get_path_for_id(scene_file)
                if file_path:
                    scene_path = proj.path / file_path
                else:
                    console.print(f"[red]✗ Could not find file for ID: {scene_file}[/red]")
                    raise typer.Exit(1)
            else:
                console.print(f"[red]✗ Not found: {scene_file}[/red]")
                raise typer.Exit(1)

        # Run cascade update
        console.print(f"\n[cyan]Analyzing {scene_path.relative_to(proj.path)}...[/cyan]")

        result = asyncio.run(cascade_service.analyze_and_update(scene_path, dry_run=dry_run))

        # Display results
        if result["status"] == "error":
            console.print(f"\n[red]✗ Error: {', '.join(result['errors'])}")
            raise typer.Exit(1)

        if not result["changed_files"] and not result["updates"]:
            console.print("\n[dim]No entity updates detected.[/dim]")
            return

        # Show updates in a table
        table = Table(title="Cascade Updates" + (" (DRY RUN - not written)" if dry_run else ""))
        table.add_column("Entity", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Changes", style="green")

        for entity_id, changes in result["updates"].items():
            # Find entity name
            entity_containers = kg_service.find_containers(filters={"id": entity_id})
            if entity_containers:
                entity_name = entity_containers[0].get("name", entity_id)
                entity_type = entity_containers[0].get("container_type", "unknown")

                # Format changes
                change_lines = []
                for key, value in changes.items():
                    if isinstance(value, dict):
                        if "old_emotional_state" in value:
                            change_lines.append(
                                f"emotional_state: {value.get('old_emotional_state')} → "
                                f"{value.get('new_emotional_state')}"
                            )
                        if "old_location" in value:
                            change_lines.append(
                                f"location: {value.get('old_location')} → "
                                f"{value.get('new_location')}"
                            )
                        if "relationship_changes" in value:
                            for other, rel in value["relationship_changes"].items():
                                change_lines.append(f"relationship[{other}]: {rel}")
                    else:
                        change_lines.append(f"{key}: {value}")

                table.add_row(
                    entity_name,
                    entity_type,
                    "\n".join(change_lines),
                )

        console.print(f"\n{table}")

        if dry_run:
            console.print("\n[yellow]ℹ DRY RUN: No files were modified. Run without --dry-run to apply changes.[/yellow]")
        else:
            console.print(f"\n[green]✓ Updated {len(result['changed_files'])} file(s).[/green]")
            for file_path in result["changed_files"]:
                console.print(f"  • {file_path}")

        # Clean up
        indexer.close()

    except Exception as e:
        console.print(f"[red]✗ Cascade update failed: {e}[/red]")
        if not isinstance(e, typer.Exit):
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@app.command("config")
def cascade_config(
    setting: str = typer.Argument(..., help="Setting name (e.g., 'auto_enable')"),
    value: str = typer.Argument(..., help="Value (e.g., 'true' or 'false')"),
) -> None:
    """Configure cascade update behavior.

    Examples:
        showrunner cascade config auto_enable true   # Auto-update on file changes
        showrunner cascade config auto_enable false  # Manual updates only
    """
    try:
        proj = Project.find(Path.cwd())

        # Read/write config (stored in .showrunner/config.yaml)
        config_path = proj.path / ".showrunner" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        import yaml
        config = {}
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}

        # Ensure cascade section exists
        if "cascade" not in config:
            config["cascade"] = {}

        # Set the value
        if value.lower() in ("true", "yes", "1"):
            config["cascade"][setting] = True
        elif value.lower() in ("false", "no", "0"):
            config["cascade"][setting] = False
        else:
            config["cascade"][setting] = value

        # Write back
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        console.print(f"[green]✓ Set cascade.{setting} = {value}[/green]")

    except Exception as e:
        console.print(f"[red]✗ Config update failed: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
