"""LLM Client wrapper for Showrunner."""
from __future__ import annotations

import os
from typing import Any, Optional
import json

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from litellm import completion

console = Console()

class LLMClient:
    """Handles communication with LLM providers."""

    def __init__(self, model: str = "gemini/gemini-1.5-pro", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            # Try to load from .env file manually if not in env
            try:
                from dotenv import load_dotenv
                load_dotenv()
                self.api_key = os.getenv("GEMINI_API_KEY")
            except ImportError:
                pass
        
        if not self.api_key:
            console.print("[yellow]Warning: GEMINI_API_KEY not found in environment.[/]")

    def generate(self, prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
        """Generate text from the LLM."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        try:
            response = completion(
                model=self.model,
                messages=messages,
                api_key=self.api_key,
            )
            return response.choices[0].message.content
        except Exception as e:
            console.print(f"[bold red]LLM Error:[/]{e}")
            return ""

    def generate_stream(self, prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
        """Generate text with streaming output to console."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        full_content = ""
        try:
            response = completion(
                model=self.model,
                messages=messages,
                api_key=self.api_key,
                stream=True,
            )
            
            with Live(Markdown(""), refresh_per_second=10) as live:
                for chunk in response:
                    content = chunk.choices[0].delta.content or ""
                    full_content += content
                    live.update(Markdown(full_content))
            
            return full_content
        except Exception as e:
            console.print(f"[bold red]LLM Stream Error:[/]{e}")
            return full_content
