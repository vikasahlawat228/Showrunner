"""The Director Agent - CLI-friendly wrapper around DirectorService.

This module preserves the original Director interface for CLI use
while delegating to DirectorService for actual logic.
"""
from __future__ import annotations

from antigravity_tool.core.project import Project
from antigravity_tool.agent.llm import LLMClient
from antigravity_tool.agent.writer import Writer
from antigravity_tool.services.base import ServiceContext
from antigravity_tool.services.director_service import DirectorService, DirectorResult
from antigravity_tool.utils.display import console, print_success, print_info


class Director:
    """CLI-friendly director that prints results to console.

    Delegates to DirectorService for actual logic, then formats
    the DirectorResult for Rich console output.
    """

    def __init__(self, project: Project, llm_client: LLMClient):
        ctx = ServiceContext.from_project(project)
        self.service = DirectorService(ctx, Writer(llm_client))
        self.project = project

    def act(self) -> None:
        """Analyze state and perform the next best action."""
        result = self.service.act()

        console.print(f"[bold blue]Director:[/] {result.message}")

        if result.status == "success":
            for f in result.files_created:
                print_success(f"Created: {f}")
            for f in result.files_modified:
                print_info(f"Modified: {f}")
        elif result.status == "skipped":
            console.print(f"[yellow]Step skipped:[/] {result.step_executed}")
        elif result.status == "error":
            console.print(f"[red]Error in {result.step_executed}:[/] {result.message}")

        if result.next_step:
            console.print(f"[dim]Next step: {result.next_step}[/]")
