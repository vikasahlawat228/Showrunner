"""antigravity genre - genre preset management commands."""

from __future__ import annotations

from typing import Optional

import typer
import yaml

from antigravity_tool.core.genre_presets import get_preset, list_presets, get_preset_ids
from antigravity_tool.core.project import Project
from antigravity_tool.core.template_engine import TemplateEngine
from antigravity_tool.utils.display import (
    console, create_table, print_success, print_info, print_error, print_prompt_output,
)
from antigravity_tool.utils.io import read_yaml, write_yaml

app = typer.Typer(help="Genre preset management.")


@app.command("list")
def list_genres() -> None:
    """List all available genre presets."""
    presets = list_presets()
    table = create_table("Genre Presets", [
        ("Genre ID", ""),
        ("Name", ""),
        ("Structure", ""),
        ("Description", ""),
    ])
    for p in presets:
        table.add_row(p.genre_id, p.display_name, p.suggested_structure, p.description[:60] + "...")
    console.print(table)


@app.command("show")
def show_genre(
    genre_id: str = typer.Argument(..., help="Genre preset ID"),
) -> None:
    """Display detailed genre preset configuration."""
    preset = get_preset(genre_id)
    if not preset:
        print_error(f"Unknown genre: {genre_id}. Use 'antigravity genre list' to see options.")
        raise typer.Exit(1)

    console.print(f"\n[bold]{preset.display_name}[/] ({preset.genre_id})")
    console.print(f"[dim]{preset.description}[/]\n")
    console.print(f"[bold]Suggested structure:[/] {preset.suggested_structure}\n")

    # Narrative defaults
    console.print("[bold]Narrative Defaults:[/]")
    for key, val in preset.narrative_defaults.items():
        if isinstance(val, list):
            console.print(f"  {key}: {', '.join(val)}")
        else:
            console.print(f"  {key}: {val}")

    console.print()

    # Visual defaults
    console.print("[bold]Visual Defaults:[/]")
    for key, val in preset.visual_defaults.items():
        if isinstance(val, list):
            console.print(f"  {key}: {', '.join(val)}")
        else:
            console.print(f"  {key}: {val}")

    console.print()

    # Tropes
    if preset.common_tropes:
        console.print("[bold]Common Tropes:[/]")
        for t in preset.common_tropes:
            console.print(f"  - {t}")
        console.print()

    if preset.anti_tropes:
        console.print("[bold]Anti-Tropes (avoid):[/]")
        for t in preset.anti_tropes:
            console.print(f"  - {t}")
        console.print()

    # Reference works
    if preset.reference_works:
        console.print(f"[bold]Reference works:[/] {', '.join(preset.reference_works)}")
        console.print()

    # Panel style hints
    if preset.panel_style_hints:
        console.print("[bold]Panel Style Hints:[/]")
        for mood, hint in preset.panel_style_hints.items():
            console.print(f"  {mood}: {hint}")
        console.print()


@app.command("apply")
def apply_genre(
    genre_id: str = typer.Argument(..., help="Genre preset ID to apply"),
) -> None:
    """Apply a genre preset to the current project's style guides."""
    preset = get_preset(genre_id)
    if not preset:
        print_error(f"Unknown genre: {genre_id}. Use 'antigravity genre list' to see options.")
        raise typer.Exit(1)

    project = Project.find()

    # Update visual style guide
    visual_path = project.path / "style_guide" / "visual.yaml"
    visual_data = read_yaml(visual_path)
    visual_data.update(preset.visual_defaults)
    visual_data["genre_preset"] = genre_id
    visual_data["genre_tags"] = [genre_id, preset.display_name.lower()]
    if preset.mood_lighting_overrides:
        existing_moods = visual_data.get("mood_lighting_presets", {})
        existing_moods.update(preset.mood_lighting_overrides)
        visual_data["mood_lighting_presets"] = existing_moods
    write_yaml(visual_path, visual_data)

    # Update narrative style guide
    narrative_path = project.path / "style_guide" / "narrative.yaml"
    narrative_data = read_yaml(narrative_path)
    narrative_data.update(preset.narrative_defaults)
    narrative_data["genre_preset"] = genre_id
    narrative_data["genre_tags"] = [genre_id, preset.display_name.lower()]
    write_yaml(narrative_path, narrative_data)

    print_success(f"Applied genre preset '{preset.display_name}' to {project.name}")
    console.print(f"  [dim]Visual guide:[/] {visual_path}")
    console.print(f"  [dim]Narrative guide:[/] {narrative_path}")
    console.print(f"\n[dim]Suggested story structure: {preset.suggested_structure}[/]")


@app.command("customize")
def customize_genre(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save prompt to file"),
) -> None:
    """Generate a prompt to customize the current genre preset."""
    project = Project.find()
    engine = TemplateEngine(project.user_prompts_dir)

    visual_data = read_yaml(project.path / "style_guide" / "visual.yaml")
    narrative_data = read_yaml(project.path / "style_guide" / "narrative.yaml")

    genre_id = visual_data.get("genre_preset", "") or narrative_data.get("genre_preset", "")
    preset = get_preset(genre_id) if genre_id else None

    ctx = {
        "project_name": project.name,
        "genre_preset": preset.model_dump() if preset else None,
        "genre_id": genre_id,
        "current_visual": visual_data,
        "current_narrative": narrative_data,
    }

    prompt = engine.render("genre/customize_preset.md.j2", **ctx)

    if output:
        with open(output, "w") as f:
            f.write(prompt)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(prompt, "Customize Genre Preset")
