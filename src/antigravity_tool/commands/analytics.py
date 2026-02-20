"""antigravity analytics - project analytics dashboard commands."""

from __future__ import annotations

from typing import Optional

import json

import typer

from antigravity_tool.core.project import Project
from antigravity_tool.core.analytics import ProjectAnalytics
from antigravity_tool.utils.display import (
    console, create_table, print_success, print_info,
)
from antigravity_tool.utils.io import ensure_dir

app = typer.Typer(help="Project analytics and statistics.")


@app.command("dashboard")
def dashboard() -> None:
    """Display the full project analytics dashboard."""
    project = Project.find()
    analytics = ProjectAnalytics(project)
    report = analytics.compute()

    console.print(f"\n[bold]{'═' * 50}[/]")
    console.print(f"[bold]  {report.project_name} — Analytics Dashboard[/]")
    console.print(f"[bold]{'═' * 50}[/]\n")

    # Progress bar
    pct = report.completion_percentage
    bar_filled = int(pct / 5)
    bar = "█" * bar_filled + "░" * (20 - bar_filled)
    console.print(f"  Completion: [{bar}] {pct:.0f}%\n")

    # Overview
    table = create_table("Project Overview", [("Metric", "cyan"), ("Value", "")])
    table.add_row("Chapters", f"{report.chapters_complete}/{report.total_chapters}")
    table.add_row("Scenes", str(report.total_scenes))
    table.add_row("Panels", str(report.total_panels))
    table.add_row("Total words", f"{report.total_words:,}")
    table.add_row("Characters", str(report.character_count))
    table.add_row("Images generated", str(report.images_generated))
    table.add_row("Images composited", str(report.images_composited))
    table.add_row("Est. reading time", report.estimated_reading_time)
    console.print(table)

    # Scene type distribution
    if report.scene_type_distribution:
        console.print("\n[bold]Scene Types:[/]")
        for stype, count in sorted(report.scene_type_distribution.items(), key=lambda x: -x[1]):
            bar = "█" * count
            console.print(f"  {stype:<20} {bar} ({count})")

    console.print()


@app.command("characters")
def character_analytics() -> None:
    """Show character appearance and dialogue statistics."""
    project = Project.find()
    analytics = ProjectAnalytics(project)
    report = analytics.compute()

    if not report.character_stats:
        print_info("No character data available.")
        return

    table = create_table("Character Statistics", [
        ("Character", "cyan"),
        ("Role", "dim"),
        ("Scene App.", ""),
        ("Panel App.", ""),
        ("Dialogues", ""),
        ("Words", ""),
    ])

    for cs in report.character_stats:
        table.add_row(
            cs.name,
            cs.role,
            str(cs.scene_appearances),
            str(cs.panel_appearances),
            str(cs.dialogue_count),
            str(cs.total_words),
        )

    console.print(table)


@app.command("progress")
def progress() -> None:
    """Show detailed progress across all chapters."""
    project = Project.find()

    console.print(f"\n[bold]Progress: {project.name}[/]\n")

    if not project.chapters_dir.exists():
        print_info("No chapters found.")
        return

    table = create_table("Chapter Progress", [
        ("Chapter", "cyan"),
        ("Scenes", ""),
        ("Panels", ""),
        ("Images", ""),
        ("Composited", ""),
        ("Status", ""),
    ])

    for d in sorted(project.chapters_dir.iterdir()):
        if not d.is_dir() or not d.name.startswith("chapter-"):
            continue

        try:
            ch_num = int(d.name.split("-")[1])
        except (IndexError, ValueError):
            continue

        scenes = project.load_scenes(ch_num)
        panels = project.load_panels(ch_num)

        images_dir = d / "images"
        images = len(list(images_dir.glob("*.png"))) if images_dir.exists() else 0

        comp_dir = d / "composited"
        composited = len(list(comp_dir.glob("*.png"))) if comp_dir.exists() else 0

        # Status
        if composited > 0:
            status = "[green]composited[/]"
        elif images > 0:
            status = "[yellow]images ready[/]"
        elif len(panels) > 0:
            status = "[yellow]panels defined[/]"
        elif len(scenes) > 0:
            status = "[yellow]scenes written[/]"
        else:
            status = "[dim]planned[/]"

        table.add_row(
            f"Chapter {ch_num}",
            str(len(scenes)),
            str(len(panels)),
            str(images),
            str(composited),
            status,
        )

    console.print(table)


@app.command("export")
def export_analytics(
    format: str = typer.Option("json", "--format", "-f", help="Export format: json"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Export analytics data as JSON."""
    project = Project.find()
    analytics = ProjectAnalytics(project)
    report = analytics.compute()

    data = report.model_dump(mode="json")

    if output:
        from pathlib import Path
        out_path = Path(output)
        out_path.write_text(json.dumps(data, indent=2))
        print_success(f"Analytics exported to {out_path}")
    else:
        console.print_json(json.dumps(data, indent=2))
