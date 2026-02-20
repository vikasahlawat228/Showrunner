"""Continuity checking and DNA drift detection schemas."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from antigravity_tool.schemas.base import AntigravityBase


class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(str, Enum):
    CHARACTER_STATE = "character_state"
    OUTFIT_CONTINUITY = "outfit_continuity"
    INJURY_CONTINUITY = "injury_continuity"
    LOCATION_CONTINUITY = "location_continuity"
    SCENE_FLOW = "scene_flow"
    TIME_CONTINUITY = "time_continuity"
    READER_KNOWLEDGE = "reader_knowledge"
    RELATIONSHIP_CONSISTENCY = "relationship_consistency"
    DNA_DRIFT = "dna_drift"


class ContinuityIssue(BaseModel):
    """A single detected continuity issue."""

    severity: IssueSeverity = IssueSeverity.WARNING
    category: IssueCategory = IssueCategory.CHARACTER_STATE
    location: str = ""  # e.g. "Chapter 2, Scene 3"
    description: str = ""
    suggestion: str = ""
    character_name: Optional[str] = None
    field: Optional[str] = None  # which field drifted
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None


class ContinuityReport(AntigravityBase):
    """Full continuity check report."""

    chapter_num: Optional[int] = None
    issues: list[ContinuityIssue] = Field(default_factory=list)
    checked_scenes: int = 0
    checked_characters: int = 0

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.INFO)


class DNADriftIssue(BaseModel):
    """A DNA field that drifted from the canonical character definition."""

    character_name: str = ""
    panel_location: str = ""  # e.g. "Chapter 1, Page 2, Panel 3"
    dna_field: str = ""  # e.g. "hair.color"
    canonical_value: str = ""
    prompt_value: str = ""
    severity: IssueSeverity = IssueSeverity.WARNING


class DNADriftReport(AntigravityBase):
    """DNA drift check report for one or all characters."""

    character_name: Optional[str] = None  # None = all characters
    issues: list[DNADriftIssue] = Field(default_factory=list)
    panels_checked: int = 0

    @property
    def drift_count(self) -> int:
        return len(self.issues)
