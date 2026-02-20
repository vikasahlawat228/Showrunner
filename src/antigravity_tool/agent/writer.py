"""The Writer Agent - Responsible for content generation."""
from __future__ import annotations

import yaml
from typing import Any

from antigravity_tool.agent.llm import LLMClient
from antigravity_tool.utils.display import console

class Writer:
    """The creative engine that turns strict prompts into content."""

    def __init__(self, client: LLMClient):
        self.client = client

    def write(self, prompt: str, task_type: str = "general") -> str:
        """Generate content based on the prompt."""
        system_prompt = (
            "You are an expert creative writer and narrative designer. "
            "Your task is to generate structured YAML content based strictly on the provided context. "
            "Do not output markdown code blocks. Output raw YAML text only. "
            "Follow the schema requirements exactly."
        )
        
        console.print(f"[bold green]Writer Agent[/] starting task: [cyan]{task_type}[/]")
        return self.client.generate_stream(prompt, system_prompt)

    def parse_yaml(self, content: str) -> dict[str, Any]:
        """Clean and parse the output into a dictionary."""
        # Strip code blocks if present
        clean = content.replace("```yaml", "").replace("```", "").strip()
        try:
            return yaml.safe_load(clean)
        except yaml.YAMLError as e:
            console.print(f"[red]YAML Parsing Error:[/]{e}")
            return {}
