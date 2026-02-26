"""API request/response schemas (separate from domain schemas).

These define the API contract and are decoupled from internal models.
"""

from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, Any
import os


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


class DispatchRequest(BaseModel):
    intent: str
    context: dict[str, Any] = {}


class AgentResultResponse(BaseModel):
    skill_used: str
    response: str
    actions: list[dict[str, Any]] = []
    success: bool
    error: Optional[str] = None
    model_used: str = ""
    context_used: list[str] = []


class AgentSkillSummary(BaseModel):
    name: str
    description: str
    keywords: list[str]


# ── Character Progressions ──────────────────────────────────────

class CharacterProgression(BaseModel):
    id: Optional[str] = None
    chapter: int
    label: str
    changes: dict  # Partial DNA changes
    notes: str = ""

class ProgressionCreateRequest(BaseModel):
    chapter: int
    label: str
    changes: dict
    notes: str = ""

class ResolvedDNAResponse(BaseModel):
    character_id: str
    character_name: str
    chapter: int
    resolved_dna: dict  # Full merged DNA at this chapter
    progressions_applied: list[str]  # Labels of applied progressions


# ── Reader Preview Simulation ───────────────────────────────────

class PanelReadingMetrics(BaseModel):
    panel_id: str
    panel_number: int
    panel_type: str
    estimated_reading_seconds: float
    text_density: float
    is_info_dense: bool
    pacing_type: str

class ReadingSimResult(BaseModel):
    scene_id: str
    scene_name: str
    total_reading_seconds: float
    panels: list[PanelReadingMetrics]
    pacing_dead_zones: list[dict[str, Any]]
    info_overload_warnings: list[dict[str, Any]]
    engagement_score: float
    recommendations: list[str]

# ── Research ────────────────────────────────────────────────────


class ResearchQueryRequest(BaseModel):
    query: str
    context: dict[str, Any] = {}


class ResearchResultResponse(BaseModel):
    id: str
    original_query: str
    summary: str
    confidence_score: float
    sources: list[str]
    key_facts: dict[str, Any]
    created_at: str
    updated_at: str


class ResearchLibraryResponse(BaseModel):
    items: list[ResearchResultResponse]
    total: int


# ── Analysis ────────────────────────────────────────────────────

class EmotionalScoreResponse(BaseModel):
    scene_id: str
    scene_name: str
    chapter: int
    scene_number: int
    hope: float
    conflict: float
    tension: float
    sadness: float
    joy: float
    dominant_emotion: str
    summary: str


class EmotionalArcResponse(BaseModel):
    scores: list[EmotionalScoreResponse]
    flat_zones: list[dict[str, Any]]
    peak_moments: list[dict[str, Any]]
    pacing_grade: str
    recommendations: list[str]


class CharacterRibbonResponse(BaseModel):
    scene_id: str
    scene_name: str
    chapter: int
    scene_number: int
    characters: list[dict[str, Any]]

class VoiceProfileResponse(BaseModel):
    character_id: str
    character_name: str
    avg_sentence_length: float
    vocabulary_diversity: float
    formality_score: float
    top_phrases: list[str]
    dialogue_sample_count: int


class VoiceScorecardResponse(BaseModel):
    profiles: list[VoiceProfileResponse]
    similarity_matrix: list[dict]
    warnings: list[str]


class ContinuityCheckRequest(BaseModel):
    container_id: str
    proposed_changes: Optional[dict[str, Any]] = None

class ContinuityCheckResponse(BaseModel):
    status: str
    reasoning: str
    suggestions: str
    affected_entities: list[str]
    severity: str
    flagged_text: Optional[str] = None

class SuggestResolutionsRequest(BaseModel):
    issue: dict[str, Any]

class ResolutionOption(BaseModel):
    description: str
    affected_scenes: list[str]
    original_text: Optional[str] = None
    edits: str
    risk: str
    trade_off: str

class StyleCheckRequest(BaseModel):
    text: str
    scene_id: Optional[str] = None

class StyleIssueResponse(BaseModel):
    category: str
    severity: str
    location: str
    description: str
    suggestion: str

class StyleCheckResponse(BaseModel):
    status: str
    overall_score: float
    issues: list[StyleIssueResponse]
    strengths: list[str]
    summary: str


# ── Containers ──────────────────────────────────────────────────

class ContainerCreateRequest(BaseModel):
    container_type: str
    name: str
    parent_id: Optional[str] = None
    attributes: dict = {}
    sort_order: int = 0

class ContainerUpdateRequest(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None
    attributes: Optional[dict] = None
    sort_order: Optional[int] = None

class ReorderRequest(BaseModel):
    items: list[dict]

class ExtractFromTextRequest(BaseModel):
    text: str

# ── Sync ────────────────────────────────────────────────────────

class SyncAuthRequest(BaseModel):
    auth_code: str

class SyncRevertRequest(BaseModel):
    yaml_path: str
    revision_id: str


class ApplyEditRequest(BaseModel):
    fragment_id: str
    original_text: str
    replacement_text: str
    branch_id: str = "main"


class AltTakeRequest(BaseModel):
    fragment_id: str
    highlighted_text: str
    prompt: str
    branch_id: str = "main"
