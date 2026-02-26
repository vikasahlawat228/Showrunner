"""Timeline schemas for chronological story tracking."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from showrunner_tool.schemas.base import ShowrunnerBase


class TimelineUnit(str, Enum):
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"


class TimelineEvent(BaseModel):
    """A single event on the story timeline."""

    event_id: str = ""
    description: str = ""
    story_time: str = ""  # e.g. "Day 1, Morning" or "Year 3, Month 2"
    sort_order: float = 0.0  # numeric sort key for ordering
    chapter_num: Optional[int] = None
    scene_num: Optional[int] = None
    characters_involved: list[str] = Field(default_factory=list)
    location: str = ""
    is_flashback: bool = False
    parallel_group: Optional[str] = None  # events happening simultaneously
    duration: Optional[str] = None  # e.g. "2 hours", "3 days"
    tags: list[str] = Field(default_factory=list)


class TimelineIssue(BaseModel):
    """A detected timeline inconsistency."""

    description: str = ""
    event_a: str = ""  # description of first event
    event_b: str = ""  # description of second event
    issue_type: str = ""  # e.g. "temporal_impossibility", "character_bilocation"


class Timeline(ShowrunnerBase):
    """The story's timeline with chronological and narrative ordering."""

    events: list[TimelineEvent] = Field(default_factory=list)
    time_unit: TimelineUnit = TimelineUnit.DAYS

    def get_chronological_order(self) -> list[TimelineEvent]:
        """Return events sorted by story time (sort_order)."""
        return sorted(self.events, key=lambda e: e.sort_order)

    def get_narrative_order(self) -> list[TimelineEvent]:
        """Return events sorted by chapter/scene (narrative order)."""
        return sorted(
            self.events,
            key=lambda e: (e.chapter_num or 0, e.scene_num or 0),
        )

    def get_events_for_chapter(self, chapter_num: int) -> list[TimelineEvent]:
        """Return events in a specific chapter."""
        return [e for e in self.events if e.chapter_num == chapter_num]

    def get_parallel_events(self, group: str) -> list[TimelineEvent]:
        """Return all events in a parallel group."""
        return [e for e in self.events if e.parallel_group == group]
