from fastapi import APIRouter, Depends, Query

from showrunner_tool.server.deps import get_analysis_service, get_continuity_service, get_style_service
from showrunner_tool.server.api_schemas import EmotionalArcResponse, CharacterRibbonResponse, VoiceScorecardResponse, ContinuityCheckRequest, ContinuityCheckResponse, SuggestResolutionsRequest, ResolutionOption, StyleCheckRequest, StyleCheckResponse
from showrunner_tool.services.analysis_service import AnalysisService
from showrunner_tool.services.continuity_service import ContinuityService
from showrunner_tool.services.style_service import StyleService

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.get("/emotional-arc", response_model=EmotionalArcResponse)
async def get_emotional_arc(
    chapter: int | None = Query(None, description="Optional chapter filter"),
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    """LLM-scored emotional valence per scene."""
    result = await analysis_service.analyze_emotional_arc(chapter=chapter)
    return EmotionalArcResponse(
        scores=[s.__dict__ for s in result.scores],
        flat_zones=result.flat_zones,
        peak_moments=result.peak_moments,
        pacing_grade=result.pacing_grade,
        recommendations=result.recommendations,
    )


@router.get("/ribbons", response_model=list[CharacterRibbonResponse])
async def get_ribbons(
    chapter: int | None = Query(None, description="Optional chapter filter"),
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    """Character presence per scene for SVG ribbons."""
    result = analysis_service.compute_character_ribbons(chapter=chapter)
    # Convert list of dataclasses to list of dicts that pydantic can parse
    return [CharacterRibbonResponse(**r.__dict__) for r in result]


@router.get("/voice-scorecard", response_model=VoiceScorecardResponse)
async def get_voice_scorecard(
    character_ids: str | None = Query(None, description="Comma-separated character IDs"),
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    """Analyze dialogue patterns and voice similarity across characters."""
    ids_list = [cid.strip() for cid in character_ids.split(",")] if character_ids else None
    result = await analysis_service.analyze_character_voices(character_ids=ids_list)
    return VoiceScorecardResponse(
        profiles=[p.__dict__ for p in result.profiles],
        similarity_matrix=result.similarity_matrix,
        warnings=result.warnings,
    )


@router.post("/continuity-check", response_model=ContinuityCheckResponse)
async def check_continuity(
    body: ContinuityCheckRequest,
    svc: ContinuityService = Depends(get_continuity_service),
):
    """Run continuity validation on a container."""
    result = await svc.check_continuity(body.container_id, body.proposed_changes)
    return ContinuityCheckResponse(
        status=result.status,
        reasoning=result.reasoning,
        suggestions=result.suggestions,
        affected_entities=result.affected_entities,
        severity=result.severity
    )


@router.post("/continuity-check/scene/{scene_id}", response_model=list[ContinuityCheckResponse])
async def check_scene_continuity(
    scene_id: str,
    svc: ContinuityService = Depends(get_continuity_service),
):
    """Run continuity checks on all entities in a scene."""
    verdicts = await svc.check_scene_continuity(scene_id)
    return [
        ContinuityCheckResponse(
            status=v.status,
            reasoning=v.reasoning,
            suggestions=v.suggestions,
            affected_entities=v.affected_entities,
            severity=v.severity
        ) for v in verdicts
    ]


@router.get("/continuity-issues", response_model=list[ContinuityCheckResponse])
async def get_continuity_issues(
    scope: str = Query("all", description="Scope of issues to fetch"),
    scope_id: str | None = Query(None, description="Scope ID if applicable"),
    svc: ContinuityService = Depends(get_continuity_service),
):
    """List recent continuity issues."""
    verdicts = await svc.get_recent_issues(scope, scope_id)
    return [
        ContinuityCheckResponse(
            status=v.status,
            reasoning=v.reasoning,
            suggestions=v.suggestions,
            affected_entities=v.affected_entities,
            severity=v.severity
        ) for v in verdicts
    ]


@router.post("/continuity/suggest-resolutions", response_model=list[ResolutionOption])
async def suggest_resolutions(
    body: SuggestResolutionsRequest,
    svc: ContinuityService = Depends(get_continuity_service),
):
    """Generate resolution options for a continuity issue."""
    options = await svc.suggest_resolutions(body.issue, {})
    return [ResolutionOption(**opt) for opt in options]


@router.post("/style-check", response_model=StyleCheckResponse)
async def check_style(
    body: StyleCheckRequest,
    svc: StyleService = Depends(get_style_service),
):
    """Evaluate prose against the project's style guide."""
    result = await svc.evaluate_style(text=body.text, scene_id=body.scene_id)
    return StyleCheckResponse(
        status=result.status,
        overall_score=result.overall_score,
        issues=[i.__dict__ for i in result.issues],
        strengths=result.strengths,
        summary=result.summary,
    )


