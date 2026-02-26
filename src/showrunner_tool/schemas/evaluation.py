"""Evaluation result schemas for story quality assessment."""

from __future__ import annotations

from pydantic import BaseModel, Field

from showrunner_tool.schemas.base import ShowrunnerBase


class ScoreEntry(BaseModel):
    criterion: str
    score: float = 0.0
    reasoning: str = ""
    suggestions: list[str] = Field(default_factory=list)


class EvaluationResult(ShowrunnerBase):
    target_type: str = ""
    target_id: str = ""
    target_name: str = ""
    evaluator_type: str = ""
    scores: list[ScoreEntry] = Field(default_factory=list)
    overall_score: float = 0.0
    summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    knowledge_base_refs: list[str] = Field(default_factory=list)
