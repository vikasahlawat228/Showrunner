"""API request/response schemas (separate from domain schemas).

These define the API contract and are decoupled from internal models.
"""

from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, Any


# ── Responses ────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    project: str


class ProjectResponse(BaseModel):
    name: str
    path: str
    variables: dict
    workflow_step: str


class CharacterSummary(BaseModel):
    id: str
    name: str
    role: str
    one_line: str
    has_dna: bool


class SceneSummary(BaseModel):
    id: str
    title: str
    chapter: int
    scene_number: int
    scene_type: str
    tension_level: int
    characters_present: list[str] = []


class SceneDetail(BaseModel):
    id: str
    title: str
    chapter: int
    scene_number: int
    scene_type: str
    tension_level: int
    characters_present: list[str] = []
    pov_character_id: Optional[str] = None
    location_name: str = ""
    mood: str = ""
    summary: str = ""


class WorkflowStepInfo(BaseModel):
    step: str
    label: str
    status: str


class WorkflowResponse(BaseModel):
    current_step: str
    current_chapter: Optional[int] = None
    current_scene: Optional[int] = None
    steps: list[WorkflowStepInfo]


class PromptResponse(BaseModel):
    prompt_text: str
    step: str
    template_used: str
    context_keys: list[str]


class DirectorResultResponse(BaseModel):
    step_executed: str
    status: str
    files_created: list[str] = []
    files_modified: list[str] = []
    next_step: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    error: str
    error_type: str
    context: dict = {}


# ── Requests ─────────────────────────────────────────────────────

class CreateCharacterRequest(BaseModel):
    name: str
    role: str = "supporting"


class WriteSceneRequest(BaseModel):
    chapter: int
    scene: int
    beat_reference: Optional[str] = None
    scene_type: Optional[str] = None


class CompileScreenplayRequest(BaseModel):
    chapter: int
    scene: int


class DividePanelsRequest(BaseModel):
    chapter: int
    scene: int


class UpdateSceneRequest(BaseModel):
    characters_present: Optional[list[str]] = None


class DirectorActRequest(BaseModel):
    step_override: Optional[str] = None


class AddDecisionRequest(BaseModel):
    decision: str
    category: str = "meta"
    chapter: Optional[int] = None
    scene: Optional[int] = None
    character_name: Optional[str] = None
