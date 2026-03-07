"""showrunner capture - Frictionless idea capture and inbox management."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Optional
import typer

from showrunner_tool.utils.io import read_yaml, write_yaml
from showrunner_tool.utils.display import console, print_success, print_info
from showrunner_tool.core.project import Project

app = typer.Typer(help="Brain-dump idea capture and inbox management.")


def get_inbox_path(project: Project) -> Path:
    """Get path to project inbox file."""
    return project.project_dir / ".showrunner" / "inbox.yaml"


def load_inbox(project: Project) -> dict:
    """Load or create the inbox YAML."""
    inbox_path = get_inbox_path(project)
    if inbox_path.exists():
        data = read_yaml(inbox_path)
        return data if isinstance(data, dict) and "captures" in data else {"captures": []}
    return {"captures": []}


@app.command()
def capture(
    text: str = typer.Argument(..., help="The idea or observation to capture"),
    tag: Optional[str] = typer.Option(
        None, "--tag", "-t", help="Optional tags (comma-separated, e.g., 'plot-twist,season-1')"
    ),
) -> None:
    """
    Capture an idea to your project inbox.

    One-keystroke idea capture — never lose a thought.

    Examples:
        showrunner capture "Zara discovers the pendant was her mother's all along"
        showrunner capture "What if the villain isn't evil, just desperate?" --tag "plot-twist,season-2"
        showrunner capture "Research: how do feudal Japanese forges work?" --tag "research"
    """
    try:
        project = Project(Path.cwd())
    except Exception as e:
        console.print(f"[red]Not in a Showrunner project: {e}[/]")
        raise typer.Exit(1)

    # Load inbox
    inbox = load_inbox(project)

    # Create capture entry
    from ulid import ULID

    capture_id = str(ULID())
    tags = [t.strip() for t in tag.split(",")] if tag else []

    entry = {
        "id": capture_id,
        "text": text.strip(),
        "tags": tags,
        "captured_at": datetime.utcnow().isoformat() + "Z",
        "processed": False,
        "converted_to": None,  # Will store container_id when processed
    }

    inbox["captures"].append(entry)

    # Save inbox
    inbox_path = get_inbox_path(project)
    write_yaml(inbox_path, inbox)

    # Print success
    console.print()
    print_success(f"💡 Captured: {text[:60]}")
    if tags:
        console.print(f"   [dim]Tags: {', '.join(tags)}[/]")
    console.print(f"   [dim]ID: {capture_id}[/]")
    console.print()
    console.print("[dim]View all captures: showrunner inbox show[/]")


@app.command()
def inbox_show(unprocessed_only: bool = typer.Option(False, "--unprocessed", "-u", help="Only show unprocessed ideas")) -> None:
    """
    Display all captured ideas in your inbox.

    Examples:
        showrunner inbox show          # Show all captures
        showrunner inbox show -u       # Show only unprocessed
    """
    try:
        project = Project(Path.cwd())
    except Exception as e:
        console.print(f"[red]Not in a Showrunner project: {e}[/]")
        raise typer.Exit(1)

    inbox = load_inbox(project)
    captures = inbox.get("captures", [])

    if unprocessed_only:
        captures = [c for c in captures if not c.get("processed", False)]

    if not captures:
        status = "unprocessed" if unprocessed_only else "total"
        console.print(f"[dim]No {status} ideas in inbox.[/]")
        return

    console.print()
    console.print(f"[bold]Inbox ({len(captures)} ideas)[/]")
    console.print()

    for i, capture in enumerate(captures, 1):
        status = "✓" if capture.get("processed") else "○"
        text = capture["text"][:70] + ("..." if len(capture["text"]) > 70 else "")

        console.print(f"{status} [{i}] {text}")

        if capture.get("tags"):
            tags_str = ", ".join(capture["tags"])
            console.print(f"    [dim]Tags: {tags_str}[/]")

        if capture.get("converted_to"):
            console.print(f"    [dim]→ Container: {capture['converted_to']}[/]")

        captured_at = capture.get("captured_at", "")[:10]
        console.print(f"    [dim]{captured_at}[/]")
        console.print()


@app.command()
def inbox_process() -> None:
    """
    Interactively process unprocessed ideas in your inbox.

    For each unprocessed idea, choose: convert to container, discard, or skip.

    This is typically done in Claude Code after capturing ideas.
    """
    try:
        project = Project(Path.cwd())
    except Exception as e:
        console.print(f"[red]Not in a Showrunner project: {e}[/]")
        raise typer.Exit(1)

    inbox = load_inbox(project)
    captures = inbox.get("captures", [])
    unprocessed = [c for c in captures if not c.get("processed", False)]

    if not unprocessed:
        console.print("[dim]No unprocessed ideas to process.[/]")
        return

    console.print()
    console.print(f"[bold]Processing {len(unprocessed)} unprocessed ideas[/]")
    console.print()

    for capture in unprocessed:
        console.print(f"[bold]Idea:[/] {capture['text']}")
        if capture.get("tags"):
            console.print(f"[dim]Tags: {', '.join(capture['tags'])}[/]")

        console.print()
        console.print("Options:")
        console.print("  [dim]C[/]onvert to container (give container ID)")
        console.print("  [dim]S[/]kip this one")
        console.print("  [dim]D[/]iscard")
        console.print("  [dim]Q[/]uit processing")
        console.print()

        choice = console.input("Choose [c/s/d/q]: ").lower().strip()

        if choice == "c":
            container_id = console.input("Enter container ID (e.g., 'idea-zara-twin'): ").strip()
            capture["processed"] = True
            capture["converted_to"] = container_id
            print_success(f"✓ Marked as processed → {container_id}")
        elif choice == "d":
            capture["processed"] = True
            print_success("✓ Discarded")
        elif choice == "q":
            print_info("Quitting.")
            break
        # else: skip

        console.print()

    # Save updated inbox
    write_yaml(get_inbox_path(project), inbox)
    console.print("[dim]Inbox updated.[/]")


@app.command()
def inbox_clear(force: bool = typer.Option(False, "--force", "-f", help="Don't ask for confirmation")) -> None:
    """
    Clear all processed ideas from the inbox.

    Use --force to skip confirmation.
    """
    try:
        project = Project(Path.cwd())
    except Exception as e:
        console.print(f"[red]Not in a Showrunner project: {e}[/]")
        raise typer.Exit(1)

    inbox = load_inbox(project)
    processed_count = sum(1 for c in inbox.get("captures", []) if c.get("processed"))

    if processed_count == 0:
        console.print("[dim]No processed ideas to clear.[/]")
        return

    if not force:
        confirm = typer.confirm(
            f"Delete {processed_count} processed idea(s) from inbox? This cannot be undone."
        )
        if not confirm:
            print_info("Cancelled.")
            return

    # Remove processed entries
    inbox["captures"] = [c for c in inbox.get("captures", []) if not c.get("processed")]

    # Save
    write_yaml(get_inbox_path(project), inbox)
    print_success(f"✓ Cleared {processed_count} processed idea(s)")


def register_capture_commands(app: typer.Typer) -> None:
    """Register all capture/inbox commands to the main CLI app."""
    # Create the 'capture' command (direct)
    app.command(name="capture")(capture)

    # Create the 'inbox' command group
    inbox_app = typer.Typer(help="Manage your brain-dump inbox")
    inbox_app.command(name="show")(inbox_show)
    inbox_app.command(name="process")(inbox_process)
    inbox_app.command(name="clear")(inbox_clear)

    app.add_typer(inbox_app, name="inbox")
