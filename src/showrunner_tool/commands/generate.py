"""showrunner generate - batch image generation commands."""

from __future__ import annotations

from typing import Optional

import typer

from showrunner_tool.core.project import Project
from showrunner_tool.agent.image_provider import ImageProviderType, get_provider, list_providers
from showrunner_tool.core.batch_generator import BatchGenerator
from showrunner_tool.utils.display import (
    console, create_table, print_success, print_info, print_error,
)

app = typer.Typer(help="Batch image generation commands.")


def _get_provider_from_project(project: Project, provider_override: Optional[str] = None):
    """Get the configured image provider for the project."""
    style = project.load_visual_style_guide()
    provider_name = provider_override or (
        getattr(style, "image_provider", "gemini") if style else "gemini"
    )
    try:
        provider_type = ImageProviderType(provider_name)
    except ValueError:
        provider_type = ImageProviderType.GEMINI
    return get_provider(provider_type)


@app.command("chapter")
def generate_chapter(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be generated without generating"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Image provider override"),
    skip_existing: bool = typer.Option(True, "--skip-existing/--regenerate", help="Skip panels with existing images"),
) -> None:
    """Generate images for all panels in a chapter."""
    project = Project.find()
    img_provider = _get_provider_from_project(project, provider)

    if not dry_run and not img_provider.is_available():
        print_error(f"Provider '{img_provider.provider_type.value}' is not available. Check API keys.")
        raise typer.Exit(1)

    gen = BatchGenerator(project, img_provider)

    if dry_run:
        console.print(f"\n[bold]Dry run: Chapter {chapter}[/]\n")

    result = gen.generate_chapter(chapter, dry_run=dry_run, skip_existing=skip_existing)

    if dry_run:
        console.print(f"[dim]Total panels: {result.total_panels}[/]")
        console.print(f"[dim]Would generate: {result.total_panels - result.skipped}[/]")
        console.print(f"[dim]Would skip (existing): {result.skipped}[/]")
        if result.results:
            console.print("\n[bold]Prompts that would be sent:[/]\n")
            for i, r in enumerate(result.results[:5]):
                console.print(f"  [cyan]Panel {i+1}:[/] {r.prompt_used[:100]}...")
            if len(result.results) > 5:
                console.print(f"  [dim]... and {len(result.results) - 5} more[/]")
    else:
        console.print(f"\n[bold]Batch Generation: Chapter {chapter}[/]\n")
        print_success(f"Generated: {result.generated}/{result.total_panels}")
        if result.failed:
            print_error(f"Failed: {result.failed}")
        if result.skipped:
            print_info(f"Skipped: {result.skipped}")


@app.command("panel")
def generate_panel(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    page: int = typer.Option(..., "--page", "-p", help="Page number"),
    panel_num: int = typer.Option(..., "--panel", help="Panel number"),
    provider: Optional[str] = typer.Option(None, "--provider", help="Image provider override"),
) -> None:
    """Generate a single panel image."""
    project = Project.find()
    img_provider = _get_provider_from_project(project, provider)

    if not img_provider.is_available():
        print_error(f"Provider '{img_provider.provider_type.value}' is not available.")
        raise typer.Exit(1)

    gen = BatchGenerator(project, img_provider)
    result = gen.generate_single(chapter, page, panel_num)

    if result.status == "success":
        print_success(f"Generated: {result.image_path}")
    else:
        print_error(f"Failed: {result.error_message}")


@app.command("status")
def generation_status(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
) -> None:
    """Show image generation status for a chapter."""
    project = Project.find()
    img_provider = _get_provider_from_project(project)
    gen = BatchGenerator(project, img_provider)

    status = gen.get_status(chapter)

    console.print(f"\n[bold]Generation Status: Chapter {chapter}[/]\n")

    pct = status["completion_pct"]
    bar_filled = int(pct / 5)
    bar = "█" * bar_filled + "░" * (20 - bar_filled)
    console.print(f"  Progress: [{bar}] {pct:.0f}%")
    console.print(f"  Total panels: {status['total_panels']}")
    console.print(f"  Generated: [green]{status['images_generated']}[/]")
    console.print(f"  Missing: [yellow]{status['images_missing']}[/]")

    if status["missing_panels"]:
        console.print("\n  [dim]Missing panels:[/]")
        for p in status["missing_panels"][:10]:
            console.print(f"    - {p}")
        if len(status["missing_panels"]) > 10:
            console.print(f"    [dim]... and {len(status['missing_panels']) - 10} more[/]")


@app.command("providers")
def show_providers() -> None:
    """List available image generation providers and their status."""
    table = create_table("Image Providers", [
        ("Provider", "cyan"),
        ("Status", ""),
        ("API Key Env", "dim"),
    ])

    env_vars = {
        ImageProviderType.GEMINI: "GEMINI_API_KEY",
        ImageProviderType.DALLE: "OPENAI_API_KEY",
        ImageProviderType.STABLE_DIFFUSION: "(local API)",
        ImageProviderType.FLUX: "BFL_API_KEY",
    }

    for ptype in list_providers():
        try:
            provider = get_provider(ptype)
            available = provider.is_available()
            status = "[green]available[/]" if available else "[red]not configured[/]"
        except Exception:
            status = "[red]error[/]"

        table.add_row(
            ptype.value,
            status,
            env_vars.get(ptype, ""),
        )

    console.print(table)
