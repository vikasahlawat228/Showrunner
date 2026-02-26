"""Context store CRUD operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from showrunner_tool.utils.io import read_yaml, write_yaml


class ContextStore:
    """Read/write context data from the project's YAML files."""

    def __init__(self, project_path: Path):
        self.project_path = project_path

    def read(self, relative_path: str) -> Any:
        """Read a YAML file relative to the project root."""
        full_path = self.project_path / relative_path
        if not full_path.exists():
            return {}
        return read_yaml(full_path)

    def write(self, relative_path: str, data: Any) -> Path:
        """Write data to a YAML file relative to the project root."""
        full_path = self.project_path / relative_path
        write_yaml(full_path, data)
        return full_path

    def exists(self, relative_path: str) -> bool:
        return (self.project_path / relative_path).exists()

    def list_files(self, relative_dir: str, pattern: str = "*.yaml") -> list[Path]:
        """List YAML files in a directory, excluding templates."""
        d = self.project_path / relative_dir
        if not d.exists():
            return []
        return sorted(
            f for f in d.glob(pattern)
            if not f.name.startswith("_")
        )

    def read_all_in_dir(self, relative_dir: str) -> list[dict]:
        """Read all YAML files in a directory."""
        results = []
        for f in self.list_files(relative_dir):
            results.append(read_yaml(f))
        return results
