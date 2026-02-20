"""antigravity check - continuity and DNA drift checking commands."""

from __future__ import annotations

from typing import Optional

import typer

from antigravity_tool.core.project import Project
from antigravity_tool.core.continuity import ContinuityChecker
from antigravity_tool.core.dna_checker import DNADriftChecker
from antigravity_tool.core.template_engine import TemplateEngine
from antigravity_tool.schemas.continuity import IssueSeverity
from antigravity_tool.utils.display import (
    console, create_table, print_success, print_info, print_error, print_prompt_output,
)

app = typer.Typer(help="Continuity checking and DNA drift detection.")


@app.command("continuity")
def check_continuity(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Chapter number (omit for all)"),
) -> None:
    """Run full continuity check on scenes and character states."""
    project = Project.find()
    checker = ContinuityChecker(project)

    scope = f"Chapter {chapter}" if chapter else "All chapters"
    console.print(f"\n[bold]Running continuity check: {scope}[/]\n")

    report = checker.full_check(chapter)

    if not report.issues:
        print_success(f"No continuity issues found! Checked {report.checked_scenes} scenes, {report.checked_characters} characters.")
        return

    # Display issues
    table = create_table(f"Continuity Report ({scope})", [
        ("Sev", ""),
        ("Category", "cyan"),
        ("Location", "dim"),
        ("Description", ""),
        ("Suggestion", "green"),
    ])

    severity_icons = {
        IssueSeverity.ERROR: "[red]ERR[/]",
        IssueSeverity.WARNING: "[yellow]WRN[/]",
        IssueSeverity.INFO: "[dim]INF[/]",
    }

    for issue in report.issues:
        table.add_row(
            severity_icons.get(issue.severity, "?"),
            issue.category.value.replace("_", " "),
            issue.location,
            issue.description,
            issue.suggestion,
        )

    console.print(table)
    console.print(
        f"\n[bold]Summary:[/] {report.error_count} errors, "
        f"{report.warning_count} warnings, {report.info_count} info"
    )
    console.print(
        f"[dim]Checked {report.checked_scenes} scenes, "
        f"{report.checked_characters} characters[/]"
    )


@app.command("scene-flow")
def check_scene_flow(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
) -> None:
    """Check scene flow continuity (time, tension, transitions)."""
    project = Project.find()
    checker = ContinuityChecker(project)

    scenes = project.load_scenes(chapter)
    if not scenes:
        print_info(f"No scenes found in chapter {chapter}.")
        return

    issues = checker.check_scene_flow(chapter, scenes)

    if not issues:
        print_success(f"Scene flow looks good in chapter {chapter}!")
        return

    for issue in issues:
        icon = "[yellow]WRN[/]" if issue.severity == IssueSeverity.WARNING else "[dim]INF[/]"
        console.print(f"  {icon} {issue.description}")
        console.print(f"      [green]{issue.suggestion}[/]")


@app.command("knowledge")
def check_knowledge(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
) -> None:
    """Check reader knowledge consistency."""
    project = Project.find()
    checker = ContinuityChecker(project)

    issues = checker.check_reader_knowledge(chapter)

    if not issues:
        print_success(f"Reader knowledge is consistent in chapter {chapter}!")
        return

    for issue in issues:
        console.print(f"  [dim]INF[/] {issue.description}")
        if issue.suggestion:
            console.print(f"      [green]{issue.suggestion}[/]")


@app.command("relationships")
def check_relationships() -> None:
    """Check relationship graph consistency against character files."""
    project = Project.find()
    checker = ContinuityChecker(project)

    issues = checker.check_relationship_consistency()

    if not issues:
        print_success("Relationship graph is consistent with all character files!")
        return

    for issue in issues:
        icon = "[red]ERR[/]" if issue.severity == IssueSeverity.ERROR else "[yellow]WRN[/]"
        console.print(f"  {icon} {issue.description}")
        console.print(f"      [green]{issue.suggestion}[/]")


@app.command("report")
def check_report(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Chapter number"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save prompt to file"),
) -> None:
    """Generate a continuity report prompt for AI-assisted review."""
    project = Project.find()
    engine = TemplateEngine(project.user_prompts_dir)

    checker = ContinuityChecker(project)
    report = checker.full_check(chapter)

    ctx = {
        "project_name": project.name,
        "chapter_num": chapter,
        "issues": [i.model_dump(mode="json") for i in report.issues],
        "checked_scenes": report.checked_scenes,
        "checked_characters": report.checked_characters,
        "error_count": report.error_count,
        "warning_count": report.warning_count,
    }

    prompt = engine.render("evaluate/check_continuity.md.j2", **ctx)

    if output:
        with open(output, "w") as f:
            f.write(prompt)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(prompt, "Continuity Report")


@app.command("dna")
def check_dna(
    name: Optional[str] = typer.Argument(None, help="Character name (omit for all)"),
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Limit to chapter"),
) -> None:
    """Check character DNA drift against image prompts."""
    project = Project.find()
    checker = DNADriftChecker(project)

    if name:
        report = checker.check_character(name, chapter)
        scope = f"{name}"
    else:
        report = checker.check_all(chapter)
        scope = "All characters"

    if not report.issues:
        print_success(f"No DNA drift detected for {scope}! ({report.panels_checked} panels checked)")
        return

    table = create_table(f"DNA Drift Report: {scope}", [
        ("Character", "cyan"),
        ("Panel", "dim"),
        ("Field", "magenta"),
        ("Canonical", "green"),
        ("In Prompt", "red"),
    ])

    for issue in report.issues:
        table.add_row(
            issue.character_name,
            issue.panel_location,
            issue.dna_field,
            issue.canonical_value,
            issue.prompt_value,
        )

    console.print(table)
    console.print(f"\n[bold]Total drift issues:[/] {report.drift_count}")


@app.command("dna-fix")
def check_dna_fix(
    name: str = typer.Argument(..., help="Character name"),
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Limit to chapter"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save prompt to file"),
) -> None:
    """Generate a correction prompt to fix DNA drift for a character."""
    project = Project.find()
    checker = DNADriftChecker(project)
    engine = TemplateEngine(project.user_prompts_dir)

    report = checker.check_character(name, chapter)

    if not report.issues:
        print_success(f"No DNA drift detected for {name}!")
        return

    char = project.load_character(name)
    ctx = {
        "character_name": name,
        "character_dna": char.dna.model_dump(mode="json") if char else {},
        "drift_issues": [i.model_dump(mode="json") for i in report.issues],
        "panels_checked": report.panels_checked,
    }

    prompt = engine.render("evaluate/check_dna_drift.md.j2", **ctx)

    if output:
        with open(output, "w") as f:
            f.write(prompt)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(prompt, f"DNA Drift Fix: {name}")
