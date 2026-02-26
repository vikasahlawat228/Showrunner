"""Root CLI application for Showrunner."""

from __future__ import annotations

import typer

from showrunner_tool.commands import (
    init_cmd,
    world,
    character,
    story,
    scene,
    screenplay,
    panel,
    image_prompt,
    creative_room,
    evaluate,
    knowledge_cmd,
    export,
    director,
    brief,
    decide,
    session_cmd,
    genre,
    character_state,
    relationship,
    check,
    timeline,
    reference,
    generate,
    composite,
    branch,
    pacing,
    analytics,
    server,
    db,
)
from showrunner_tool.core.project import Project, ProjectError
from showrunner_tool.core.workflow import WorkflowState, STEP_LABELS
from showrunner_tool.utils.display import console, create_table, print_info

app = typer.Typer(
    name="showrunner",
    help="CLI tool for creating manga/manhwa/comic panels with agentic AI workflows.",
    no_args_is_help=True,
)

# Register commands
app.command("init")(init_cmd.init_project)
app.add_typer(world.app, name="world")
app.add_typer(character.app, name="character")
app.add_typer(story.app, name="story")
app.add_typer(scene.app, name="scene")
app.add_typer(screenplay.app, name="screenplay")
app.add_typer(panel.app, name="panel")
app.add_typer(image_prompt.app, name="prompt")
app.add_typer(creative_room.app, name="creative-room")
app.add_typer(evaluate.app, name="evaluate")
app.add_typer(knowledge_cmd.app, name="knowledge")
app.add_typer(export.app, name="export")
app.add_typer(director.app, name="director")
app.add_typer(brief.app, name="brief")
app.add_typer(decide.app, name="decide")
app.add_typer(session_cmd.app, name="session")
app.add_typer(genre.app, name="genre")
app.add_typer(character_state.app, name="character-state")
app.add_typer(relationship.app, name="relationship")
app.add_typer(check.app, name="check")
app.add_typer(timeline.app, name="timeline")
app.add_typer(reference.app, name="reference")
app.add_typer(generate.app, name="generate")
app.add_typer(composite.app, name="composite")
app.add_typer(branch.app, name="branch")
app.add_typer(pacing.app, name="pacing")
app.add_typer(analytics.app, name="analytics")
app.add_typer(server.app, name="server")
app.add_typer(db.app, name="db")


@app.command("status")
def status() -> None:
    """Show project status and workflow progress."""
    try:
        project = Project.find()
    except ProjectError:
        print_info("No project found. Run 'showrunner init <name>' to create one.")
        return

    console.print(f"\n[bold]{project.name}[/]")
    console.print(f"[dim]{project.path}[/]\n")

    # Validation
    ok, errors = project.is_valid()
    if not ok:
        console.print("[red]Project issues:[/]")
        for err in errors:
            console.print(f"  - {err}")
        console.print()

    # Workflow progress
    wf = WorkflowState(project.path)
    table = create_table("Workflow Progress", [
        ("Step", ""),
        ("Status", ""),
    ])

    status_icons = {
        "pending": "[dim]pending[/]",
        "in_progress": "[yellow]in progress[/]",
        "complete": "[green]complete[/]",
    }

    for step_key, label, step_status in wf.get_progress_summary():
        icon = status_icons.get(step_status, step_status)
        is_current = step_key == wf.get_current_step()
        name = f"[bold]> {label}[/]" if is_current else f"  {label}"
        table.add_row(name, icon)

    console.print(table)

    # Quick stats
    characters = project.load_all_characters(filter_secrets=False)
    console.print(f"\n[dim]Characters:[/] {len(characters)}")

    structure = project.load_story_structure()
    if structure and structure.beats:
        filled = sum(1 for b in structure.beats if b.content)
        console.print(f"[dim]Story beats:[/] {filled}/{len(structure.beats)} filled")

    console.print()
