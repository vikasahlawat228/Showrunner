"""GIT command — story file version control integration.

Usage:
    showrunner git stage-story      # Stage only story files
    showrunner git commit-message   # Generate AI commit message
    showrunner git history          # Show story commit history
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.syntax import Syntax

from showrunner_tool.core.project import Project

console = Console()

app = typer.Typer(help="Git operations for story files.")


def _run_git(args: list[str], cwd: Optional[Path] = None) -> tuple[str, int]:
    """Run a git command and return output + return code."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd or Path.cwd(),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout + result.stderr, result.returncode
    except Exception as e:
        return str(e), 1


@app.command("stage-story")
def stage_story() -> None:
    """Stage all story files (characters, world, containers, fragments, etc.)."""
    try:
        proj = Project.find(Path.cwd())
        console.print(f"[dim]Project: {proj.name}[/dim]")

        # Story file patterns
        story_dirs = [
            "characters",
            "world",
            "containers",
            "fragment",
            "idea_card",
            "pipeline_def",
        ]

        # Stage each directory
        staged_count = 0
        for story_dir in story_dirs:
            dir_path = proj.path / story_dir
            if dir_path.exists():
                output, code = _run_git(["add", story_dir], cwd=proj.path)
                if code == 0:
                    staged_count += 1
                    console.print(f"[green]✓[/green] Staged [cyan]{story_dir}/[/cyan]")
                else:
                    console.print(f"[yellow]⚠[/yellow] {story_dir}: {output.strip()}")

        console.print(f"\n[green]✓ Staged {staged_count} story directories[/green]")

        # Show what's staged
        output, _ = _run_git(
            ["diff", "--staged", "--stat", "--"] + story_dirs,
            cwd=proj.path,
        )
        if output:
            console.print(f"\n[bold]Staged changes:[/bold]\n{output}")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("commit-message")
