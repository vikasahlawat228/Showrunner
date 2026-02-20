"""antigravity creative-room - author-only secret space commands."""

from __future__ import annotations

from typing import Optional

import typer
import yaml

from antigravity_tool.core.project import Project
from antigravity_tool.core.creative_room import CreativeRoomManager
from antigravity_tool.core.context_compiler import ContextCompiler
from antigravity_tool.core.template_engine import TemplateEngine
from antigravity_tool.core.extractors import KnowledgeExtractor
from antigravity_tool.schemas.creative_room import (
    PlotTwist, CharacterSecret, ForeshadowingEntry, TrueMechanic,
)
from antigravity_tool.utils.display import (
    console, print_success, print_info, print_warning,
    print_prompt_output, print_yaml, create_table,
)

app = typer.Typer(help="Author-only creative room (isolated from story prompts).")


@app.command("show")
def show() -> None:
    """Display all creative room contents."""
    project = Project.find()
    mgr = CreativeRoomManager(project)

    if not mgr.is_isolated():
        print_warning("Creative room isolation marker missing!")
        return

    console.print("\n[bold red]CREATIVE ROOM (SPOILERS)[/]\n")

    # Plot twists
    twists = mgr.list_plot_twists()
    if twists:
        console.print("[bold]Plot Twists:[/]")
        for t in twists:
            console.print(f"  - [cyan]{t.name}[/]: {t.description}")
        console.print()

    # Secrets
    secrets = mgr.list_character_secrets()
    if secrets:
        console.print("[bold]Character Secrets:[/]")
        for s in secrets:
            console.print(f"  - [cyan]{s.character_name}[/]: {s.secret}")
            if s.dramatic_irony_note:
                console.print(f"    [dim]Irony: {s.dramatic_irony_note}[/]")
        console.print()

    # Foreshadowing
    foreshadowing = mgr.list_foreshadowing()
    if foreshadowing:
        console.print("[bold]Foreshadowing Map:[/]")
        for f in foreshadowing:
            status_color = {"planted": "yellow", "growing": "green", "paid_off": "blue"}.get(f.status, "")
            console.print(f"  - [{status_color}]{f.status}[/] {f.plant_description} -> {f.payoff_description}")
        console.print()

    # Ending
    ending = mgr.get_ending_plans()
    if ending:
        console.print(f"[bold]Ending Plans:[/]\n  {ending}\n")

    if not any([twists, secrets, foreshadowing, ending]):
        print_info("Creative room is empty. Use add-twist, add-secret, etc. to populate.")


@app.command("add-twist")
def add_twist(
    name: str = typer.Argument(..., help="Twist name"),
    description: str = typer.Option("", "--desc", "-d", help="Twist description"),
) -> None:
    """Add a plot twist to the creative room."""
    project = Project.find()
    mgr = CreativeRoomManager(project)
    mgr.ensure_isolation_marker()

    from antigravity_tool.utils.ids import generate_id
    twist = PlotTwist(id=generate_id(), name=name, description=description)
    mgr.add_plot_twist(twist)
    print_success(f"Added plot twist: {name}")


@app.command("add-secret")
def add_secret(
    character: str = typer.Argument(..., help="Character name"),
    secret: str = typer.Option("", "--secret", "-s", help="The secret"),
    irony: str = typer.Option("", "--irony", "-i", help="Dramatic irony note"),
) -> None:
    """Add a character secret to the creative room."""
    project = Project.find()
    mgr = CreativeRoomManager(project)
    mgr.ensure_isolation_marker()

    char = project.load_character(character)
    cs = CharacterSecret(
        character_id=char.id if char else "",
        character_name=character,
        secret=secret,
        dramatic_irony_note=irony or None,
    )
    mgr.add_character_secret(cs)
    print_success(f"Added secret for {character}")


@app.command("add-foreshadowing")
def add_foreshadowing(
    plant: str = typer.Option(..., "--plant", "-p", help="The subtle hint"),
    payoff: str = typer.Option(..., "--payoff", help="What it pays off as"),
    plant_scene: str = typer.Option("", "--plant-scene", help="Scene ID where planted"),
    subtlety: str = typer.Option("moderate", "--subtlety", help="obvious/moderate/subtle/deeply_buried"),
) -> None:
    """Add a foreshadowing entry."""
    project = Project.find()
    mgr = CreativeRoomManager(project)
    mgr.ensure_isolation_marker()

    from antigravity_tool.utils.ids import generate_id
    entry = ForeshadowingEntry(
        id=generate_id(),
        plant_description=plant,
        payoff_description=payoff,
        plant_scene_id=plant_scene,
        subtlety_level=subtlety,
    )
    mgr.add_foreshadowing(entry)
    print_success("Added foreshadowing entry")


@app.command("add-mechanic")
def add_mechanic(
    name: str = typer.Argument(..., help="Mechanic name"),
    true_desc: str = typer.Option("", "--true", "-t", help="True description"),
    apparent_desc: str = typer.Option("", "--apparent", "-a", help="What reader/chars think"),
    reveal_plan: str = typer.Option("", "--reveal", "-r", help="How/when truth comes out"),
) -> None:
    """Add a true world mechanic (hidden from reader)."""
    project = Project.find()
    mgr = CreativeRoomManager(project)
    mgr.ensure_isolation_marker()

    mechanic = TrueMechanic(
        name=name,
        true_description=true_desc,
        apparent_description=apparent_desc,
        reveal_plan=reveal_plan,
    )
    mgr.add_true_mechanic(mechanic)
    print_success(f"Added true mechanic: {name}")


@app.command("set-ending")
def set_ending(
    plans: str = typer.Argument(..., help="Ending plans text"),
) -> None:
    """Set or update the ending plans."""
    project = Project.find()
    mgr = CreativeRoomManager(project)
    mgr.ensure_isolation_marker()
    mgr.set_ending_plans(plans)
    print_success("Ending plans updated")


@app.command("update-knowledge")
def update_knowledge(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    scene: int = typer.Option(..., "--scene", "-s", help="Scene number"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a prompt to extract reader knowledge after a scene."""
    project = Project.find()
    extractor = KnowledgeExtractor(project)
    prompt = extractor.generate_extraction_prompt(chapter, scene)

    if output:
        with open(output, "w") as f:
            f.write(prompt)
        print_success(f"Knowledge extraction prompt saved to {output}")
    else:
        print_prompt_output(prompt, f"Extract Reader Knowledge: Ch.{chapter} Sc.{scene}")


@app.command("show-knowledge")
def show_knowledge(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
) -> None:
    """Show reader knowledge state at a chapter."""
    project = Project.find()
    chapter_id = f"chapter-{chapter:02d}"
    rk = project.load_reader_knowledge(chapter_id)

    if not rk:
        print_info(f"No reader knowledge state for chapter {chapter}.")
        return

    console.print(f"\n[bold]Reader Knowledge at: {rk.position_label}[/]\n")
    console.print(f"[green]Known Characters:[/] {', '.join(rk.known_characters)}")
    console.print(f"[green]Known Locations:[/] {', '.join(rk.known_locations)}")
    console.print(f"[green]Known Rules:[/] {', '.join(rk.known_world_rules)}")
    console.print(f"[yellow]Active Questions:[/] {', '.join(rk.active_questions)}")
    console.print(f"[red]False Beliefs:[/] {', '.join(rk.false_beliefs)}")
    console.print()
