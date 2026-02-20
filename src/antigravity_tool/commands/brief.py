"""antigravity brief — session briefing and CLAUDE.md management."""

from __future__ import annotations

import typer

from antigravity_tool.core.project import Project
from antigravity_tool.core.briefing import BriefingGenerator
from antigravity_tool.utils.display import console, print_success, print_info

app = typer.Typer(help="Session briefing and context management.")


@app.command("show")
def show() -> None:
    """Display current project briefing for this session."""
    project = Project.find()
    gen = BriefingGenerator(project)
    brief = gen.generate()
    md = gen.render_markdown(brief)
    from rich.markdown import Markdown
    console.print(Markdown(md))


@app.command("update")
def update_claude_md() -> None:
    """Regenerate the dynamic section of CLAUDE.md with current state."""
    project = Project.find()
    gen = BriefingGenerator(project)
    brief = gen.generate()
    dynamic_section = gen.render_markdown(brief)

    claude_md_path = project.path / "CLAUDE.md"
    if not claude_md_path.exists():
        console.print("[red]No CLAUDE.md found. Run 'antigravity init' first.[/]")
        raise typer.Exit(1)

    content = claude_md_path.read_text()

    # Replace the dynamic section between markers
    start_marker = "<!-- DYNAMIC:START -->"
    end_marker = "<!-- DYNAMIC:END -->"

    if start_marker in content and end_marker in content:
        before = content[:content.index(start_marker) + len(start_marker)]
        after = content[content.index(end_marker):]
        new_content = f"{before}\n\n{dynamic_section}\n{after}"
    else:
        # First time — append markers and dynamic section
        new_content = content.rstrip() + f"\n\n{start_marker}\n\n{dynamic_section}\n{end_marker}\n"

    claude_md_path.write_text(new_content)
    print_success("CLAUDE.md updated with current project state.")


@app.command("context")
def show_context(
    step: str = typer.Option(None, "--step", "-s", help="Workflow step to show context for"),
    chapter: int = typer.Option(None, "--chapter", "-c", help="Chapter number"),
    scene: int = typer.Option(None, "--scene", help="Scene number"),
) -> None:
    """Show what context would be compiled for a given step."""
    project = Project.find()
    from antigravity_tool.core.context_compiler import ContextCompiler
    from antigravity_tool.core.workflow import WorkflowState

    compiler = ContextCompiler(project)
    step_name = step or WorkflowState(project.path).get_current_step()

    ctx = compiler.compile_for_step(step_name, chapter_num=chapter, scene_num=scene)

    console.print(f"\n[bold]Context for step: {step_name}[/]\n")

    # Show context keys and sizes
    from antigravity_tool.utils.display import create_table
    table = create_table("Compiled Context", [("Key", ""), ("Type", ""), ("Size", "")])
    for key, value in ctx.items():
        if isinstance(value, list):
            size = f"{len(value)} items"
        elif isinstance(value, dict):
            size = f"{len(value)} keys"
        elif isinstance(value, str):
            size = f"{len(value)} chars"
        else:
            size = str(type(value).__name__)
        table.add_row(key, type(value).__name__, size)

    console.print(table)

    # Show decisions that would be injected
    from antigravity_tool.core.session_manager import DecisionLog
    dl = DecisionLog(project.path)
    decisions_text = dl.format_for_prompt(chapter=chapter, scene=scene)
    if decisions_text:
        console.print(f"\n[bold]Decisions injected:[/]\n")
        console.print(decisions_text)
    else:
        print_info("No active decisions for this context.")
