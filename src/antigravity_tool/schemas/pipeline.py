"""Pipeline schemas for state-machine workflows."""

from enum import Enum
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PipelineState(str, Enum):
    """States of a pipeline run."""
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
    payload: dict[str, Any] = Field(default_factory=dict, description="Current payload/context of the run.")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Time the run was created.")
    error: Optional[str] = Field(default=None, description="Error message if failed.")

class PipelineRunCreate(BaseModel):
    """Model for initiating a pipeline run."""
    initial_payload: dict[str, Any] = Field(default_factory=dict, description="Starting payload for the sequence.")

class PipelineResume(BaseModel):
    """Model for resuming a paused pipeline run."""
    payload: dict[str, Any] = Field(description="Updated payload to resume execution with.")
