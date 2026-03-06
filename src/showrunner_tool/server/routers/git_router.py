"""Git REST API router — expose git operations via HTTP.

Endpoints:
  GET  /api/v1/git/log      — Commit history for story files
  GET  /api/v1/git/diff     — Current changes to story files
  POST /api/v1/git/commit   — Generate message and commit
  POST /api/v1/git/stage    — Stage story files
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/git", tags=["git"])


class CommitRequest(BaseModel):
    """Request to generate and create a commit."""
    auto_commit: bool = False
    message: Optional[str] = None  # If provided, use this instead of generating


class CommitResponse(BaseModel):
    """Response from commit endpoint."""
    status: str  # "success" or "error"
    message: str
    commit_hash: Optional[str] = None


class DiffResponse(BaseModel):
    """Response from diff endpoint."""
    status: str
    staged_changes: str
    unstaged_changes: str
    file_count: int


def _run_git(args: list[str], cwd: Path) -> tuple[str, int]:
    """Run git command and return output + return code."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout + result.stderr, result.returncode
    except Exception as e:
        return str(e), 1


@router.get("/log")
async def get_git_log(
    lines: int = 10,
    request: Request = None,
) -> dict:
    """Get recent commits for story files.

    Query params:
      lines: Number of commits to return (default 10)
    """
    try:
        proj = request.app.state.project
        story_dirs = ["characters", "world", "containers", "fragment", "idea_card", "pipeline_def"]

        output, code = _run_git(
            ["log", "--oneline", f"-n{lines}", "--", *story_dirs],
            cwd=proj.path,
        )

        if code != 0:
            raise HTTPException(status_code=500, detail=f"Git log failed: {output}")

        commits = []
        for line in output.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2:
                commits.append({
                    "hash": parts[0],
                    "message": parts[1],
                })

        return {
            "status": "success",
            "commits": commits,
            "total": len(commits),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diff")
async def get_diff(
    staged: bool = False,
    request: Request = None,
) -> DiffResponse:
    """Get diff of changes to story files.

    Query params:
      staged: Show only staged changes (default false)
    """
    try:
        proj = request.app.state.project
        story_dirs = ["characters", "world", "containers", "fragment", "idea_card", "pipeline_def"]

        # Get staged changes
        staged_output, _ = _run_git(
            ["diff", "--staged", "--", *story_dirs],
            cwd=proj.path,
        )

        # Get unstaged changes
        unstaged_output, _ = _run_git(
            ["diff", "--", *story_dirs],
            cwd=proj.path,
        )

        # Count changed files
        file_stat, _ = _run_git(
            ["diff", "--cached" if staged else "", "--stat", "--", *story_dirs],
            cwd=proj.path,
        )
        file_count = file_stat.count("\n") - 1 if file_stat else 0

        return DiffResponse(
            status="success",
            staged_changes=staged_output if staged else staged_output[:500],
            unstaged_changes=unstaged_output if not staged else unstaged_output[:500],
            file_count=max(0, file_count),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stage")
async def stage_story(request: Request = None) -> dict:
    """Stage all story files for commit."""
    try:
        proj = request.app.state.project
        story_dirs = ["characters", "world", "containers", "fragment", "idea_card", "pipeline_def"]

        staged_count = 0
        for story_dir in story_dirs:
            dir_path = proj.path / story_dir
            if dir_path.exists():
                output, code = _run_git(["add", story_dir], cwd=proj.path)
                if code == 0:
                    staged_count += 1

        # Get staged stat
        stat_output, _ = _run_git(
            ["diff", "--cached", "--stat", "--", *story_dirs],
            cwd=proj.path,
        )

        return {
            "status": "success",
            "message": f"Staged {staged_count} story directories",
            "stat": stat_output,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/commit")
async def create_commit(
    req: CommitRequest,
    request: Request = None,
) -> CommitResponse:
    """Generate and create a commit for staged story files.

    Request body:
      auto_commit: If true, don't require confirmation
      message: If provided, use this message instead of generating
    """
    try:
        proj = request.app.state.project

        # Check if there are staged changes
        stat_output, code = _run_git(
            ["diff", "--cached", "--stat"],
            cwd=proj.path,
        )

        if code != 0 or not stat_output.strip():
            raise HTTPException(status_code=400, detail="No staged changes found")

        # Use provided message or generate one
        commit_msg = req.message
        if not commit_msg:
            # Get the diff for context
            diff_output, _ = _run_git(["diff", "--cached"], cwd=proj.path)

            # Generate message using Claude
            try:
                from litellm import completion

                prompt = f"""Generate a git commit message for story files based on this diff.
The message should:
- Start with a verb (Add, Update, Fix, Revise)
- Be 1-2 sentences max
- Describe story impact, not technical details

DIFF:
{diff_output[:1500]}

Generate ONLY the message (no quotes, no markdown):"""

                response = completion(
                    model="gemini/gemini-2.0-flash",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                )

                commit_msg = response.choices[0].message.content.strip()

            except Exception as e:
                # Fallback message
                file_count = stat_output.count("\n")
                commit_msg = f"Update story files ({file_count} changed)"

        # Create the commit
        output, code = _run_git(
            ["commit", "-m", commit_msg],
            cwd=proj.path,
        )

        if code != 0:
            raise HTTPException(status_code=500, detail=f"Commit failed: {output}")

        # Extract commit hash
        import re
        match = re.search(r"\[[\w/]+\s+([a-f0-9]+)\]", output)
        commit_hash = match.group(1)[:8] if match else "unknown"

        return CommitResponse(
            status="success",
            message=commit_msg,
            commit_hash=commit_hash,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_git_status(request: Request = None) -> dict:
    """Get git status for story files."""
    try:
        proj = request.app.state.project
        story_dirs = ["characters", "world", "containers", "fragment", "idea_card", "pipeline_def"]

        output, code = _run_git(
            ["status", "--porcelain", "--", *story_dirs],
            cwd=proj.path,
        )

        staged = []
        unstaged = []
        untracked = []

        for line in output.strip().split("\n"):
            if not line:
                continue
            status = line[:2]
            filename = line[3:]

            if status[0] != " ":
                staged.append({"status": status, "file": filename})
            if status[1] != " ":
                unstaged.append({"status": status, "file": filename})
            if status == "??":
                untracked.append(filename)

        return {
            "status": "success",
            "staged": staged,
            "unstaged": unstaged,
            "untracked": untracked,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
