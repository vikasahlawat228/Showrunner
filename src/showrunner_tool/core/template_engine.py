"""Jinja2-based prompt template engine with user override resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, ChoiceLoader, select_autoescape


# Built-in templates ship with the package
BUILTIN_TEMPLATES_DIR = Path(__file__).parent.parent / "prompts"


def _to_yaml_filter(value: Any) -> str:
    """Jinja2 filter to render a value as YAML."""
    return yaml.dump(value, default_flow_style=False, allow_unicode=True, sort_keys=False)


class TemplateEngine:
    """Renders Jinja2 prompt templates with context injection.

    Resolution order:
    1. User project overrides (project_path/prompts/)
    2. Built-in templates (src/showrunner/prompts/)
    """

    def __init__(self, project_prompts_dir: Path | None = None):
        loaders = []

        # User overrides first (higher priority)
        if project_prompts_dir and project_prompts_dir.exists():
            loaders.append(FileSystemLoader(str(project_prompts_dir)))

        # Built-in templates
        loaders.append(FileSystemLoader(str(BUILTIN_TEMPLATES_DIR)))

        self.env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape([]),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Custom filters
        self.env.filters["to_yaml"] = _to_yaml_filter

    def render(self, template_name: str, **context: Any) -> str:
        """Render a template with the given context."""
        template = self.env.get_template(template_name)
        return template.render(**context)

    def list_templates(self, prefix: str = "") -> list[str]:
        """List available template names, optionally filtered by prefix."""
        all_templates = self.env.loader.list_templates()
        if prefix:
            return [t for t in all_templates if t.startswith(prefix)]
        return list(all_templates)

    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists in any loader."""
        try:
            self.env.get_template(template_name)
            return True
        except Exception:
            return False
