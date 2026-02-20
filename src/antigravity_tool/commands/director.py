"""antigravity director - autonomous agent commands."""
from __future__ import annotations

import typer
from typing import Optional

from antigravity_tool.core.project import Project
from antigravity_tool.agent.llm import LLMClient
from antigravity_tool.agent.director import Director
from antigravity_tool.utils.display import console, print_info

app = typer.Typer(help="Autonomous Director Agent commands.")

@app.command("action")
def action(
    model: str = typer.Option("gemini/gemini-1.5-pro", "--model", "-m", help="LLM Model ID"),
) -> None:
    """Analyze the project and perform the next best action."""
    project = Project.find()
    
    console.print(f"[bold]Starting Director Agent ({model})...[/]")
    llm = LLMClient(model=model)
    director = Director(project, llm)
    
    director.act()

@app.command("loop")
def loop(
    steps: int = typer.Option(5, "--steps", "-n", help="Max steps to run"),
    model: str = typer.Option("gemini/gemini-1.5-pro", "--model", "-m", help="LLM Model ID"),
) -> None:
    """Run the Director Agent in a loop."""
    project = Project.find()
    
    console.print(f"[bold]Starting Director Loop ({steps} steps)...[/]")
    llm = LLMClient(model=model)
    director = Director(project, llm)
    
    for i in range(steps):
        console.print(f"\n[bold reverse] Step {i+1} [/]")
        director.act()
