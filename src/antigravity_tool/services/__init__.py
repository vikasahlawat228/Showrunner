"""Service layer -- reusable business logic for CLI and API.

Services encapsulate the ContextCompiler -> TemplateEngine -> render
pipeline that previously lived directly in command handlers.
"""

from antigravity_tool.services.base import ServiceContext, PromptResult

__all__ = ["ServiceContext", "PromptResult"]
