"""Service layer -- reusable business logic for CLI and API.

Services encapsulate the ContextCompiler -> TemplateEngine -> render
pipeline that previously lived directly in command handlers.
"""

from showrunner_tool.services.base import ServiceContext, PromptResult
from showrunner_tool.services.pipeline_service import PipelineService

__all__ = ["ServiceContext", "PromptResult", "PipelineService"]
