"""Rich console display helpers."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown

console = Console()


def print_success(message: str) -> None:
    console.print(f"[bold green]OK[/] {message}")


def print_error(message: str) -> None:
    console.print(f"[bold red]ERROR[/] {message}")


def print_warning(message: str) -> None:
    console.print(f"[bold yellow]WARN[/] {message}")


def print_info(message: str) -> None:
    console.print(f"[bold blue]INFO[/] {message}")


def print_panel(title: str, content: str, style: str = "blue") -> None:
    """Print content inside a Rich panel."""
    console.print(Panel(content, title=title, border_style=style))


def print_yaml(content: str, title: str | None = None) -> None:
    """Print YAML with syntax highlighting."""
    syntax = Syntax(content, "yaml", theme="monokai", line_numbers=False)
    if title:
        console.print(Panel(syntax, title=title, border_style="cyan"))
    else:
        console.print(syntax)


def print_markdown(content: str) -> None:
    """Print rendered markdown."""
    console.print(Markdown(content))


def print_prompt_output(prompt_text: str, title: str = "Generated Prompt") -> None:
    """Print an assembled prompt with clear boundaries."""
    console.print()
    console.print(Panel(
        Markdown(prompt_text),
        title=f"[bold]{title}[/]",
        border_style="green",
        subtitle="Copy this prompt to your LLM",
    ))
    console.print()


def create_table(title: str, columns: list[tuple[str, str]]) -> Table:
    """Create a Rich table with predefined columns.

    columns: list of (header, style) tuples.
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for header, style in columns:
        table.add_column(header, style=style)
    return table
