"""Agent Dispatcher -- routes user intents to specialized agent skills and executes them.

Loads agent skill definitions from markdown files in agents/skills/,
performs keyword-based and LLM-based intent routing, and executes
skills via LiteLLM.  Supports a ReAct (Reason → Act → Observe) loop
for multi-step tool-augmented agent execution.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import litellm

logger = logging.getLogger(__name__)

# Model used for both routing classification and skill execution
LLM_MODEL = "gemini/gemini-2.5-flash"

# Maximum number of Reason→Act→Observe iterations before forcing termination
DEFAULT_MAX_REACT_ITERATIONS = 5

# Regex to parse  Action: ToolName("arg")  or  Action: ToolName(arg)  lines
REACT_ACTION_RE = re.compile(
    r"Action:\s*([A-Za-z_][A-Za-z0-9_]*)\((.*)\)",
    re.DOTALL,
)

# Regex to detect a Final Answer block
FINAL_ANSWER_RE = re.compile(
    r"Final Answer:\s*(.*)",
    re.DOTALL,
)


# ── Skill & Result Models ────────────────────────────────────────


@dataclass
class AgentSkill:
    """Represents a loaded agent skill parsed from a markdown file."""

    name: str
    description: str
    system_prompt: str
    keywords: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    """Structured result from an agent skill execution."""

    skill_used: str
    response: str
    actions: list[dict] = field(default_factory=list)
    success: bool = True
    error: str | None = None
    react_iterations: int = 0  # How many ReAct loops were executed
    model_used: str = ""  # Which LLM model handled the request
    context_used: list[str] = field(default_factory=list)  # Container IDs/names injected


@dataclass
class ReActTool:
    """A tool that can be invoked during a ReAct loop."""

    name: str
    description: str
    handler: Callable[[str], str]  # Takes arg string, returns observation string


# ── Keyword Mappings ─────────────────────────────────────────────

# Manually curated keyword lists derived from each skill's domain.
# These are checked first (fast path) before falling back to LLM routing.
SKILL_KEYWORDS: dict[str, list[str]] = {
    "schema_architect": [
        "schema",
        "type",
        "entity",
        "container",
        "data model",
        "eav",
        "container type",
        "entity type",
        "define schema",
        "design schema",
    ],
    "graph_arranger": [
        "layout",
        "arrange",
        "position",
        "graph",
        "nodes",
        "canvas",
        "coordinates",
        "placement",
        "spatial",
        "overlap",
    ],
    "pipeline_director": [
        "pipeline",
        "workflow",
        "step",
        "dag",
        "execute",
        "run pipeline",
        "assemble pipeline",
        "execution plan",
        "pipeline plan",
    ],
    "continuity_analyst": [
        "continuity",
        "consistency",
        "paradox",
        "timeline",
        "validate",
        "continuity error",
        "contradiction",
        "lore check",
        "state validation",
    ],
    "schema_wizard": [
        "create type",
        "new field",
        "add property",
        "wizard",
        "natural language",
        "create schema",
        "generate schema",
        "new schema",
        "track",
        "tracking",
    ],
    "research_agent": [
        "research",
        "investigate",
        "deep dive",
        "look up",
        "find out",
        "learn about",
        "background",
        "reference material",
        "source material",
        "world building research",
    ],
    "story_architect": [
        "structure",
        "outline",
        "plan story",
        "story structure",
        "acts",
        "chapters",
        "scenes",
        "season",
        "arc",
        "decompose",
        "hierarchy",
    ],
    "prompt_composer": [
        "compose prompt",
        "refine prompt",
        "optimize prompt",
        "prompt engineering",
        "rewrite prompt",
        "improve prompt",
        "draft prompt",
    ],
    "style_enforcer": [
        "style check",
        "style guide",
        "tone",
        "pov",
        "tense",
        "voice",
        "style review",
        "enforce style",
        "narrative style",
        "prose quality",
    ],
    "translator_agent": [
        "translate",
        "translation",
        "localize",
        "localization",
        "language",
        "adapt",
        "multilingual",
        "l10n",
        "i18n",
    ],
    "brainstorm_agent": [
        "brainstorm",
        "ideas",
        "ideate",
        "what if",
        "possibilities",
        "explore options",
        "creative options",
        "plot twist",
        "diverge",
        "alternatives",
    ],
}


# ── Dispatcher ───────────────────────────────────────────────────


class AgentDispatcher:
    """Routes user intents to specialized agent skills and executes them.

    Supports a ReAct (Reason → Act → Observe) execution loop.  When an
    agent's LLM response contains ``Action: ToolName("args")``, the
    dispatcher parses the tool call, executes it via a registered handler
    (or a built-in stub), appends the observation to the conversation
    history, and re-calls the LLM.  The loop terminates when the LLM
    emits ``Final Answer: ...`` or when the max-iteration cap is reached.
    """

    def __init__(self, skills_dir: Path):
        self.skills: dict[str, AgentSkill] = {}
        self.react_tools: dict[str, ReActTool] = {}
        self._load_skills(skills_dir)
        self._register_default_tools()

    # ── Skill Loading ────────────────────────────────────────────

    def _load_skills(self, skills_dir: Path) -> None:
        """Load all .md files from the skills directory, parse their metadata.

        Skips the README.md file. For each skill file:
        - The skill name is derived from the filename (without extension)
        - The description is extracted from the first meaningful paragraph
        - Keywords come from the curated SKILL_KEYWORDS mapping
        - The full markdown content becomes the system_prompt
        """
        if not skills_dir.exists():
            logger.warning("Skills directory does not exist: %s", skills_dir)
            return

        for md_file in sorted(skills_dir.glob("*.md")):
            if md_file.name.lower() == "readme.md":
                continue

            skill_name = md_file.stem  # e.g. "schema_architect"
            content = md_file.read_text(encoding="utf-8")

            description = self._extract_description(content)
            keywords = SKILL_KEYWORDS.get(skill_name, [])

            self.skills[skill_name] = AgentSkill(
                name=skill_name,
                description=description,
                system_prompt=content,
                keywords=keywords,
            )

        logger.info(
            "Loaded %d agent skills: %s",
            len(self.skills),
            list(self.skills.keys()),
        )

    @staticmethod
    def _extract_description(content: str) -> str:
        """Extract a brief description from the skill's markdown content.

        Looks for the first non-empty paragraph that isn't a heading or
        YAML frontmatter. Falls back to the first heading text.
        """
        lines = content.split("\n")
        in_frontmatter = False
        description_lines: list[str] = []

        for line in lines:
            stripped = line.strip()

            # Skip YAML frontmatter
            if stripped == "---":
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                continue

            # Skip headings
            if stripped.startswith("#"):
                # If we already gathered some description, stop
                if description_lines:
                    break
                continue

            # Skip empty lines between heading and first paragraph
            if not stripped and not description_lines:
                continue

            # Found a non-empty, non-heading line
            if stripped:
                description_lines.append(stripped)
            else:
                # Empty line after we started collecting = end of paragraph
                if description_lines:
                    break

        desc = " ".join(description_lines)
        # Strip markdown bold markers for a cleaner description
        desc = re.sub(r"\*\*([^*]+)\*\*", r"\1", desc)
        # Truncate to a reasonable length
        if len(desc) > 200:
            desc = desc[:197] + "..."
        return desc or "Agent skill"

    # ── Routing ──────────────────────────────────────────────────

    def route(self, intent: str) -> AgentSkill | None:
        """Determine which skill best matches the user's intent.

        Strategy (in order of preference):
        1. Keyword matching against skill keywords (fast, no API call)
        2. If ambiguous or no match, return None (caller can try LLM routing)
        """
        intent_lower = intent.lower()

        # Score each skill by keyword matches
        scores: dict[str, int] = {}
        for skill_name, skill in self.skills.items():
            score = 0
            for keyword in skill.keywords:
                if keyword in intent_lower:
                    # Multi-word keywords get higher weight
                    score += len(keyword.split())
            if score > 0:
                scores[skill_name] = score

        if not scores:
            return None

        # Return the best match, but only if it's clearly dominant
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_name, best_score = sorted_scores[0]

        # If there's a tie or very close second, treat as ambiguous
        if len(sorted_scores) > 1:
            _, second_score = sorted_scores[1]
            if second_score >= best_score:
                # True tie -- ambiguous, return None to fall back
                return None

        return self.skills[best_name]

    async def route_with_llm(self, intent: str) -> AgentSkill | None:
        """Use LLM to classify the intent when keyword matching is ambiguous.

        This is a lightweight classification call, not a full generation.
        Returns None if the LLM cannot confidently match a skill.
        """
        if not self.skills:
            return None

        skill_descriptions = "\n".join(
            f"- {name}: {skill.description}"
            for name, skill in self.skills.items()
        )

        classification_prompt = (
            "You are an intent classifier. Given a user intent and a list of "
            "available agent skills, determine which skill best matches the intent.\n\n"
            f"Available skills:\n{skill_descriptions}\n\n"
            f"User intent: \"{intent}\"\n\n"
            "Respond with ONLY the skill name (e.g., 'schema_architect') if one matches, "
            "or 'none' if no skill is a good match. Do not explain."
        )

        try:
            response = await litellm.acompletion(
                model=LLM_MODEL,
                messages=[
                    {"role": "user", "content": classification_prompt},
                ],
                temperature=0.0,
                max_tokens=50,
            )
            result = response.choices[0].message.content.strip().lower()

            # Clean up any accidental quoting or punctuation
            result = result.strip("'\"`.").strip()

            if result in self.skills:
                return self.skills[result]

            return None

        except Exception as e:
            logger.warning("LLM routing call failed: %s", e)
            return None

    # ── Tool Registration ─────────────────────────────────────────

    def _register_default_tools(self) -> None:
        """Register built-in stub tools for the ReAct loop.

        These are lightweight placeholders.  Real implementations will
        be injected when KnowledgeGraphService / ChromaIndexer are wired
        into the dispatcher in a later phase.
        """
        self.register_tool(ReActTool(
            name="SearchKG",
            description="Search the Knowledge Graph for entities matching a query.",
            handler=lambda q: f'No results found for "{q}" (KG not connected yet).',
        ))
        self.register_tool(ReActTool(
            name="SemanticSearch",
            description="Perform semantic vector search over project containers.",
            handler=lambda q: f'No semantic results for "{q}" (vector store not connected yet).',
        ))
        self.register_tool(ReActTool(
            name="GetContainer",
            description="Retrieve a container by ID or type+name.",
            handler=lambda q: f'Container "{q}" not found (stub handler).',
        ))
        self.register_tool(ReActTool(
            name="ListContainers",
            description="List containers of a given type.",
            handler=lambda q: f'No containers of type "{q}" (stub handler).',
        ))

    def register_tool(self, tool: ReActTool) -> None:
        """Register a tool for use in ReAct loops."""
        self.react_tools[tool.name] = tool

    # ── Execution ────────────────────────────────────────────────

    async def execute(
        self,
        skill: AgentSkill,
        intent: str,
        context: dict | None = None,
        max_iterations: int = DEFAULT_MAX_REACT_ITERATIONS,
    ) -> AgentResult:
        """Execute a skill via LiteLLM, supporting a ReAct loop.

        The method sends the skill's system prompt and the user message
        to the LLM.  If the response contains an ``Action:`` directive,
        the dispatcher:
        1. Parses the tool name and argument.
        2. Executes the tool (or returns a stub observation).
        3. Appends an ``Observation: ...`` message to the history.
        4. Re-calls the LLM with the updated history.

        The loop terminates when:
        - The LLM emits ``Final Answer: <text>``.
        - No ``Action:`` pattern is detected (plain response).
        - ``max_iterations`` is reached.

        Args:
            skill: The matched AgentSkill to execute.
            intent: The user's original intent string.
            context: Optional dict of additional context.
            max_iterations: Cap on ReAct loop iterations.

        Returns:
            AgentResult with the final LLM response and metadata.
        """
        # Build the user message with intent and any provided context
        user_message = intent
        if context:
            context_text = json.dumps(context, indent=2, default=str)
            user_message = (
                f"{intent}\n\n"
                f"--- Context ---\n"
                f"{context_text}"
            )

        # Build the available-tools preamble so the LLM knows what it can call
        tools_preamble = self._build_tools_preamble()
        system_content = skill.system_prompt
        if tools_preamble:
            system_content += "\n\n" + tools_preamble

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_message},
        ]

        iterations = 0
        final_response_text = ""

        try:
            while iterations < max_iterations:
                response = await litellm.acompletion(
                    model=LLM_MODEL,
                    messages=messages,
                )
                response_text = response.choices[0].message.content or ""
                iterations += 1

                # ── Check for Final Answer ────────────────────────
                final_match = FINAL_ANSWER_RE.search(response_text)
                if final_match:
                    final_response_text = final_match.group(1).strip()
                    break

                # ── Check for Action ──────────────────────────────
                action_parsed = self._parse_react_action(response_text)
                if action_parsed is None:
                    # No action pattern — treat as a direct final response
                    final_response_text = response_text
                    break

                tool_name, tool_arg = action_parsed
                logger.info(
                    "ReAct iteration %d: Action=%s(%r)",
                    iterations, tool_name, tool_arg,
                )

                # Execute the tool
                observation = self._execute_tool(tool_name, tool_arg)

                # Append the assistant's reasoning + action and the observation
                messages.append({"role": "assistant", "content": response_text})
                messages.append({
                    "role": "user",
                    "content": f"Observation: {observation}",
                })

            else:
                # Max iterations reached — use last response as-is
                logger.warning(
                    "ReAct loop hit max iterations (%d) for skill '%s'",
                    max_iterations, skill.name,
                )
                final_response_text = response_text  # type: ignore[possibly-undefined]

            # Try to extract structured actions from the final response
            actions = self._extract_actions(final_response_text)

            # Build context_used list from the context keys
            context_keys = list(context.keys()) if context else []

            return AgentResult(
                skill_used=skill.name,
                response=final_response_text,
                actions=actions,
                success=True,
                react_iterations=iterations,
                model_used=LLM_MODEL,
                context_used=context_keys,
            )

        except Exception as e:
            logger.error("Skill execution failed for '%s': %s", skill.name, e)
            return AgentResult(
                skill_used=skill.name,
                response="",
                actions=[],
                success=False,
                error=str(e),
                react_iterations=iterations,
                model_used=LLM_MODEL,
            )

    # ── ReAct Helpers ────────────────────────────────────────────

    @staticmethod
    def _parse_react_action(response_text: str) -> tuple[str, str] | None:
        """Parse an ``Action: ToolName("arg")`` directive from LLM text.

        Returns a (tool_name, argument_string) tuple, or None if no
        action pattern is found.
        """
        match = REACT_ACTION_RE.search(response_text)
        if not match:
            return None

        tool_name = match.group(1).strip()
        raw_arg = match.group(2).strip()

        # Strip surrounding quotes if present
        if (
            (raw_arg.startswith('"') and raw_arg.endswith('"'))
            or (raw_arg.startswith("'") and raw_arg.endswith("'"))
        ):
            raw_arg = raw_arg[1:-1]

        return tool_name, raw_arg

    def _execute_tool(self, tool_name: str, tool_arg: str) -> str:
        """Dispatch a tool call to its registered handler.

        Returns the observation string.  If the tool is not registered,
        returns an error message that the LLM can learn from.
        """
        tool = self.react_tools.get(tool_name)
        if tool is None:
            return (
                f"Error: Unknown tool '{tool_name}'. "
                f"Available tools: {list(self.react_tools.keys())}"
            )

        try:
            return tool.handler(tool_arg)
        except Exception as e:
            logger.error("Tool '%s' failed: %s", tool_name, e)
            return f"Error executing {tool_name}: {e}"

    def _build_tools_preamble(self) -> str:
        """Build a text block describing available tools for the LLM."""
        if not getattr(self, "react_tools", None):
            return ""

        lines = [
            "You have access to the following tools.  To use a tool, write "
            "exactly:\n  Action: ToolName(\"argument\")\n"
            "After using a tool you will receive an Observation with the result.  "
            "When you have enough information, write:\n  Final Answer: <your response>\n",
            "Available tools:",
        ]
        for tool in self.react_tools.values():
            lines.append(f"  - {tool.name}: {tool.description}")

        return "\n".join(lines)

    @staticmethod
    def _extract_actions(response_text: str) -> list[dict]:
        """Attempt to extract structured JSON actions from the LLM response.

        Looks for JSON objects or arrays in the response text (either bare
        or wrapped in markdown code fences). Returns a list of dicts.
        """
        actions: list[dict] = []

        # Try to find JSON in code fences first
        fence_pattern = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)
        matches = fence_pattern.findall(response_text)

        candidates = matches if matches else [response_text]

        for candidate in candidates:
            candidate = candidate.strip()
            if not candidate:
                continue
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    actions.append(parsed)
                elif isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, dict):
                            actions.append(item)
            except (json.JSONDecodeError, TypeError):
                continue

        return actions

    # ── Combined Route + Execute ─────────────────────────────────

    async def route_and_execute(
        self,
        intent: str,
        context: dict | None = None,
    ) -> AgentResult | None:
        """Combined route + execute for convenience.

        Routing strategy:
        1. Try keyword matching first (fast, no API call)
        2. If no keyword match, try LLM-based classification
        3. If still no match, return None (caller should fall back)

        Returns:
            AgentResult if a skill was matched and executed, None otherwise.
        """
        # Step 1: Keyword routing
        skill = self.route(intent)

        # Step 2: LLM routing fallback
        if skill is None:
            skill = await self.route_with_llm(intent)

        # Step 3: No match at all
        if skill is None:
            return None

        # Execute the matched skill
        return await self.execute(skill, intent, context)

    # ── Introspection ────────────────────────────────────────────

    def list_skills(self) -> list[dict]:
        """Return a summary of all loaded skills for API consumers."""
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "keywords": skill.keywords,
            }
            for skill in self.skills.values()
        ]
