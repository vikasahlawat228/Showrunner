"""Pydantic v2 schemas for all Antigravity data types."""

from antigravity_tool.schemas.base import AntigravityBase
from antigravity_tool.schemas.character import (
    Character,
    CharacterDNA,
    CharacterRole,
    FacialFeatures,
    HairDescription,
    BodyDescription,
    OutfitCanon,
    Personality,
    CharacterArc,
    Relationship,
    CharacterState,
    RelationshipEdge,
    RelationshipEvolution,
    RelationshipGraph,
)
from antigravity_tool.schemas.world import (
    WorldSettings,
    Location,
    WorldRule,
    Faction,
    HistoricalEvent,
)
from antigravity_tool.schemas.scene import Scene, TimeOfDay, Weather, SceneType
from antigravity_tool.schemas.screenplay import Screenplay, ScreenplayBeat, BeatType
from antigravity_tool.schemas.panel import (
    Panel,
    ShotType,
    CameraAngle,
    PanelSize,
    PanelWidth,
    CharacterInPanel,
    DialogueBubble,
)
from antigravity_tool.schemas.style_guide import VisualStyleGuide, NarrativeStyleGuide
from antigravity_tool.schemas.story_structure import (
    StoryStructure,
    StoryBeat,
    CharacterArcBeat,
    StructureType,
    SubArc,
    SubArcType,
)
from antigravity_tool.schemas.creative_room import (
    CreativeRoom,
    PlotTwist,
    CharacterSecret,
    ForeshadowingEntry,
    TrueMechanic,
    ReaderKnowledgeState,
)
from antigravity_tool.schemas.evaluation import EvaluationResult, ScoreEntry
from antigravity_tool.schemas.genre import GenrePreset
from antigravity_tool.schemas.continuity import (
    ContinuityIssue,
    ContinuityReport,
    IssueSeverity,
    IssueCategory,
    DNADriftIssue,
    DNADriftReport,
)
from antigravity_tool.schemas.timeline import (
    Timeline,
    TimelineEvent,
    TimelineIssue,
    TimelineUnit,
)
from antigravity_tool.schemas.assets import (
    ReferenceImage,
    ReferenceLibrary,
    ReferenceType,
)
from antigravity_tool.schemas.pacing import (
    PacingMetrics,
    PacingIssue,
    PacingReport,
)
from antigravity_tool.schemas.analytics import (
    AnalyticsReport,
    CharacterStats,
)
from antigravity_tool.schemas.session import (
    Decision,
    DecisionCategory,
    DecisionScope,
    SessionAction,
    SessionEntry,
    ChapterSummary,
    ProjectBrief,
)
from antigravity_tool.schemas.pipeline import (
    PipelineState,
    PipelineRun,
    PipelineRunCreate,
    PipelineResume,
)
from antigravity_tool.schemas.dal import (
    SyncMetadata,
    CacheEntry,
    CacheStats,
    ContextScope,
    ProjectSnapshot,
    UnitOfWorkEntry,
    DBHealthReport,
    ConsistencyIssue,
)

__all__ = [
    "AntigravityBase",
    "Character", "CharacterDNA", "CharacterRole", "FacialFeatures",
    "HairDescription", "BodyDescription", "OutfitCanon", "Personality",
    "CharacterArc", "Relationship",
    "CharacterState", "RelationshipEdge", "RelationshipEvolution", "RelationshipGraph",
    "WorldSettings", "Location", "WorldRule", "Faction", "HistoricalEvent",
    "Scene", "TimeOfDay", "Weather", "SceneType",
    "Screenplay", "ScreenplayBeat", "BeatType",
    "Panel", "ShotType", "CameraAngle", "PanelSize", "PanelWidth",
    "CharacterInPanel", "DialogueBubble",
    "VisualStyleGuide", "NarrativeStyleGuide",
    "StoryStructure", "StoryBeat", "CharacterArcBeat", "StructureType",
    "SubArc", "SubArcType",
    "CreativeRoom", "PlotTwist", "CharacterSecret", "ForeshadowingEntry",
    "TrueMechanic", "ReaderKnowledgeState",
    "EvaluationResult", "ScoreEntry",
    "GenrePreset",
    "ContinuityIssue", "ContinuityReport", "IssueSeverity", "IssueCategory",
    "DNADriftIssue", "DNADriftReport",
    "Timeline", "TimelineEvent", "TimelineIssue", "TimelineUnit",
    "ReferenceImage", "ReferenceLibrary", "ReferenceType",
    "PacingMetrics", "PacingIssue", "PacingReport",
    "AnalyticsReport", "CharacterStats",
    "Decision", "DecisionCategory", "DecisionScope",
    "SessionAction", "SessionEntry",
    "ChapterSummary", "ProjectBrief",
    "PipelineState", "PipelineRun", "PipelineRunCreate", "PipelineResume",
    "SyncMetadata", "CacheEntry", "CacheStats", "ContextScope",
    "ProjectSnapshot", "UnitOfWorkEntry", "DBHealthReport", "ConsistencyIssue",
]
