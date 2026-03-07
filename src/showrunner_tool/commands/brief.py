"""showrunner brief — session briefing and CLAUDE.md management."""

from __future__ import annotations

import typer

from showrunner_tool.core.project import Project
from showrunner_tool.core.briefing import BriefingGenerator
from showrunner_tool.utils.display import console, print_success, print_info

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
        console.print("[red]No CLAUDE.md found. Run 'showrunner init' first.[/]")
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
    format: str = typer.Option("md", "--format", "-f", help="Output format: 'md' or 'json'"),
    explain: bool = typer.Option(False, "--explain-context", help="Show which context entries are injected and their token counts"),
) -> None:
    """Show what context would be compiled for a given step.

    Formats:
      md (default) — Human-readable markdown
      json — Machine-readable JSON (for IDE agents)

    Use --explain-context to see exactly which entities are included with token estimates.
    """
    project = Project.find()

    if format == "json":
        # Output IDE context as JSON
        gen = BriefingGenerator(project)
        brief = gen.generate()
        ide_context = gen.to_ide_context(brief)

        import json
        json_output = json.dumps(ide_context, indent=2)
        console.print(json_output)
    else:
        # Original markdown output
        from showrunner_tool.core.context_compiler import ContextCompiler
        from showrunner_tool.core.workflow import WorkflowState

        compiler = ContextCompiler(project)
        step_name = step or WorkflowState(project.path).get_current_step()

        ctx = compiler.compile_for_step(step_name, chapter_num=chapter, scene_num=scene)

        console.print(f"\n[bold]Context for step: {step_name}[/]\n")

        # Show context injection transparency if requested
        if explain:
            _show_context_injection_detail(project, ctx, chapter, scene)
        else:
            # Show context keys and sizes
            from showrunner_tool.utils.display import create_table
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
        from showrunner_tool.core.session_manager import DecisionLog
        dl = DecisionLog(project.path)
        decisions_text = dl.format_for_prompt(chapter=chapter, scene=scene)
        if decisions_text:
            console.print(f"\n[bold]Decisions injected:[/]\n")
            console.print(decisions_text)
        else:
            print_info("No active decisions for this context.")


def _estimate_tokens(text: str | dict | list) -> int:
    """Estimate token count. Rough approximation: ~4 chars = 1 token."""
    if isinstance(text, str):
        return len(text) // 4
    elif isinstance(text, dict):
        import json
        return len(json.dumps(text)) // 4
    elif isinstance(text, list):
        import json
        return len(json.dumps(text)) // 4
    return 0


def _show_context_injection_detail(
    project: Project,
    ctx: dict,
    chapter: int | None,
    scene: int | None,
) -> None:
    """Show detailed breakdown of which entities are included in context."""
    from pathlib import Path
    from showrunner_tool.utils.io import read_yaml
    from showrunner_tool.utils.display import create_table

    console.print("[bold cyan]Context Injection Breakdown[/]\n")

    # Collect all available entities
    entities = {
        "characters": [],
        "locations": [],
        "research": [],
        "decisions": [],
    }

    # Load all characters
    for char_file in (project.path / "characters").glob("*.yaml"):
        if char_file.stem != "template":
            entities["characters"].append({
                "type": "character",
                "name": char_file.stem,
                "path": str(char_file.relative_to(project.path)),
                "content": read_yaml(char_file),
            })

    # Load locations from world/locations/
    locations_dir = project.path / "world" / "locations"
    if locations_dir.exists():
        for loc_file in locations_dir.glob("*.yaml"):
            entities["locations"].append({
                "type": "location",
                "name": loc_file.stem,
                "path": str(loc_file.relative_to(project.path)),
                "content": read_yaml(loc_file),
            })

    # Load research containers
    research_dir = project.path / "containers"
    if research_dir.exists():
        for container_file in research_dir.glob("*.yaml"):
            if container_file.stem != "template":
                try:
                    content = read_yaml(container_file)
                    if isinstance(content, dict) and content.get("container_type") == "research":
                        entities["research"].append({
                            "type": "research",
                            "name": container_file.stem,
                            "path": str(container_file.relative_to(project.path)),
                            "content": content,
                        })
                except Exception:
                    pass

    # Load decisions
    from showrunner_tool.core.session_manager import DecisionLog
    dl = DecisionLog(project.path)
    decisions = dl.query(chapter=chapter, scene=scene)
    for dec in decisions:
        entities["decisions"].append({
            "type": "decision",
            "name": dec.decision[:50],
            "path": ".showrunner/decisions.yaml",
            "content": dec.model_dump(),
        })

    # Determine which entities are actually in the compiled context
    total_tokens = 0
    included_count = 0

    # Create summary table
    table = create_table(
        "Context Injection Summary",
        [("Status", ""), ("Entity", ""), ("Path", ""), ("Tokens", "")]
    )

    # Check characters
    for char in entities["characters"]:
        char_name = char["name"]
        is_included = any(
            char_name.lower() in str(v).lower()
            for v in ctx.values()
        )
        tokens = _estimate_tokens(char["content"])
        status = "✅" if is_included else "❌"
        reason = "" if is_included else " (not in scene)"
        table.add_row(
            status,
            f"Character: {char_name}{reason}",
            char["path"],
            str(tokens),
        )
        if is_included:
            total_tokens += tokens
            included_count += 1

    # Check locations
    for loc in entities["locations"]:
        loc_name = loc["name"]
        is_included = any(
            loc_name.lower() in str(v).lower()
            for v in ctx.values()
        )
        tokens = _estimate_tokens(loc["content"])
        status = "✅" if is_included else "❌"
        reason = "" if is_included else " (not referenced)"
        table.add_row(
            status,
            f"Location: {loc_name}{reason}",
            loc["path"],
            str(tokens),
        )
        if is_included:
            total_tokens += tokens
            included_count += 1

    # Check research
    for res in entities["research"]:
        res_name = res["name"]
        is_included = any(
            res_name.lower() in str(v).lower()
            for v in ctx.values()
        )
        tokens = _estimate_tokens(res["content"])
        status = "✅" if is_included else "❌"
        reason = "" if is_included else " (not needed)"
        table.add_row(
            status,
            f"Research: {res_name}{reason}",
            res["path"],
            str(tokens),
        )
        if is_included:
            total_tokens += tokens
            included_count += 1

    # Check decisions
    for dec in entities["decisions"]:
        dec_name = dec["name"][:40]
        is_included = "author_decisions" in ctx
        tokens = _estimate_tokens(dec["content"])
        status = "✅" if is_included else "❌"
        table.add_row(
            status,
            f"Decision: {dec_name}",
            dec["path"],
            str(tokens),
        )
        if is_included:
            total_tokens += tokens
            included_count += 1

    console.print(table)

    # Summary footer
    console.print()
    console.print(f"[dim]Included: {included_count} entries[/]")
    console.print(f"[dim]Estimated tokens: ~{total_tokens} (4 chars ≈ 1 token)[/]")
    console.print(f"[dim]Remaining budget: ~{4000 - total_tokens} tokens in 4000-token window[/]")
