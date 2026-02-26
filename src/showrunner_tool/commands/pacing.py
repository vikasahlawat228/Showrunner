"""showrunner pacing - pacing analysis and tension curve commands."""

from __future__ import annotations

from typing import Optional

import typer

from showrunner_tool.core.project import Project
from showrunner_tool.core.pacing import PacingAnalyzer
from showrunner_tool.core.tension_curve import TensionCurveRenderer
from showrunner_tool.core.template_engine import TemplateEngine
from showrunner_tool.utils.display import (
    console, create_table, print_success, print_info, print_prompt_output,
)

app = typer.Typer(help="Pacing analysis and tension visualization.")


@app.command("analyze")
def analyze(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Chapter number (omit for full story)"),
) -> None:
    """Analyze pacing metrics for a chapter or the full story."""
    project = Project.find()
    analyzer = PacingAnalyzer(project)

    if chapter:
        report = analyzer.analyze_chapter(chapter)
        scope = f"Chapter {chapter}"
    else:
        report = analyzer.analyze_story()
        scope = "Full Story"

    m = report.metrics
    console.print(f"\n[bold]Pacing Analysis: {scope}[/]\n")

    # Metrics table
    table = create_table("Metrics", [("Metric", "cyan"), ("Value", "")])
    table.add_row("Total scenes", str(m.total_scenes))
    table.add_row("Total panels", str(m.total_panels))
    table.add_row("Dialogue density", f"{m.dialogue_density:.0%}")
    table.add_row("Action density", f"{m.action_density:.0%}")
    table.add_row("Emotional density", f"{m.emotional_density:.0%}")
    table.add_row("Avg tension", f"{m.avg_tension:.1f}/10")
    table.add_row("Tension range", f"{m.min_tension}-{m.max_tension}")
    table.add_row("Tension variance", f"{m.tension_variance:.1f}")
    if m.avg_scene_panels > 0:
        table.add_row("Avg panels/scene", f"{m.avg_scene_panels:.1f}")
    console.print(table)

    # Scene type distribution
    if m.scene_type_distribution:
        console.print("\n[bold]Scene Type Distribution:[/]")
        for stype, count in sorted(m.scene_type_distribution.items(), key=lambda x: -x[1]):
            bar = "█" * count
            console.print(f"  {stype:<20} {bar} ({count})")

    # Tension sparkline
    if m.tension_progression:
        renderer = TensionCurveRenderer(project)
        sparkline = renderer.render_sparkline(chapter)
        console.print(f"\n[bold]Tension:[/] {sparkline}")

    # Issues
    if report.issues:
        console.print(f"\n[bold yellow]Issues ({len(report.issues)}):[/]")
        for issue in report.issues:
            console.print(f"  [yellow]●[/] {issue.description}")
            console.print(f"    [green]{issue.suggestion}[/]")

    # Recommendations
    if report.recommendations:
        console.print(f"\n[bold]Recommendations:[/]")
        for rec in report.recommendations:
            console.print(f"  → {rec}")

    console.print()


@app.command("report")
def report(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Chapter number"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a pacing evaluation prompt for AI-assisted review."""
    project = Project.find()
    engine = TemplateEngine(project.user_prompts_dir)
    analyzer = PacingAnalyzer(project)

    if chapter:
        pacing_report = analyzer.analyze_chapter(chapter)
    else:
        pacing_report = analyzer.analyze_story()

    ctx = {
        "project_name": project.name,
        "chapter_num": chapter,
        "metrics": pacing_report.metrics.model_dump(mode="json"),
        "issues": [i.model_dump(mode="json") for i in pacing_report.issues],
        "recommendations": pacing_report.recommendations,
    }

    prompt = engine.render("evaluate/evaluate_pacing.md.j2", **ctx)

    if output:
        with open(output, "w") as f:
            f.write(prompt)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(prompt, "Pacing Report")


@app.command("suggest")
def suggest(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
) -> None:
    """Get specific suggestions to improve pacing in a chapter."""
    project = Project.find()
    analyzer = PacingAnalyzer(project)

    report = analyzer.analyze_chapter(chapter)

    console.print(f"\n[bold]Pacing Suggestions: Chapter {chapter}[/]\n")

    if not report.issues and not report.recommendations:
        print_success("Pacing looks good! No specific suggestions.")
        return

    for i, issue in enumerate(report.issues, 1):
        console.print(f"  {i}. [yellow]{issue.issue_type}[/]: {issue.description}")
        console.print(f"     [green]Fix: {issue.suggestion}[/]")
        console.print()

    if report.recommendations:
        console.print("[bold]General recommendations:[/]")
        for rec in report.recommendations:
            console.print(f"  → {rec}")

    console.print()


@app.command("curve")
def curve(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Chapter (omit for full story)"),
    beats: bool = typer.Option(False, "--beats", "-b", help="Overlay story beats"),
    compact: bool = typer.Option(False, "--compact", help="Show compact sparkline only"),
) -> None:
    """Display tension curve visualization."""
    project = Project.find()
    renderer = TensionCurveRenderer(project)

    if compact:
        sparkline = renderer.render_sparkline(chapter)
        scope = f"Ch.{chapter}" if chapter else "Story"
        console.print(f"[bold]Tension ({scope}):[/] {sparkline}")
        return

    if beats:
        output = renderer.overlay_beats(chapter)
    else:
        output = renderer.render_ascii(chapter)

    console.print(f"\n{output}\n")
