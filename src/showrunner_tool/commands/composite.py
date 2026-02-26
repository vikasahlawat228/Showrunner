"""showrunner composite - panel compositing commands (speech bubbles, SFX)."""

from __future__ import annotations

from typing import Optional

import typer

from showrunner_tool.core.project import Project
from showrunner_tool.utils.display import (
    console, print_success, print_info, print_error,
)

app = typer.Typer(help="Panel compositing (speech bubbles, SFX overlays).")


@app.command("panel")
def composite_panel(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    page: int = typer.Option(..., "--page", "-p", help="Page number"),
    panel_num: int = typer.Option(..., "--panel", help="Panel number"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output path"),
) -> None:
    """Composite a single panel with speech bubbles and SFX."""
    from showrunner_tool.core.compositor import PanelCompositor, _check_pillow

    if not _check_pillow():
        print_error("Pillow is required. Install with: pip install Pillow>=10.0.0")
        raise typer.Exit(1)

    project = Project.find()
    compositor = PanelCompositor(project)

    from pathlib import Path
    output_path = Path(output) if output else None

    result = compositor.composite_panel(chapter, page, panel_num, output_path=output_path)

    if result:
        print_success(f"Composited: {result}")
    else:
        print_error(f"Failed to composite Page {page}, Panel {panel_num}. Check that the source image exists.")


@app.command("chapter")
def composite_chapter(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
) -> None:
    """Composite all panels in a chapter."""
    from showrunner_tool.core.compositor import PanelCompositor, _check_pillow

    if not _check_pillow():
        print_error("Pillow is required. Install with: pip install Pillow>=10.0.0")
        raise typer.Exit(1)

    project = Project.find()
    compositor = PanelCompositor(project)

    results = compositor.composite_chapter(chapter)

    if results:
        print_success(f"Composited {len(results)} panels for chapter {chapter}")
        for r in results:
            console.print(f"  [dim]{r}[/]")
    else:
        print_info(f"No panels to composite in chapter {chapter}.")


@app.command("preview")
def preview_panel(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    page: int = typer.Option(..., "--page", "-p", help="Page number"),
    panel_num: int = typer.Option(..., "--panel", help="Panel number"),
) -> None:
    """Show a preview of what will be composited on a panel."""
    project = Project.find()
    panels = project.load_panels(chapter)

    target = next(
        (p for p in panels if p.page_number == page and p.panel_number == panel_num),
        None,
    )

    if not target:
        print_error(f"Panel not found: Page {page}, Panel {panel_num}")
        raise typer.Exit(1)

    console.print(f"\n[bold]Composite Preview: Ch.{chapter} P.{page} Panel {panel_num}[/]\n")

    # Check source image
    images_dir = project.chapters_dir / f"chapter-{chapter:02d}" / "images"
    filename = f"page-{page:02d}-panel-{panel_num:02d}.png"
    source = images_dir / filename
    exists = "[green]exists[/]" if source.exists() else "[red]missing[/]"
    console.print(f"  Source image: {filename} ({exists})")

    # Speech bubbles
    if target.dialogue_bubbles:
        console.print(f"\n  [bold]Speech Bubbles ({len(target.dialogue_bubbles)}):[/]")
        for bubble in target.dialogue_bubbles:
            console.print(f"    [{bubble.bubble_type}] {bubble.character_name}: \"{bubble.text}\"")
            console.print(f"    [dim]Position: {bubble.position_hint}[/]")
    else:
        console.print("\n  [dim]No speech bubbles[/]")

    # SFX
    if target.sound_effects:
        console.print(f"\n  [bold]Sound Effects ({len(target.sound_effects)}):[/]")
        for sfx in target.sound_effects:
            console.print(f"    [red]{sfx.upper()}[/]")
    else:
        console.print("  [dim]No sound effects[/]")

    # Narration
    if target.narration_box:
        console.print(f"\n  [bold]Narration:[/]")
        console.print(f"    [italic]{target.narration_box}[/]")
    else:
        console.print("  [dim]No narration box[/]")

    console.print()
