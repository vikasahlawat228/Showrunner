"""Pydantic v2 schemas for all Showrunner data types."""

from showrunner_tool.schemas.base import ShowrunnerBase
from showrunner_tool.schemas.character import (
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
from showrunner_tool.schemas.world import (
    WorldSettings,
    Location,
    WorldRule,
    Faction,
    HistoricalEvent,
)
from showrunner_tool.schemas.scene import Scene, TimeOfDay, Weather, SceneType
from showrunner_tool.schemas.screenplay import Screenplay, ScreenplayBeat, BeatType
from showrunner_tool.schemas.panel import (
    Panel,
    ShotType,
    CameraAngle,
    PanelSize,
    PanelWidth,
    CharacterInPanel,
    DialogueBubble,
)
from showrunner_tool.schemas.style_guide import VisualStyleGuide, NarrativeStyleGuide
from showrunner_tool.schemas.story_structure import (
    StoryStructure,
    StoryBeat,
    CharacterArcBeat,
    StructureType,
    SubArc,
    SubArcType,
)
from showrunner_tool.schemas.creative_room import (
    CreativeRoom,
    PlotTwist,
    CharacterSecret,
    ForeshadowingEntry,
    TrueMechanic,
    ReaderKnowledgeState,
)
from showrunner_tool.schemas.evaluation import EvaluationResult, ScoreEntry
from showrunner_tool.schemas.genre import GenrePreset
from showrunner_tool.schemas.continuity import (
    ContinuityIssue,
    ContinuityReport,
    IssueSeverity,
    IssueCategory,
    DNADriftIssue,
    DNADriftReport,
)
from showrunner_tool.schemas.timeline import (
    Timeline,
    TimelineEvent,
    TimelineIssue,
    TimelineUnit,
)
from showrunner_tool.schemas.assets import (
    ReferenceImage,
    ReferenceLibrary,
    ReferenceType,
)
from showrunner_tool.schemas.pacing import (
    PacingMetrics,
    PacingIssue,
    PacingReport,
)
from showrunner_tool.schemas.analytics import (
    AnalyticsReport,
    CharacterStats,
)
from showrunner_tool.schemas.session import (
    Decision,
    DecisionCategory,
    DecisionScope,
    SessionAction,
    SessionEntry,
    ChapterSummary,
    ProjectBrief,
)
from showrunner_tool.schemas.pipeline import (
    PipelineState,
    PipelineRun,
    PipelineRunCreate,
    PipelineResume,
)
from showrunner_tool.schemas.dal import (
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
    "ShowrunnerBase",
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
