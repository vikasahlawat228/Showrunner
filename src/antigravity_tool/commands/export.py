"""antigravity export - export commands for story bible, screenplays, prompts."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import yaml

from antigravity_tool.core.project import Project
from antigravity_tool.utils.io import ensure_dir
from antigravity_tool.utils.display import console, print_success, print_info

app = typer.Typer(help="Export project data in various formats.")


@app.command("bible")
def export_bible(
    output: str = typer.Option("exports/story_bible.md", "--output", "-o"),
) -> None:
    """Export a complete story bible (world, characters, structure)."""
    project = Project.find()
    lines = []

    lines.append(f"# {project.name} - Story Bible\n")

    # World
    ws = project.load_world_settings()
    if ws:
        lines.append("## World\n")
        lines.append(f"**Genre:** {ws.genre}")
        lines.append(f"**Time Period:** {ws.time_period}")
        lines.append(f"**Tone:** {ws.tone}")
        lines.append(f"\n{ws.description}\n")

        if ws.rules:
            lines.append("### World Rules\n")
            for rule in ws.rules:
                lines.append(f"- **{rule.name}** ({rule.category}): {rule.description}")
            lines.append("")

    # Characters
    characters = project.load_all_characters(filter_secrets=False)
    if characters:
        lines.append("## Characters\n")
        for char in characters:
            lines.append(f"### {char.name} ({char.role.value})")
            lines.append(f"\n{char.one_line}\n")
            if char.backstory:
                lines.append(f"**Backstory:** {char.backstory}\n")
            if char.personality.traits:
                lines.append(f"**Traits:** {', '.join(char.personality.traits)}")
            if char.personality.speech_pattern:
                lines.append(f"**Speech:** {char.personality.speech_pattern}")
            lines.append("")

    # Story Structure
    structure = project.load_story_structure()
    if structure:
        lines.append("## Story Structure\n")
        lines.append(f"**Type:** {structure.structure_type.value}")
        lines.append(f"**Logline:** {structure.logline}")
        lines.append(f"**Premise:** {structure.premise}\n")

        if structure.beats:
            lines.append("### Beats\n")
            for beat in structure.beats:
                lines.append(f"**{beat.beat_number}. {beat.beat_name}** ({beat.act}, {beat.target_percentage:.0%})")
                if beat.content:
                    lines.append(f"  {beat.content}")
            lines.append("")

    out_path = project.path / output
    ensure_dir(out_path.parent)
    out_path.write_text("\n".join(lines))
    print_success(f"Story bible exported to {out_path}")


@app.command("prompts")
def export_prompts(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    format: str = typer.Option("txt", "--format", "-f", help="Export format: txt, json"),
) -> None:
    """Export image prompts for a chapter."""
    # Delegate to the image_prompt export command
    from antigravity_tool.commands.image_prompt import export as prompt_export
    prompt_export(chapter=chapter, format=format)


@app.command("outline")
def export_outline(
    output: str = typer.Option("exports/outline.md", "--output", "-o"),
) -> None:
    """Export the story outline."""
    project = Project.find()
    structure = project.load_story_structure()
    if not structure:
        print_info("No story structure found.")
        return

    lines = [f"# {structure.title} - Story Outline\n"]
    lines.append(f"**Logline:** {structure.logline}\n")
    lines.append(f"**Structure:** {structure.structure_type.value}\n")

    current_act = ""
    for beat in structure.beats:
        if beat.act != current_act:
            current_act = beat.act
            lines.append(f"\n## {current_act}\n")
        lines.append(f"### {beat.beat_number}. {beat.beat_name} ({beat.target_percentage:.0%})")
        lines.append(f"{beat.content}\n")

    out_path = project.path / output
    ensure_dir(out_path.parent)
    out_path.write_text("\n".join(lines))
    print_success(f"Outline exported to {out_path}")


@app.command("webtoon")
def export_webtoon(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Custom output directory"),
) -> None:
    """Export a chapter as WEBTOON vertical scroll strips."""
    from antigravity_tool.core.exporters.webtoon import WebtoonExporter

    project = Project.find()
    exporter = WebtoonExporter(project)

    out_dir = Path(output_dir) if output_dir else None

    try:
        slices = exporter.export_chapter(chapter, output_dir=out_dir)
    except RuntimeError as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(1)

    if slices:
        print_success(f"Exported {len(slices)} WEBTOON slices for chapter {chapter}")
        console.print(f"  [dim]{slices[0].parent}[/]")
    else:
        print_info(f"No images found for chapter {chapter}.")


@app.command("pdf")
def export_pdf(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Chapter number (omit for all)"),
    layout: str = typer.Option("page_based", "--layout", "-l", help="Layout: vertical or page_based"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output path"),
) -> None:
    """Export as print-ready PDF."""
    from antigravity_tool.core.exporters.pdf import PDFExporter

    project = Project.find()
    exporter = PDFExporter(project)

    out_path = Path(output) if output else None

    try:
        if chapter:
            result = exporter.export_chapter(chapter, output_path=out_path, layout=layout)
        else:
            result = exporter.export_full(output_path=out_path, layout=layout)
    except RuntimeError as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(1)

    if result:
        print_success(f"PDF exported to {result}")
    else:
        print_info("No images found to export.")


@app.command("social")
def export_social(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    page: int = typer.Option(..., "--page", "-p", help="Page number"),
    panel_num: int = typer.Option(..., "--panel", help="Panel number"),
    format_name: str = typer.Option("instagram_square", "--format", "-f", help="Format: instagram_square, instagram_portrait, twitter, tiktok"),
    watermark: Optional[str] = typer.Option(None, "--watermark", "-w", help="Watermark text"),
) -> None:
    """Export a single panel for social media."""
    from antigravity_tool.core.exporters.social import SocialExporter

    project = Project.find()
    exporter = SocialExporter(project)

    try:
        result = exporter.export_panel(
            chapter, page, panel_num,
            format_name=format_name,
            watermark_text=watermark,
        )
    except RuntimeError as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(1)

    if result:
        print_success(f"Social export saved to {result}")
    else:
        print_info("Panel image not found.")


@app.command("social-batch")
def export_social_batch(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    format_name: str = typer.Option("instagram_square", "--format", "-f", help="Format: instagram_square, instagram_portrait, twitter, tiktok"),
    watermark: Optional[str] = typer.Option(None, "--watermark", "-w", help="Watermark text"),
) -> None:
    """Export all panels in a chapter for social media."""
    from antigravity_tool.core.exporters.social import SocialExporter

    project = Project.find()
    exporter = SocialExporter(project)

    try:
        results = exporter.export_chapter_batch(
            chapter,
            format_name=format_name,
            watermark_text=watermark,
        )
    except RuntimeError as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(1)

    if results:
        print_success(f"Exported {len(results)} panels for {format_name}")
        console.print(f"  [dim]{results[0].parent}[/]")
    else:
        print_info(f"No images found for chapter {chapter}.")


@app.command("reading-time")
def export_reading_time(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Chapter (omit for full story)"),
) -> None:
    """Estimate reading time for a chapter or the full story."""
    from antigravity_tool.core.reading_time import ReadingTimeEstimator

    project = Project.find()
    estimator = ReadingTimeEstimator(project)

    if chapter:
        data = estimator.estimate_chapter(chapter)
        console.print(f"\n[bold]Reading Time: Chapter {chapter}[/]\n")
        console.print(f"  Panels: {data['panel_count']}")
        console.print(f"  Estimated time: [cyan]{data['formatted']}[/]")
    else:
        data = estimator.estimate_story()
        console.print(f"\n[bold]Reading Time: Full Story[/]\n")
        console.print(f"  Chapters: {data['chapter_count']}")
        console.print(f"  Total panels: {data['total_panels']}")
        console.print(f"  Estimated time: [cyan]{data['formatted']}[/]")

        if data.get("chapters"):
            console.print("\n  [dim]Per chapter:[/]")
            for ch in data["chapters"]:
                console.print(f"    Ch.{ch['chapter_num']}: {ch['formatted']} ({ch['panel_count']} panels)")

    console.print()
