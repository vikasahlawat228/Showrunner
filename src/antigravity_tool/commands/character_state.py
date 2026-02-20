"""antigravity character-state - per-scene character state tracking."""

from __future__ import annotations

from typing import Optional

import typer
import yaml

from antigravity_tool.core.project import Project
from antigravity_tool.core.template_engine import TemplateEngine
from antigravity_tool.utils.display import (
    console, create_table, print_info, print_error, print_prompt_output,
)
from antigravity_tool.utils.io import read_yaml

app = typer.Typer(help="Per-scene character state tracking.")


@app.command("show")
def show_state(
    name: str = typer.Argument(..., help="Character name"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    scene: int = typer.Option(..., "--scene", "-s", help="Scene number"),
) -> None:
    """Show a character's state snapshot at a specific scene."""
    project = Project.find()
    chapter_dir = project.path / "chapters" / f"chapter-{chapter:02d}"
    states_dir = chapter_dir / "character_states"

    if not states_dir.exists():
        print_info("No character states found. Use 'character-state extract' after writing scenes.")
        return

    state_file = states_dir / f"scene-{scene:02d}-{name.lower().replace(' ', '_')}.yaml"
    if not state_file.exists():
        print_info(f"No state for '{name}' at Chapter {chapter}, Scene {scene}.")
        return

    data = read_yaml(state_file)
    console.print(f"\n[bold]{name}[/] — Chapter {chapter}, Scene {scene}\n")

    for key, val in data.items():
        if isinstance(val, list) and val:
            console.print(f"  [bold]{key}:[/] {', '.join(str(v) for v in val)}")
        elif val and val != "default":
            console.print(f"  [bold]{key}:[/] {val}")
    console.print()


@app.command("timeline")
def timeline(
    name: str = typer.Argument(..., help="Character name"),
) -> None:
    """Show a character's state evolution across all scenes."""
    project = Project.find()
    slug = name.lower().replace(" ", "_")

    table = create_table(f"{name} — State Timeline", [
        ("Location", ""),
        ("Emotional", ""),
        ("Physical", ""),
        ("Outfit", ""),
        ("Changes", ""),
    ])

    chapters_dir = project.path / "chapters"
    found = False
    for chapter_dir in sorted(chapters_dir.iterdir()):
        if not chapter_dir.is_dir() or not chapter_dir.name.startswith("chapter-"):
            continue
        states_dir = chapter_dir / "character_states"
        if not states_dir.exists():
            continue
        for state_file in sorted(states_dir.glob(f"scene-*-{slug}.yaml")):
            data = read_yaml(state_file)
            scene_label = state_file.stem.rsplit("-", 1)[0]
            ch_label = chapter_dir.name
            loc = f"{ch_label}/{scene_label}"
            changes = data.get("relationship_changes", []) + data.get("knowledge_gained", [])
            table.add_row(
                loc,
                data.get("emotional_state", ""),
                data.get("physical_state", ""),
                data.get("current_outfit", "default"),
                "; ".join(changes[:3]) if changes else "",
            )
            found = True

    if not found:
        print_info(f"No state data found for '{name}'. Use 'character-state extract' after writing scenes.")
        return

    console.print(table)


@app.command("extract")
def extract_state(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    scene: int = typer.Option(..., "--scene", "-s", help="Scene number"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a prompt to extract character states from a written scene."""
    project = Project.find()
    engine = TemplateEngine(project.user_prompts_dir)

    scene_file = (
        project.path / "chapters" / f"chapter-{chapter:02d}" / "scenes" / f"scene-{scene:02d}.yaml"
    )
    if not scene_file.exists():
        print_error(f"Scene not found: {scene_file}")
        raise typer.Exit(1)

    scene_data = read_yaml(scene_file)
    characters = project.load_all_characters(filter_secrets=True)
    char_map = {c.name.lower(): c.model_dump(mode="json") for c in characters}

    # Load previous scene end states if available
    prev_states = {}
    if scene > 1:
        prev_states_dir = project.path / "chapters" / f"chapter-{chapter:02d}" / "character_states"
        if prev_states_dir.exists():
            for name_key in scene_data.get("characters_present", []):
                slug = name_key.lower().replace(" ", "_")
                prev_file = prev_states_dir / f"scene-{(scene - 1):02d}-{slug}.yaml"
                if prev_file.exists():
                    prev_states[name_key] = read_yaml(prev_file)

    ctx = {
        "scene": scene_data,
        "chapter_num": chapter,
        "scene_num": scene,
        "characters": char_map,
        "previous_states": prev_states,
    }

    prompt = engine.render("character/extract_state.md.j2", **ctx)

    if output:
        with open(output, "w") as f:
            f.write(prompt)
    else:
        print_prompt_output(prompt, f"Extract Character States — Ch{chapter} Sc{scene}")
