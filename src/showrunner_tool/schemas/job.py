from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(BaseModel):
    id: str
    job_type: str  # e.g., "pipeline"
    status: JobStatus = JobStatus.PENDING
    progress: int = Field(default=0, ge=0, le=100)
    message: str = "Initializing..."
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float
    updated_at: float

class JobCreate(BaseModel):
    job_type: str
    payload: Dict[str, Any]