def generate_commit_message(
    auto_commit: bool = typer.Option(
        False,
        "--auto",
        help="Automatically commit without confirmation",
    ),
) -> None:
    """Generate an AI-powered commit message for staged story files.

    Reads the staged diff and uses Claude to generate a meaningful commit message.
    """
    try:
        proj = Project.find(Path.cwd())

        # Check if there are staged changes
        output, code = _run_git(
            ["diff", "--staged", "--stat"],
            cwd=proj.path,
        )
        if code != 0 or not output.strip():
            console.print("[yellow]ℹ No staged changes found.[/yellow]")
            console.print("Run [cyan]showrunner git stage-story[/cyan] first.")
            raise typer.Exit(1)

        console.print("[cyan]Reading staged changes...[/cyan]")

        # Get the full staged diff
        diff_output, _ = _run_git(
            ["diff", "--staged"],
            cwd=proj.path,
        )

        # Generate commit message using Claude
        console.print("[cyan]Generating commit message with Claude...[/cyan]")

        try:
            from litellm import completion

            prompt = f"""You are a git commit message composer. Read this story file diff and generate a concise,
meaningful commit message.

The message should:
- Start with a verb (Add, Update, Fix, Revise, etc.)
- Be 1-2 sentences max
- Describe WHAT changed and WHY (not HOW)
- Be appropriate for a creative writing project
- Focus on story impact, not technical details

Examples of good messages:
- "Chapter 3 Scene 2: Zara discovers the artifact; update character state"
- "Add researched feudal armor details; integrate into Ch4"
- "Revise pacing in Act 2; tighten emotional beats"

DIFF:
{diff_output[:2000]}  # First 2000 chars to avoid context explosion

Generate ONLY the commit message (no quotes, no markdown, just the text):"""

            response = completion(
                model="gemini/gemini-2.0-flash",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )

            commit_msg = response.choices[0].message.content.strip()

        except Exception as e:
            console.print(f"[yellow]⚠ Claude generation failed ({e}), using default.[/yellow]")
            # Fallback: generate simple message from file counts
            file_count = output.count("\n")
            commit_msg = f"Update story files ({file_count} changed)"

        # Show preview
        console.print(f"\n[bold]Proposed commit message:[/bold]\n")
        console.print(f"[green]{commit_msg}[/green]\n")

        if auto_commit:
            confirmed = True
        else:
            confirmed = typer.confirm("Commit with this message?", default=True)

        if confirmed:
            # Create the commit
            output, code = _run_git(
                ["commit", "-m", commit_msg],
                cwd=proj.path,
            )

            if code == 0:
                # Extract commit hash
                import re

                match = re.search(r"\[[\w/]+\s+([a-f0-9]+)\]", output)
                commit_hash = match.group(1)[:8] if match else "..."

                console.print(f"\n[green]✓ Committed! ({commit_hash})[/green]")
                console.print(f"\nMessage: [cyan]{commit_msg}[/cyan]")
            else:
                console.print(f"[red]✗ Commit failed: {output}[/red]")
                raise typer.Exit(1)
        else:
            console.print("[yellow]Commit cancelled.[/yellow]")

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("history")
def show_history(
    lines: int = typer.Option(
        10,
        "--lines",
        "-n",
        help="Number of commits to show",
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-v",
        help="Show detailed commit info",
    ),
) -> None:
    """Show git history for story files only."""
    try:
        proj = Project.find(Path.cwd())
        console.print(f"[dim]Project: {proj.name}[/dim]\n")

        # Story file patterns
        story_files = [
            "characters",
            "world",
            "containers",
            "fragment",
            "idea_card",
            "pipeline_def",
        ]

        if detailed:
            # Show full commit details
            output, code = _run_git(
                ["log", "--oneline", f"-n{lines}", "--", *story_files],
                cwd=proj.path,
            )
            if code == 0 and output:
                console.print("[bold]Story commit history:[/bold]\n")
                console.print(output)
            else:
                console.print("[yellow]No story commits found.[/yellow]")
        else:
            # Show oneline format with nice formatting
            output, code = _run_git(
                ["log", "--oneline", f"-n{lines}", "--", *story_files],
                cwd=proj.path,
            )

            if code == 0 and output.strip():
                console.print("[bold]Story commit history:[/bold]\n")
                for line in output.strip().split("\n"):
                    # Format: hash message
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        hash_val, msg = parts
                        console.print(f"[cyan]{hash_val}[/cyan]  {msg}")
                    else:
                        console.print(line)
            else:
                console.print("[yellow]No story commits found.[/yellow]")

            # Show summary stats
            console.print("\n[bold]Summary:[/bold]")
            stat_output, _ = _run_git(
                ["log", "--shortstat", f"-n{lines}", "--", *story_files],
                cwd=proj.path,
            )
            if stat_output:
                # Count insertions/deletions
                import re

                insertions = len(re.findall(r"(\d+) insertion", stat_output))
                deletions = len(re.findall(r"(\d+) deletion", stat_output))
                console.print(f"  Files changed: {output.count(chr(10))}")
                console.print(f"  Total insertions: ~{insertions}")
                console.print(f"  Total deletions: ~{deletions}")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("diff")
def show_diff(
    staged: bool = typer.Option(False, "--staged", "-s", help="Show staged changes only"),
) -> None:
    """Show git diff for story files."""
    try:
        proj = Project.find(Path.cwd())

        # Story file patterns
        story_files = [
            "characters",
            "world",
            "containers",
            "fragment",
            "idea_card",
            "pipeline_def",
        ]

        args = ["diff"]
        if staged:
            args.append("--staged")
        args.extend(["--", *story_files])

        output, code = _run_git(args, cwd=proj.path)

        if code == 0:
            if output.strip():
                # Syntax highlight YAML diff if possible
                console.print(output)
            else:
                console.print("[yellow]No changes found.[/yellow]")
        else:
            console.print(f"[red]✗ Diff failed: {output}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
