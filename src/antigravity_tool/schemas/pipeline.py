"""Pipeline schemas for state-machine workflows.

Extended for composable pipelines — tracks which step is active
and which definition is being executed.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class PipelineState(str, Enum):
    """States of a pipeline run."""
    IDLE = "IDLE"
    CONTEXT_GATHERING = "CONTEXT_GATHERING"
    PROMPT_ASSEMBLY = "PROMPT_ASSEMBLY"
    PAUSED_FOR_USER = "PAUSED_FOR_USER"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PipelineRun(BaseModel):
    """Model representing an active pipeline run."""
    id: str = Field(description="Unique ID of the pipeline run.")
    current_state: PipelineState = Field(description="Current state of the pipeline.")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Current payload/context of the run.")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Time the run was created.")
    error: Optional[str] = Field(default=None, description="Error message if failed.")

    # ── Composable pipeline extensions ────────────────────────
    definition_id: Optional[str] = Field(
        default=None,
        description="ID of the PipelineDefinition being executed (None for legacy runs).",
    )
    current_step_id: Optional[str] = Field(
        default=None,
        description="ID of the currently active step in the pipeline definition.",
    )
    current_step_type: Optional[str] = Field(
        default=None,
        description="StepType of the active step (for frontend rendering).",
    )
    current_step_label: Optional[str] = Field(
        default=None,
        description="Display name of the active step.",
    )
    current_agent_id: Optional[str] = Field(
        default=None,
        description="Skill ID of the agent currently handling this step (for frontend rendering).",
    )
    steps_completed: List[str] = Field(
        default_factory=list,
        description="IDs of steps that have finished executing.",
    )
    total_steps: int = Field(
        default=0,
        description="Total number of steps in the definition.",
    )


class PipelineRunCreate(BaseModel):
    """Model for initiating a pipeline run."""
    initial_payload: Dict[str, Any] = Field(default_factory=dict, description="Starting payload for the sequence.")
    definition_id: Optional[str] = Field(
        default=None,
        description="Pipeline definition to run. If None, uses the legacy hardcoded pipeline.",
    )


class PipelineResume(BaseModel):
    """Model for resuming a paused pipeline run."""
    payload: Dict[str, Any] = Field(description="Updated payload to resume execution with.")
