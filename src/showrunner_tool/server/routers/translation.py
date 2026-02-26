from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from showrunner_tool.server.deps import get_translation_service
from showrunner_tool.services.translation_service import TranslationService

router = APIRouter(prefix="/api/v1/translation", tags=["translation"])

class TranslateRequest(BaseModel):
    text: str
    source_language: str = "en"
    target_language: str = "hi"
    character_ids: list[str] | None = None
    scene_id: str | None = None

class AdaptationNoteResponse(BaseModel):
    original: str
    adapted: str
    reason: str

class CulturalFlagResponse(BaseModel):
    location: str
    flag: str
    action_taken: str

class TranslateResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    adaptation_notes: list[AdaptationNoteResponse]
    cultural_flags: list[CulturalFlagResponse]
    glossary_applied: dict[str, str]
    confidence: float

class GlossaryEntryRequest(BaseModel):
    term: str
    translations: dict[str, str]
    notes: str = ""

@router.post("/translate")
async def translate_text(
    body: TranslateRequest,
    svc: TranslationService = Depends(get_translation_service),
) -> TranslateResponse:
    """Translate prose with cultural adaptation."""
    try:
        result = await svc.translate(
            text=body.text,
            source_language=body.source_language,
            target_language=body.target_language,
            character_ids=body.character_ids,
            scene_id=body.scene_id,
        )
        return TranslateResponse(
            translated_text=result.translated_text,
            source_language=result.source_language,
            target_language=result.target_language,
            adaptation_notes=[AdaptationNoteResponse(**n.__dict__) for n in result.adaptation_notes],
            cultural_flags=[CulturalFlagResponse(**f.__dict__) for f in result.cultural_flags],
            glossary_applied=result.glossary_applied,
            confidence=result.confidence,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/glossary")
async def get_glossary(
    svc: TranslationService = Depends(get_translation_service),
) -> list[dict]:
    """List all project glossary entries."""
    return svc.get_glossary()

@router.post("/glossary")
async def save_glossary_entry(
    body: GlossaryEntryRequest,
    svc: TranslationService = Depends(get_translation_service),
) -> dict:
    """Create or update a glossary entry."""
    return svc.save_glossary_entry(
        term=body.term,
        translations=body.translations,
        notes=body.notes,
    )
