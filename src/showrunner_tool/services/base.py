"""Service infrastructure -- shared context and result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from showrunner_tool.core.project import Project
from showrunner_tool.core.context_compiler import ContextCompiler
from showrunner_tool.core.template_engine import TemplateEngine
from showrunner_tool.core.workflow import WorkflowState


@dataclass
class PromptResult:
    """Result of compiling a prompt via the context pipeline."""

    prompt_text: str
    step: str
    template_used: str
    context_keys: list[str] = field(default_factory=list)


@dataclass
class ServiceContext:
    """Shared dependencies injected into all services.

    Bundles Project, ContextCompiler, TemplateEngine, and WorkflowState
    so services don't have to instantiate them individually.
    """

    project: Project
    compiler: ContextCompiler
    engine: TemplateEngine
    workflow: WorkflowState

    @classmethod
    def from_project(cls, project: Project) -> ServiceContext:
        """Create a ServiceContext from a Project instance."""
        return cls(
            project=project,
            compiler=ContextCompiler(project),
            engine=TemplateEngine(project.user_prompts_dir),
            workflow=WorkflowState(project.path),
        )
