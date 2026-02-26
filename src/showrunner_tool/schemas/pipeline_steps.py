"""Pipeline step definitions for the composable pipeline system.

This module defines the step registry — all available node types
that can be chained together in a visual pipeline builder.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from showrunner_tool.schemas.base import ShowrunnerBase


class StepCategory(str, Enum):
    """High-level grouping for step types (used for UI color-coding)."""
    CONTEXT = "context"
    TRANSFORM = "transform"
    HUMAN = "human"
    EXECUTE = "execute"
    LOGIC = "logic"


class StepType(str, Enum):
    """All available pipeline step types."""

    # Context nodes — gather information
    GATHER_BUCKETS = "gather_buckets"
    SEMANTIC_SEARCH = "semantic_search"

    # Transform nodes — reshape data
    PROMPT_TEMPLATE = "prompt_template"
    MULTI_VARIANT = "multi_variant"

    # Human checkpoint nodes — require user interaction
    REVIEW_PROMPT = "review_prompt"
    APPROVE_OUTPUT = "approve_output"
    APPROVE_IMAGE = "approve_image"

    # Execution nodes — perform actions
    LLM_GENERATE = "llm_generate"
    IMAGE_GENERATE = "image_generate"
    SAVE_TO_BUCKET = "save_to_bucket"
    HTTP_REQUEST = "http_request"
    RESEARCH_DEEP_DIVE = "research_deep_dive"
    STYLE_ENFORCE_DIALOGUE = "style_enforce_dialogue"

    # Logic nodes — control flow
    IF_ELSE = "if_else"
    LOOP = "loop"
    MERGE_OUTPUTS = "merge_outputs"


# Map step types to their category for UI rendering
STEP_CATEGORIES: Dict[StepType, StepCategory] = {
    StepType.GATHER_BUCKETS: StepCategory.CONTEXT,
    StepType.SEMANTIC_SEARCH: StepCategory.CONTEXT,
    StepType.PROMPT_TEMPLATE: StepCategory.TRANSFORM,
    StepType.MULTI_VARIANT: StepCategory.TRANSFORM,
    StepType.REVIEW_PROMPT: StepCategory.HUMAN,
    StepType.APPROVE_OUTPUT: StepCategory.HUMAN,
    StepType.APPROVE_IMAGE: StepCategory.HUMAN,
    StepType.LLM_GENERATE: StepCategory.EXECUTE,
    StepType.IMAGE_GENERATE: StepCategory.EXECUTE,
    StepType.SAVE_TO_BUCKET: StepCategory.EXECUTE,
    StepType.HTTP_REQUEST: StepCategory.EXECUTE,
    StepType.RESEARCH_DEEP_DIVE: StepCategory.EXECUTE,
    StepType.STYLE_ENFORCE_DIALOGUE: StepCategory.EXECUTE,
    StepType.IF_ELSE: StepCategory.LOGIC,
    StepType.LOOP: StepCategory.LOGIC,
    StepType.MERGE_OUTPUTS: StepCategory.LOGIC,
}

# Human-readable metadata for each step type
STEP_REGISTRY: Dict[StepType, Dict[str, Any]] = {
    StepType.GATHER_BUCKETS: {
        "label": "Gather Buckets",
        "description": "Select containers to include as context",
        "icon": "📦",
        "category": StepCategory.CONTEXT,
        "config_schema": {
            "container_types": {"type": "list[string]", "default": []},
            "max_items": {"type": "integer", "default": 10},
        },
    },
    StepType.SEMANTIC_SEARCH: {
        "label": "Semantic Search",
        "description": "Find related content by query",
        "icon": "🔍",
        "category": StepCategory.CONTEXT,
        "config_schema": {
            "query_source": {"type": "string", "default": "payload.text"},
            "limit": {"type": "integer", "default": 5},
        },
    },
    StepType.PROMPT_TEMPLATE: {
        "label": "Prompt Template",
        "description": "Assemble a prompt from context using a template",
        "icon": "📝",
        "category": StepCategory.TRANSFORM,
        "config_schema": {
            "template_id": {"type": "string", "default": ""},
            "template_inline": {"type": "string", "default": ""},
        },
    },
    StepType.MULTI_VARIANT: {
        "label": "Multi-Variant",
        "description": "Generate N variations of the input",
        "icon": "🔀",
        "category": StepCategory.TRANSFORM,
        "config_schema": {
            "count": {"type": "integer", "default": 3},
        },
    },
    StepType.REVIEW_PROMPT: {
        "label": "Review Prompt",
        "description": "Human reviews & edits the assembled prompt",
        "icon": "👁️",
        "category": StepCategory.HUMAN,
        "config_schema": {},
    },
    StepType.APPROVE_OUTPUT: {
        "label": "Approve Output",
        "description": "Human approves, rejects, or edits AI output",
        "icon": "✅",
        "category": StepCategory.HUMAN,
        "config_schema": {
            "allow_edit": {"type": "boolean", "default": True},
        },
    },
    StepType.APPROVE_IMAGE: {
        "label": "Approve Image",
        "description": "Human reviews generated image prompt/result",
        "icon": "🖼️",
        "category": StepCategory.HUMAN,
        "config_schema": {},
    },
    StepType.LLM_GENERATE: {
        "label": "LLM Generate",
        "description": "Send prompt to Gemini/Claude/GPT",
        "icon": "🤖",
        "category": StepCategory.EXECUTE,
        "config_schema": {
            "model": {"type": "string", "default": "gemini/gemini-2.0-flash"},
            "temperature": {"type": "float", "default": 0.7},
            "max_tokens": {"type": "integer", "default": 2048},
        },
    },
    StepType.IMAGE_GENERATE: {
        "label": "Image Generate",
        "description": "Send prompt to Imagen for image generation",
        "icon": "🎨",
        "category": StepCategory.EXECUTE,
        "config_schema": {
            "model": {"type": "string", "default": "imagen"},
            "style": {"type": "string", "default": "manga"},
        },
    },
    StepType.SAVE_TO_BUCKET: {
        "label": "Save to Bucket",
        "description": "Persist the result as a container",
        "icon": "💾",
        "category": StepCategory.EXECUTE,
        "config_schema": {
            "container_type": {"type": "string", "default": "fragment"},
            "name_template": {"type": "string", "default": "Generated {step_id}"},
        },
    },
    StepType.HTTP_REQUEST: {
        "label": "HTTP Request",
        "description": "Call an external API or webhook",
        "icon": "🌐",
        "category": StepCategory.EXECUTE,
        "config_schema": {
            "url": {"type": "string", "default": ""},
            "method": {"type": "string", "default": "POST"},
            "headers": {"type": "json", "default": {}},
        },
    },
    StepType.RESEARCH_DEEP_DIVE: {
        "label": "Research Deep Dive",
        "description": "Use the research agent to investigate a topic and save findings",
        "icon": "🔬",
        "category": StepCategory.EXECUTE,
        "config_schema": {
            "query_source": {"type": "string", "default": "payload.text", "description": "Payload key containing the research query"},
            "save_to_library": {"type": "boolean", "default": True, "description": "Whether to persist results to the research library"},
        },
    },
    StepType.STYLE_ENFORCE_DIALOGUE: {
        "label": "Enforce Style on Dialogue",
        "description": "Restyle a specific character's dialogue without affecting surrounding prose",
        "icon": "🎭",
        "category": StepCategory.EXECUTE,
        "config_schema": {
            "speaker_name": {"type": "string", "default": "", "description": "Name of the character"},
            "voice_profile_bucket_id": {"type": "string", "default": "", "description": "ID of the voice profile container"},
        },
    },
    StepType.IF_ELSE: {
        "label": "If / Else",
        "description": "Branch pipeline based on a condition evaluated against the payload",
        "icon": "🔀",
        "category": StepCategory.LOGIC,
        "config_schema": {
            "condition": {"type": "string", "default": "", "description": "Expression evaluated against payload, e.g. 'word_count > 500'"},
            "true_target": {"type": "string", "default": "", "description": "Step ID to jump to when condition is true"},
            "false_target": {"type": "string", "default": "", "description": "Step ID to jump to when condition is false"},
        },
    },
    StepType.LOOP: {
        "label": "Loop",
        "description": "Repeat a section of the pipeline until a condition is met or max iterations reached",
        "icon": "🔁",
        "category": StepCategory.LOGIC,
        "config_schema": {
            "condition": {"type": "string", "default": "", "description": "Exit condition — loop continues while this is false"},
            "loop_back_to": {"type": "string", "default": "", "description": "Step ID to jump back to on each iteration"},
            "max_iterations": {"type": "integer", "default": 10},
        },
    },
    StepType.MERGE_OUTPUTS: {
        "label": "Merge Outputs",
        "description": "Collect outputs from parallel branches into a single merged payload",
        "icon": "🔗",
        "category": StepCategory.LOGIC,
        "config_schema": {
            "source_keys": {"type": "list[string]", "default": [], "description": "Payload keys to merge from upstream branches"},
            "merge_strategy": {"type": "string", "default": "shallow", "description": "'shallow' or 'deep' merge"},
        },
    },
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class PipelineStepDef(BaseModel):
    """A single step in a pipeline definition."""

    id: str = Field(description="Unique step ID within this pipeline (e.g. 'step_1')")
    step_type: StepType
    label: str = Field(description="Display name for this step instance")
    config: Dict[str, Any] = Field(default_factory=dict, description="Step-specific config")
    position: Dict[str, float] = Field(
        default_factory=lambda: {"x": 0, "y": 0},
        description="React Flow node position {x, y}",
    )


class PipelineEdge(BaseModel):
    """A connection between two steps in the pipeline DAG."""

    source: str = Field(description="Source step ID")
    target: str = Field(description="Target step ID")


class PipelineDefinition(ShowrunnerBase):
    """A saved, reusable pipeline definition (stored as YAML).

    This is the composition: a DAG of steps that can be
    instantiated as a PipelineRun.
    """

    container_type: str = "pipeline"
    name: str = Field(description="Pipeline display name")
    description: str = Field(default="", description="What this pipeline does")
    steps: List[PipelineStepDef] = Field(default_factory=list)
    edges: List[PipelineEdge] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class PipelineDefinitionCreate(BaseModel):
    """POST body for saving a pipeline definition."""

    name: str
    description: str = ""
    steps: List[PipelineStepDef] = Field(default_factory=list)
    edges: List[PipelineEdge] = Field(default_factory=list)


class PipelineDefinitionResponse(BaseModel):
    """Response model for a pipeline definition."""

    id: str
    name: str
    description: str
    steps: List[PipelineStepDef]
    edges: List[PipelineEdge]
    created_at: str
    updated_at: str


class StepRegistryEntry(BaseModel):
    """A single entry in the step registry (for the frontend step library)."""

    step_type: str
    label: str
    description: str
    icon: str
    category: str
    config_schema: Dict[str, Any]


# ---------------------------------------------------------------------------
# Recorded Action Distillation models
# ---------------------------------------------------------------------------


class RecordedActionPayload(BaseModel):
    """A single recorded UI action from the frontend workflow recorder."""

    type: str = Field(
        description="Action type: slash_command, chat_message, approval, text_selection, option_select, save, entity_mention"
    )
    description: str = Field(default="", description="Human-readable description of the action")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Context payload captured with the action")


class DistillRequest(BaseModel):
    """Request body for distilling recorded actions into a pipeline definition."""

    title: str = Field(description="Display name for the generated pipeline")
    actions: List[RecordedActionPayload] = Field(
        description="Ordered list of recorded user actions to distill into a pipeline DAG"
    )
