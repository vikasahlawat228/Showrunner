"""Inbox API endpoints for capture management."""

from fastapi import APIRouter, Depends
from pathlib import Path
from typing import Optional

from showrunner_tool.core.project import Project
from showrunner_tool.utils.io import read_yaml, write_yaml

router = APIRouter(prefix="/api/inbox", tags=["inbox"])


def get_project(base_dir: Optional[str] = None) -> Project:
    """Get current project."""
    return Project(Path(base_dir or "."))


def get_inbox_path(project: Project) -> Path:
    """Get path to inbox YAML file."""
    return project.project_dir / ".showrunner" / "inbox.yaml"


def load_inbox(project: Project) -> dict:
    """Load inbox YAML or return empty structure."""
    path = get_inbox_path(project)
    if path.exists():
        data = read_yaml(path)
        return data if isinstance(data, dict) and "captures" in data else {"captures": []}
    return {"captures": []}


def save_inbox(project: Project, inbox: dict) -> None:
    """Save inbox YAML."""
    path = get_inbox_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(path, inbox)


@router.get("/list")
def list_captures(project: Project = Depends(get_project)):
    """List all captures in the inbox."""
    inbox = load_inbox(project)
    return {
        "captures": inbox.get("captures", []),
        "total": len(inbox.get("captures", [])),
        "unprocessed": sum(1 for c in inbox.get("captures", []) if not c.get("processed")),
    }


@router.post("/process")
def process_capture(
    payload: dict,
    project: Project = Depends(get_project),
):
    """Process a capture (convert, discard, or skip)."""
    capture_id = payload.get("capture_id")
    action = payload.get("action")  # "convert" or "discard"
    container_id = payload.get("container_id")

    inbox = load_inbox(project)
    captures = inbox.get("captures", [])

    for capture in captures:
        if capture["id"] == capture_id:
            if action == "convert":
                capture["processed"] = True
                capture["converted_to"] = container_id
            elif action == "discard":
                capture["processed"] = True
                capture["converted_to"] = None
            break

    save_inbox(project, inbox)

    return {
        "status": "ok",
        "capture_id": capture_id,
        "action": action,
    }


@router.post("/clear")
def clear_processed(project: Project = Depends(get_project)):
    """Clear all processed captures from the inbox."""
    inbox = load_inbox(project)
    processed_count = sum(1 for c in inbox.get("captures", []) if c.get("processed"))

    # Filter out processed
    inbox["captures"] = [c for c in inbox.get("captures", []) if not c.get("processed")]

    save_inbox(project, inbox)

    return {
        "status": "ok",
        "cleared": processed_count,
    }
