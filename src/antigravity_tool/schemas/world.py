"""World-building schemas for settings, locations, rules, factions, and history."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from antigravity_tool.schemas.base import AntigravityBase


class Location(AntigravityBase):
    name: str
    type: str = ""
    description: str = ""
    atmosphere: str = ""
    visual_description: str = ""
    notable_features: list[str] = Field(default_factory=list)
    connected_to: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class WorldRule(BaseModel):
    name: str
    category: str = ""
    description: str = ""
    limitations: list[str] = Field(default_factory=list)
    known_to_reader: bool = True


class Faction(AntigravityBase):
    name: str
    type: str = ""
    description: str = ""
    goals: list[str] = Field(default_factory=list)
    leader_character_id: Optional[str] = None
    member_character_ids: list[str] = Field(default_factory=list)
    relationships_to_other_factions: dict[str, str] = Field(default_factory=dict)
    visual_motif: str = ""
    tags: list[str] = Field(default_factory=list)


class HistoricalEvent(BaseModel):
    name: str
    period: str = ""
    description: str = ""
    impact: str = ""
    known_to_reader: bool = True


class WorldSettings(AntigravityBase):
    name: str
    genre: str = ""
    time_period: str = ""
    tone: str = ""
    one_line: str = ""
    description: str = ""
    locations: list[Location] = Field(default_factory=list)
    rules: list[WorldRule] = Field(default_factory=list)
    factions: list[Faction] = Field(default_factory=list)
    history: list[HistoricalEvent] = Field(default_factory=list)
    technology_level: str = ""
    cultural_notes: list[str] = Field(default_factory=list)
