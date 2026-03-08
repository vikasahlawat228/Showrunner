"""Project Registry Service — Multi-project discovery and management.

Maintains a registry of known projects at ~/.showrunner/projects.yaml
and allows switching between projects programmatically.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from showrunner_tool.utils.io import read_yaml, write_yaml


class ProjectSummary:
    """Summary metadata about a registered project."""

    def __init__(
        self,
        id: str,
        path: str,
        name: str,
        last_opened: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ):
        self.id = id
        self.path = path
        self.name = name
        self.last_opened = last_opened or datetime.utcnow().isoformat()
        self.tags = tags or []

    def to_dict(self):
        return {
            "id": self.id,
            "path": self.path,
            "name": self.name,
            "last_opened": self.last_opened,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ProjectSummary:
        return cls(
            id=data["id"],
            path=data["path"],
            name=data["name"],
            last_opened=data.get("last_opened"),
            tags=data.get("tags", []),
        )


class ProjectRegistryService:
    """Service for managing project registry.

    Registry lives at ~/.showrunner/projects.yaml with structure:
    ```yaml
    projects:
      - id: "quantum-dharma"
        path: "/path/to/quantum-dharma"
        name: "Quantum Dharma"
        last_opened: "2026-03-08T14:30:00Z"
        tags: ["active"]

    settings:
      default_project: "quantum-dharma"
      auto_detect: true
      remember_last: true
    ```
    """

    REGISTRY_DIR = Path.home() / ".showrunner"
    REGISTRY_FILE = REGISTRY_DIR / "projects.yaml"

    def __init__(self):
        """Initialize registry service and ensure registry file exists."""
        self.REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
        self._ensure_registry_exists()

    def _ensure_registry_exists(self):
        """Create registry file if it doesn't exist."""
        if not self.REGISTRY_FILE.exists():
            default_registry = {
                "projects": [],
                "settings": {
                    "default_project": None,
                    "auto_detect": True,
                    "remember_last": True,
                },
            }
            write_yaml(self.REGISTRY_FILE, default_registry)

    def _read_registry(self) -> dict:
        """Read registry from YAML file."""
        return read_yaml(self.REGISTRY_FILE) or {
            "projects": [],
            "settings": {},
        }

    def _write_registry(self, data: dict):
        """Write registry to YAML file."""
        write_yaml(self.REGISTRY_FILE, data)

    def get_all_projects(self) -> List[ProjectSummary]:
        """Get all registered projects."""
        registry = self._read_registry()
        projects = registry.get("projects", [])
        return [ProjectSummary.from_dict(p) for p in projects]

    def get_project_by_id(self, project_id: str) -> Optional[ProjectSummary]:
        """Get a project by ID."""
        for project in self.get_all_projects():
            if project.id == project_id:
                return project
        return None

    def get_project_by_path(self, path: str) -> Optional[ProjectSummary]:
        """Get a project by file path."""
        target_path = Path(path).resolve()
        for project in self.get_all_projects():
            if Path(project.path).resolve() == target_path:
                return project
        return None

    def get_active_project_id(self) -> Optional[str]:
        """Get the ID of the currently active project."""
        registry = self._read_registry()
        settings = registry.get("settings", {})
        return settings.get("default_project")

    def get_active_project(self) -> Optional[ProjectSummary]:
        """Get the currently active project summary."""
        active_id = self.get_active_project_id()
        if active_id:
            return self.get_project_by_id(active_id)
        return None

    def register_project(
        self, path: str, name: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> ProjectSummary:
        """Register a new project in the registry.

        Args:
            path: Absolute path to the project directory
            name: Human-readable project name (defaults to directory name)
            tags: Optional tags for categorization

        Returns:
            ProjectSummary of the registered project
        """
        path = str(Path(path).resolve())

        # Check if already registered
        existing = self.get_project_by_path(path)
        if existing:
            return existing

        # Generate ID from directory name (slugified)
        dir_name = Path(path).name
        project_id = dir_name.lower().replace(" ", "-").replace("_", "-")

        # Ensure unique ID
        counter = 1
        base_id = project_id
        while self.get_project_by_id(project_id):
            project_id = f"{base_id}-{counter}"
            counter += 1

        # Create project summary
        project = ProjectSummary(
            id=project_id,
            path=path,
            name=name or Path(path).name,
            tags=tags or [],
        )

        # Add to registry
        registry = self._read_registry()
        registry["projects"].append(project.to_dict())
        self._write_registry(registry)

        return project

    def set_active_project(self, project_id: str) -> bool:
        """Set the active project by ID.

        Args:
            project_id: ID of the project to activate

        Returns:
            True if successful, False if project not found
        """
        project = self.get_project_by_id(project_id)
        if not project:
            return False

        registry = self._read_registry()
        registry["settings"]["default_project"] = project_id

        # Update last_opened timestamp
        for p in registry["projects"]:
            if p["id"] == project_id:
                p["last_opened"] = datetime.utcnow().isoformat()
                break

        self._write_registry(registry)
        return True

    def remove_project(self, project_id: str) -> bool:
        """Remove a project from the registry.

        Args:
            project_id: ID of the project to remove

        Returns:
            True if successful, False if project not found
        """
        registry = self._read_registry()
        original_count = len(registry["projects"])

        registry["projects"] = [
            p for p in registry["projects"] if p["id"] != project_id
        ]

        if len(registry["projects"]) == original_count:
            return False  # Project not found

        # Clear default if we removed the active project
        if registry["settings"].get("default_project") == project_id:
            registry["settings"]["default_project"] = None

        self._write_registry(registry)
        return True

    def update_project_tags(self, project_id: str, tags: List[str]) -> bool:
        """Update tags for a project.

        Args:
            project_id: ID of the project
            tags: New tag list

        Returns:
            True if successful, False if project not found
        """
        registry = self._read_registry()

        for p in registry["projects"]:
            if p["id"] == project_id:
                p["tags"] = tags
                self._write_registry(registry)
                return True

        return False
