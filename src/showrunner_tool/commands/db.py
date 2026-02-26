"""showrunner db — database maintenance commands (Phase K-5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from showrunner_tool.core.project import Project
from showrunner_tool.repositories.sqlite_indexer import SQLiteIndexer
from showrunner_tool.schemas.dal import ConsistencyIssue, DBHealthReport
from showrunner_tool.utils.display import (
    console,
    create_table,
    print_error,
    print_info,
    print_success,
)

app = typer.Typer(help="Database maintenance and diagnostics.")


@app.command("stats")
def db_stats() -> None:
    """Show entity counts, cache stats, and index health."""
    project = Project.find()
    indexer = SQLiteIndexer(project.path / "knowledge_graph.db")

    counts = indexer.get_entity_count_by_type()
    total_indexed = sum(counts.values())

    # Count YAML files on disk
    yaml_count = sum(1 for _ in project.path.rglob("*.yaml") if not _.name.startswith("_"))

    console.print("\n[bold]Database Statistics[/]\n")

    table = create_table("Entity Index", "Type", "Count")
    for etype, count in sorted(counts.items()):
        table.add_row(etype, str(count))
    table.add_row("[bold]Total[/]", f"[bold]{total_indexed}[/]")
    console.print(table)

    console.print(f"\n  YAML files on disk: {yaml_count}")
    console.print(f"  Indexed entities:   {total_indexed}")

    # Check sync_metadata
    sync_rows = indexer.get_sync_metadata()
    console.print(f"  Sync metadata rows: {len(sync_rows)}")

    indexer.close()
    print_success("Stats complete")


@app.command("check")
def db_check() -> None:
    """Run YAML <-> SQLite consistency check and report issues."""
    project = Project.find()
    indexer = SQLiteIndexer(project.path / "knowledge_graph.db")

    issues = _find_consistency_issues(project.path, indexer)

    if not issues:
        print_success("No consistency issues found")
        indexer.close()
        return

    table = create_table("Consistency Issues", "Type", "Path/ID", "Description", "Fixable")
    for issue in issues:
        table.add_row(
            issue.issue_type,
            issue.yaml_path or issue.entity_id or "",
            issue.description,
            "Yes" if issue.auto_fixable else "No",
        )
    console.print(table)
    console.print(f"\n[yellow]Found {len(issues)} issue(s)[/]")

    indexer.close()


@app.command("reindex")
def db_reindex(
    force: bool = typer.Option(False, "--force", "-f", help="Drop and rebuild all indexes"),
) -> None:
    """Rebuild the SQLite entity index from YAML files."""
    project = Project.find()
    indexer = SQLiteIndexer(project.path / "knowledge_graph.db")

    if force:
        # Drop all entity rows and rebuild
        with indexer._conn:
            indexer._conn.execute("DELETE FROM entities")
            indexer._conn.execute("DELETE FROM sync_metadata")
        print_info("Cleared all entity indexes")

    # Re-sync from containers (legacy path)
    from showrunner_tool.repositories.container_repo import ContainerRepository
    from showrunner_tool.services.knowledge_graph_service import KnowledgeGraphService

    container_repo = ContainerRepository(project.path)
    schema_repo_path = project.path / "schemas"
    from showrunner_tool.repositories.container_repo import SchemaRepository
    schema_repo = SchemaRepository(schema_repo_path)

    kg_service = KnowledgeGraphService(container_repo, schema_repo, indexer)
    kg_service.sync_all(project.path)

    # Now migrate containers to entities table
    migrated = indexer.migrate_containers_to_entities()
    counts = indexer.get_entity_count_by_type()

    print_success(f"Reindex complete: {migrated} entities migrated, {sum(counts.values())} total indexed")
    indexer.close()


@app.command("compact")
def db_compact(
    days: int = typer.Option(30, "--days", "-d", help="Remove sync metadata older than N days"),
) -> None:
    """Prune orphaned indexes and old sync metadata."""
    project = Project.find()
    indexer = SQLiteIndexer(project.path / "knowledge_graph.db")

    # Find and remove orphaned entity entries (no YAML file on disk)
    issues = _find_consistency_issues(project.path, indexer)
    orphans = [i for i in issues if i.issue_type == "orphaned_index" and i.entity_id]

    removed = 0
    for orphan in orphans:
        if orphan.entity_id:
            indexer.delete_entity(orphan.entity_id)
            removed += 1
        if orphan.yaml_path:
            indexer.delete_sync_metadata(orphan.yaml_path)

    if removed:
        print_info(f"Removed {removed} orphaned index entries")
    else:
        print_info("No orphaned entries found")

    indexer.close()
    print_success("Compact complete")


# ── Internal helpers ──────────────────────────────────────────────


def _find_consistency_issues(
    project_path: Path, indexer: SQLiteIndexer
) -> list[ConsistencyIssue]:
    """Check YAML <-> SQLite consistency and return issues."""
    issues: list[ConsistencyIssue] = []

    # Check all entity rows — do their YAML files still exist?
    all_entities = indexer.query_entities()
    for entity in all_entities:
        yaml_path = entity.get("yaml_path", "")
        if yaml_path and not Path(yaml_path).exists():
            issues.append(ConsistencyIssue(
                issue_type="orphaned_index",
                yaml_path=yaml_path,
                entity_id=entity.get("id"),
                entity_type=entity.get("entity_type"),
                description=f"Entity indexed but YAML file missing: {yaml_path}",
                auto_fixable=True,
            ))

    # Check sync_metadata — do referenced files exist?
    sync_rows = indexer.get_sync_metadata()
    for row in sync_rows:
        if not Path(row["yaml_path"]).exists():
            issues.append(ConsistencyIssue(
                issue_type="stale_file",
                yaml_path=row["yaml_path"],
                entity_id=row.get("entity_id"),
                entity_type=row.get("entity_type"),
                description=f"Sync metadata references missing file: {row['yaml_path']}",
                auto_fixable=True,
            ))

    return issues
