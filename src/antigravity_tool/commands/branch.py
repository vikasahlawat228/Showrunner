"""antigravity branch - branching narratives / what-if commands."""

from __future__ import annotations

from typing import Optional

import typer

from antigravity_tool.core.project import Project
from antigravity_tool.core.branching import BranchManager
from antigravity_tool.core.template_engine import TemplateEngine
from antigravity_tool.core.context_compiler import ContextCompiler
from antigravity_tool.utils.display import (
    console, create_table, print_success, print_info, print_error, print_prompt_output,
)

app = typer.Typer(help="Branching narratives (what-if scenarios).")


@app.command("create")
def create_branch(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    scene: int = typer.Option(..., "--scene", "-s", help="Scene number to branch"),
    label: str = typer.Option(..., "--label", "-l", help="Branch label (e.g. 'Hero refuses')"),
) -> None:
    """Create a new branch from an existing scene."""
    project = Project.find()
    manager = BranchManager(project)

    try:
        branch = manager.create_branch(chapter, scene, label)
        print_success(f"Created branch: {label}")
        console.print(f"  [dim]Branch ID: {branch.branch_id[:8]}[/]")
        console.print(f"  [dim]Parent scene: Ch.{chapter} Sc.{scene}[/]")
        console.print(f"\n[dim]Use 'antigravity branch write --branch-id {branch.branch_id[:8]}' to write this branch.[/]")
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("list")
def list_branches(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    scene: Optional[int] = typer.Option(None, "--scene", "-s", help="Filter by scene"),
) -> None:
    """List all branches for a chapter or scene."""
    project = Project.find()
    manager = BranchManager(project)

    branches = manager.list_branches(chapter, scene)

    if not branches:
        print_info(f"No branches found for chapter {chapter}" + (f" scene {scene}" if scene else ""))
        return

    table = create_table("Narrative Branches", [
        ("Scene", "dim"),
        ("Branch ID", "cyan"),
        ("Label", "magenta"),
        ("Title", ""),
        ("Canonical", "green"),
    ])

    for b in branches:
        table.add_row(
            str(b.scene_number),
            (b.branch_id or "")[:8],
            b.branch_label,
            b.title[:40],
            "[green]YES[/]" if b.is_canonical else "[dim]no[/]",
        )

    console.print(table)


@app.command("compare")
def compare_branches(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    scene: int = typer.Option(..., "--scene", "-s", help="Scene number"),
) -> None:
    """Compare canonical scene with its branches."""
    project = Project.find()
    manager = BranchManager(project)

    comparison = manager.compare_branches(chapter, scene)

    console.print(f"\n[bold]Branch Comparison: Ch.{chapter} Sc.{scene}[/]\n")

    canonical = comparison.get("canonical")
    if canonical:
        console.print("[bold green]Canonical:[/]")
        console.print(f"  Title: {canonical.get('title', 'Untitled')}")
        console.print(f"  Key events: {', '.join(canonical.get('key_events', []))}")
        console.print(f"  Closing: {canonical.get('closing_state', '')}")
        console.print()

    branches = comparison.get("branches", [])
    for i, b in enumerate(branches):
        console.print(f"[bold cyan]Branch {i+1}: {b.get('branch_label', 'unnamed')}[/]")
        console.print(f"  Title: {b.get('title', 'Untitled')}")
        console.print(f"  Key events: {', '.join(b.get('key_events', []))}")
        console.print(f"  Closing: {b.get('closing_state', '')}")
        console.print()

    console.print(f"[dim]Total branches: {comparison.get('branch_count', 0)}[/]")


@app.command("promote")
def promote_branch(
    branch_id: str = typer.Argument(..., help="Branch ID to promote (first 8 chars)"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
) -> None:
    """Promote a branch to canonical status."""
    project = Project.find()
    manager = BranchManager(project)

    result = manager.promote_branch(chapter, branch_id)

    if result:
        print_success(f"Promoted branch '{result.branch_label}' to canonical for scene {result.scene_number}")
    else:
        print_error(f"Branch '{branch_id}' not found.")
        raise typer.Exit(1)


@app.command("write")
def write_branch(
    branch_id: str = typer.Option(..., "--branch-id", help="Branch ID to write"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a writing prompt for a specific branch."""
    project = Project.find()
    compiler = ContextCompiler(project)
    engine = TemplateEngine(project.user_prompts_dir)
    manager = BranchManager(project)

    # Find the branch
    branches = manager.list_branches(chapter)
    target = next((b for b in branches if b.branch_id and b.branch_id.startswith(branch_id)), None)

    if not target:
        print_error(f"Branch '{branch_id}' not found.")
        raise typer.Exit(1)

    ctx = compiler.compile_for_step(
        "scene_writing",
        chapter_num=chapter,
        scene_num=target.scene_number,
    )
    ctx["chapter_num"] = chapter
    ctx["scene_num"] = target.scene_number
    ctx["branch_label"] = target.branch_label
    ctx["branch_id"] = target.branch_id
    ctx["is_branch"] = True

    prompt = engine.render("scene/write_scene.md.j2", **ctx)

    if output:
        with open(output, "w") as f:
            f.write(prompt)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(prompt, f"Write Branch: {target.branch_label}")
