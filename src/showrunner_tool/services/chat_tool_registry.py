"""Chat Tool Registry — wires classified intents to existing services.

Each tool function has the signature:
    (content: str, entity_ids: List[str]) -> str

These are registered in the ChatOrchestrator's tool_registry dict,
keyed by lowercase intent name (e.g. "search", "create", "navigate").
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List

import ulid

from showrunner_tool.schemas.chat import ChatEvent, ChatArtifact
from showrunner_tool.schemas.container import GenericContainer

logger = logging.getLogger(__name__)


def build_tool_registry(
    kg_service=None,
    container_repo=None,
    project_memory_service=None,
    pipeline_service=None,
    writing_service=None,
    project_path=None,
    agent_dispatcher=None,
    continuity_service=None,
    style_service=None,
) -> Dict[str, Callable]:
    """Build the intent → tool function mapping.

    Each tool takes (content: str, entity_ids: List[str]) -> str.
    Services are optional — if None, that tool won't be registered.
    """
    registry: Dict[str, Callable] = {}

    # ── SEARCH: query the knowledge graph ────────────────────────
    if kg_service:
        def search_tool(content: str, entity_ids: List[str], **kwargs) -> str:
            # Try entity search first, then semantic search
            results = kg_service.find_containers(filters=None)
            query = content.lower()

            # Filter by content match
            matched = []
            for r in results:
                name = str(r.get("name", "")).lower()
                ctype = str(r.get("container_type", "")).lower()
                if any(word in name for word in query.split() if len(word) > 2):
                    matched.append(r)

            if not matched:
                # Fallback to semantic search if available
                try:
                    matched = kg_service.semantic_search(content, limit=5)
                except Exception:
                    pass

            if not matched:
                return f"No results found for: {content}"

            lines = [f"Found {len(matched)} result(s):\n"]
            for i, r in enumerate(matched[:10], 1):
                name = r.get("name", r.get("id", "?"))
                ctype = r.get("container_type", "unknown")
                lines.append(f"  {i}. [{ctype}] {name}")
            return "\n".join(lines)

        registry["search"] = search_tool

    # ── CREATE: scaffold a new entity ────────────────────────────
    if container_repo and project_path:
        def create_tool(content: str, entity_ids: List[str], **kwargs) -> str:
            try:
                import litellm
                import yaml
                import uuid
                from showrunner_tool.schemas.container import GenericContainer

                session_id = kwargs.get("session_id")
                context_manager = kwargs.get("context_manager")

                history = ""
                if session_id and context_manager:
                    context = context_manager.build_context(session_id)
                    msgs = context.get("messages", [])
                    history_lines = []
                    for m in msgs[-6:]:  # include up to 6 recent messages
                        history_lines.append(f"{m['role'].upper()}: {m['content']}")
                    history = "\n".join(history_lines)
                
                system_prompt = (
                    "You are an expert at extracting structured entities from creative writing brainstorms.\n"
                    "Extract any new characters, scenes, settings, or other story elements the user describes.\n"
                    "Format the output as a clean YAML array of objects. Do not include markdown codeblocks or any other text.\n"
                    "Each object MUST have 'type' (e.g., character, scene, location, item) and 'name'.\n"
                    "Include any other relevant attributes the user mentioned or established in the history (e.g., description, age, role, traits).\n"
                    "Example:\n"
                    "- type: character\n"
                    "  name: Zara\n"
                    "  role: Protagonist\n"
                    "  traits: [brave, curious]"
                )

                user_prompt = content
                if history:
                    user_prompt = f"Recent Conversation History:\n{history}\n\nCurrent Request:\n{content}"

                response = litellm.completion(
                    model="gemini/gemini-2.5-flash",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=1024,
                )
                
                llm_output = response.choices[0].message.content.strip()
                parsed = None
                
                # Layer 1: Direct YAML/JSON load
                try:
                    parsed = yaml.safe_load(llm_output)
                except Exception:
                    logger.debug("Layer 1 parsing failed for create_tool")

                # Layer 2: Markdown block extraction
                if not isinstance(parsed, list):
                    import re
                    blocks = re.findall(r"```(?:yaml|json)?\n(.*?)\n```", llm_output, re.DOTALL)
                    for block in blocks:
                        try:
                            parsed = yaml.safe_load(block)
                            if isinstance(parsed, list):
                                break
                        except Exception:
                            continue

                # Layer 3: Heuristic Regex Fallback (extract objects)
                if not isinstance(parsed, list):
                    logger.warning("Falling back to regex parsing for create_tool output")
                    # Try to find YAML-like items "- type: ... name: ..."
                    items = []
                    item_matches = re.findall(r"- (?:type|name):.*?(?=\n- |\Z)", llm_output, re.DOTALL)
                    for item_str in item_matches:
                        try:
                            item_parsed = yaml.safe_load(item_str)
                            if isinstance(item_parsed, list):
                                items.extend(item_parsed)
                            elif isinstance(item_parsed, dict):
                                items.append(item_parsed)
                        except Exception:
                            continue
                    if items:
                        parsed = items

                created_items = []

                if isinstance(parsed, list) and len(parsed) > 0:
                    for item in parsed:
                        if not isinstance(item, dict):
                            continue
                        etype = item.get("type", "character")
                        name = item.get("name", "Unknown")
                        # Extract reserved fields from the LLM response
                        p_id = item.get("parent_id")
                        s_order = item.get("sort_order", 0)
                        
                        # All other fields go into dynamic attributes
                        reserved = ["type", "name", "parent_id", "sort_order"]
                        attrs = {k: v for k, v in item.items() if k not in reserved}
                        
                        try:
                            # Era forking logic
                            era_id = kwargs.get("era_id")
                            import re
                            season_match = re.search(r"season\s*(\d)", user_prompt, re.I)
                            if season_match:
                                era_id = f"season_{season_match.group(1)}"

                            existing_id = None
                            if entity_ids:
                                for eid in entity_ids:
                                    match = kg_service.find_containers(filters={"id": eid})
                                    if match and match[0].get("name", "").lower() == name.lower():
                                        existing_id = eid
                                        break

                            if existing_id and era_id:
                                c = kg_service.create_era_fork(existing_id, era_id)
                                c.attributes.update(attrs)
                                if p_id: c.parent_id = p_id
                                if s_order: c.sort_order = s_order
                                container_repo.save_container(c)
                                created_items.append(f"- **{name}** ({etype}) [Forked to {era_id}]")
                            else:
                                c = GenericContainer(
                                    id=str(uuid.uuid4()),
                                    name=name,
                                    container_type=etype,
                                    attributes=attrs,
                                    parent_id=p_id,
                                    sort_order=s_order,
                                    project_path=project_path,
                                    era_id=era_id
                                )
                                container_repo.save_container(c)
                                created_items.append(f"- **{name}** ({etype})")
                        except Exception as e:
                            logger.error("Failed to save container %s: %s", name, e)

                if created_items:
                    return f"Successfully scaffolded {len(created_items)} entities:\n" + "\n".join(created_items)

                return (
                    f"I extracted some information but couldn't automatically scaffold the entities. "
                    f"Please try being more specific about the types (character, scene, etc.).\n\n"
                    f"Raw output:\n```yaml\n{llm_output}\n```"
                )
            except Exception as e:
                logger.error("Error extracting entities: %s", e)
                
                # Fallback to simple heuristic
                entity_type = None
                for etype in ["character", "scene", "chapter", "world", "panel"]:
                    if etype in content.lower():
                        entity_type = etype
                        break

                if not entity_type:
                    return (
                        "I can create characters, scenes, chapters, worlds, or panels. "
                        "Please specify what you'd like to create."
                    )

                import re
                name_match = re.search(r'"([^"]+)"', content) or re.search(
                    r"(?:called|named|titled)\s+(\w[\w\s]*\w)", content, re.I
                )
                name = name_match.group(1) if name_match else f"New {entity_type.title()}"

                return (
                    f"Ready to create {entity_type}: **{name}**.\n"
                    f"However, automatic scaffolding failed. This requires manual implementation."
                )

        registry["create"] = create_tool

    # ── UNRESOLVED THREADS: search open loops ────────────────────
    if kg_service:
        def unresolved_threads_tool(content: str, entity_ids: List[str], **kwargs) -> str:
            era_id = kwargs.get("era_id")
            import re
            season_match = re.search(r"season\s*(\d)", content, re.I)
            if season_match:
                era_id = f"season_{season_match.group(1)}"
                
            threads = kg_service.get_unresolved_threads(era_id=era_id)
            if not threads:
                return "No unresolved plot threads found."
                
            lines = [f"Found {len(threads)} unresolved plot thread(s):\n"]
            for t in threads:
                desc = f": {t['description']}" if t.get('description') else ""
                lines.append(f"  - **{t['source']}** ↔ **{t['target']}** ({t['relationship']}){desc}")
                
            return "\n".join(lines)
            
        registry["unresolved_threads"] = unresolved_threads_tool

    # ── UPDATE: describe what will change ────────────────────────
    if kg_service:
        def update_tool(content: str, entity_ids: List[str], **kwargs) -> str:
            if entity_ids:
                targets = ", ".join(entity_ids[:5])
                return (
                    f"Update targets: {targets}\n"
                    f"Request: {content}\n\n"
                    f"Approval required. Use `/approve` to proceed."
                )
            return (
                f"Update request received: {content}\n\n"
                "Please @mention the entities you want to update, "
                "or I'll search for matching items."
            )

        registry["update"] = update_tool

    # ── DELETE: confirm what will be removed ──────────────────────
    if kg_service:
        def delete_tool(content: str, entity_ids: List[str], **kwargs) -> str:
            if entity_ids:
                targets = ", ".join(entity_ids[:5])
                return (
                    f"Delete targets: {targets}\n\n"
                    f"This is destructive and cannot be undone. "
                    f"Use `/approve` to confirm deletion."
                )
            return (
                f"Delete request: {content}\n\n"
                "Please @mention the entities you want to delete."
            )

        registry["delete"] = delete_tool

    # ── NAVIGATE: return the target route ────────────────────────
    def navigate_tool(content: str, entity_ids: List[str], **kwargs) -> str:
        target_routes = {
            "storyboard": "/storyboard",
            "characters": "/dashboard",
            "timeline": "/timeline",
            "pipeline": "/pipelines",
            "pipelines": "/pipelines",
            "scenes": "/storyboard",
            "panels": "/storyboard",
            "world": "/dashboard",
            "story": "/dashboard",
            "zen": "/zen",
            "brainstorm": "/brainstorm",
            "research": "/research",
            "translation": "/translation",
            "preview": "/preview",
            "dashboard": "/dashboard",
        }

        for keyword, route in target_routes.items():
            if keyword in content.lower():
                return (
                    f"Navigate to **{keyword.title()}** → `{route}`\n\n"
                    f"The frontend will switch to this view."
                )

        available = ", ".join(target_routes.keys())
        return f"Available views: {available}"

    registry["navigate"] = navigate_tool

    # ── EVALUATE: run quality checks via ContinuityService ──────────────────────────────
    if kg_service and continuity_service:
        async def evaluate_tool(content: str, entity_ids: List[str], **kwargs) -> str:
            """Evaluate story quality using ContinuityService."""
            import re

            # If no specific entity was mentioned, offer options
            if not entity_ids:
                checks = [
                    "Scene quality (pacing, dialogue, tension)",
                    "Character consistency (across scenes)",
                    "Panel composition (visual storytelling)",
                    "Dramatic irony (reader vs character knowledge)",
                    "Continuity (timeline, facts, details)",
                ]
                lines = ["Available evaluations:\n"]
                for i, check in enumerate(checks, 1):
                    lines.append(f"  {i}. {check}")
                lines.append(
                    "\nSpecify what to evaluate and @mention the target entity, "
                    "or describe the scene/content you want evaluated."
                )
                yield ChatEvent(
                    event_type="token",
                    data={"text": "\n".join(lines)}
                )
                return

            yield ChatEvent(
                event_type="action_trace",
                data={
                    "tool_name": "continuity_analyst",
                    "context_summary": f"Evaluating: {content[:60]}..."
                }
            )

            try:
                # Run continuity check on the mentioned entities
                evaluation_results = []

                for entity_id in entity_ids:
                    verdict = await continuity_service.check_continuity(entity_id)
                    evaluation_results.append({
                        "entity_id": entity_id,
                        "status": verdict.status,
                        "severity": verdict.severity,
                        "reasoning": verdict.reasoning,
                        "suggestions": verdict.suggestions,
                        "affected_entities": verdict.affected_entities,
                    })

                # Format results
                evaluation_text = "## Evaluation Results\n\n"

                for result in evaluation_results:
                    evaluation_text += f"**Entity:** {result['entity_id']}\n"
                    evaluation_text += f"**Status:** {result['status']} ({result['severity']})\n"
                    evaluation_text += f"**Reasoning:** {result['reasoning']}\n"
                    if result['suggestions']:
                        evaluation_text += f"**Suggestions:** {result['suggestions']}\n"
                    evaluation_text += "\n"

                for word in re.findall(r'\S+\s*', evaluation_text):
                    yield ChatEvent(event_type="token", data={"text": word})

                # Emit as artifact
                yield ChatEvent(
                    event_type="artifact",
                    data=ChatArtifact(
                        artifact_type="outline",
                        title="Evaluation Report",
                        content=evaluation_text
                    ).model_dump()
                )

                yield ChatEvent(
                    event_type="complete",
                    data={"type": "evaluation"}
                )

            except Exception as e:
                logger.error(f"Evaluate tool error: {e}", exc_info=True)
                yield ChatEvent(
                    event_type="token",
                    data={"text": f"Evaluation error: {str(e)}"}
                )

        registry["evaluate"] = evaluate_tool

    # ── RESEARCH: look up reference material via Research Agent ─────────────────────
    if kg_service and agent_dispatcher and container_repo:
        async def research_tool(content: str, entity_ids: List[str], **kwargs):
            """Execute research using the Research Agent skill."""
            import uuid

            session_id = kwargs.get("session_id")
            context_manager = kwargs.get("context_manager")

            # Build context from chat history if available
            context = {}
            if session_id and context_manager:
                try:
                    ctx = context_manager.build_context(session_id)
                    if ctx.get("system_context"):
                        context["chat_history_summary"] = ctx.get("system_context", "")[:500]
                except Exception:
                    pass

            # Yield action trace
            yield ChatEvent(
                event_type="action_trace",
                data={
                    "tool_name": "research_agent",
                    "context_summary": f"Researching: {content}"
                }
            )

            try:
                # Get the research agent skill
                research_skill = agent_dispatcher.skills.get("research_agent")
                if not research_skill:
                    yield ChatEvent(
                        event_type="token",
                        data={"text": "Research agent skill not found. Please check agents/skills/research_agent.md exists."}
                    )
                    return

                # Execute the skill via ReAct loop
                result = await agent_dispatcher.execute(
                    skill=research_skill,
                    intent=content,
                    context=context,
                )

                if not result.success or not result.response:
                    yield ChatEvent(
                        event_type="token",
                        data={"text": f"Research failed: {result.error}"}
                    )
                    return

                # Parse the JSON response from the research agent
                import json
                import re

                response_text = result.response.strip()

                # Try to extract JSON from the response
                research_data = None
                try:
                    # First try direct JSON parse
                    research_data = json.loads(response_text)
                except json.JSONDecodeError:
                    # Try to find JSON in markdown code block
                    match = re.search(r'```(?:json)?\n(.*?)\n```', response_text, re.DOTALL)
                    if match:
                        try:
                            research_data = json.loads(match.group(1))
                        except json.JSONDecodeError:
                            pass

                if not research_data:
                    yield ChatEvent(
                        event_type="token",
                        data={"text": f"Could not parse research output as JSON. Raw response: {response_text[:200]}"}
                    )
                    return

                # Create a research container and save it
                container_id = str(uuid.uuid4())
                research_container = GenericContainer(
                    id=container_id,
                    name=f"Research: {content[:50]}",
                    container_type="research_topic",
                    attributes={
                        "original_query": content,
                        "summary": research_data.get("summary", ""),
                        "confidence_score": research_data.get("confidence_score", 0.5),
                        "sources": research_data.get("sources", []),
                        "key_facts": research_data.get("key_facts", {}),
                    },
                    project_path=project_path,
                )

                # Save to file and index in KG
                container_repo.save_container(research_container)
                kg_service.add_or_update_container(research_container)

                # Emit artifact with the research data
                yield ChatEvent(
                    event_type="artifact",
                    data=ChatArtifact(
                        artifact_type="research",
                        title=f"Research: {content[:40]}",
                        content=json.dumps(research_data, indent=2)
                    ).model_dump()
                )

                # Stream the summary as tokens
                summary = research_data.get("summary", "No summary available")
                for word in re.findall(r'\S+\s*', summary):
                    yield ChatEvent(event_type="token", data={"text": word})

                # Add sources as final note
                sources = research_data.get("sources", [])
                if sources:
                    sources_text = "\n\n**Sources:**\n" + "\n".join(f"- {s}" for s in sources)
                    for word in re.findall(r'\S+\s*', sources_text):
                        yield ChatEvent(event_type="token", data={"text": word})

                yield ChatEvent(
                    event_type="complete",
                    data={"container_id": container_id}
                )

            except Exception as e:
                logger.error(f"Research tool error: {e}", exc_info=True)
                yield ChatEvent(
                    event_type="token",
                    data={"text": f"Research tool error: {str(e)}"}
                )

        registry["research"] = research_tool

    # ── WRITE: prose drafting via Writing Agent ──────────────────────
    if agent_dispatcher and container_repo:
        async def write_tool(content: str, entity_ids: List[str], **kwargs):
            """Generate prose using the Writing Agent (writing_agent.md if available, else fallback)."""
            import uuid
            import re

            session_id = kwargs.get("session_id")
            context_manager = kwargs.get("context_manager")

            # Build context from chat history and mentioned entities
            context = {}
            if session_id and context_manager:
                try:
                    ctx = context_manager.build_context(session_id)
                    context["chat_history"] = ctx.get("messages", [])[:5]  # Last 5 messages for context
                    context["system_context"] = ctx.get("system_context", "")[:300]
                except Exception:
                    pass

            # Add mentioned entity context
            if entity_ids and kg_service:
                mentioned = []
                for eid in entity_ids:
                    nodes = kg_service.find_containers(filters={"id": eid})
                    if nodes:
                        mentioned.append({
                            "name": nodes[0].get("name"),
                            "type": nodes[0].get("container_type"),
                            "attributes": nodes[0].get("attributes", {})
                        })
                if mentioned:
                    context["mentioned_entities"] = mentioned

            yield ChatEvent(
                event_type="action_trace",
                data={
                    "tool_name": "writing_agent",
                    "context_summary": f"Drafting prose: {content[:60]}..."
                }
            )

            try:
                # Check if writing_agent.md skill exists
                writing_skill = agent_dispatcher.skills.get("writing_agent")

                if not writing_skill:
                    # Fallback: use litellm directly with a generic writing prompt
                    import litellm

                    system_prompt = (
                        "You are an expert prose writer for fiction. Write compelling, vivid prose "
                        "that brings scenes to life with sensory details, dialogue, and emotional depth. "
                        "Match the tone and style of the provided context if available."
                    )

                    user_message = content
                    if context.get("system_context"):
                        user_message = f"Context:\n{context['system_context']}\n\nWrite:\n{content}"

                    response = await litellm.acompletion(
                        model="claude-3.5-sonnet",  # Use Claude for prose writing
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        stream=True,
                    )

                    prose_chunks = []
                    async for chunk in response:
                        if chunk.choices[0].delta.content:
                            text = chunk.choices[0].delta.content
                            prose_chunks.append(text)
                            for word in re.findall(r'\S+\s*', text):
                                yield ChatEvent(event_type="token", data={"text": word})

                    prose_text = "".join(prose_chunks)
                else:
                    # Use the writing agent skill
                    result = await agent_dispatcher.execute(
                        skill=writing_skill,
                        intent=content,
                        context=context,
                    )

                    if not result.success or not result.response:
                        yield ChatEvent(
                            event_type="token",
                            data={"text": f"Writing failed: {result.error}"}
                        )
                        return

                    prose_text = result.response
                    for word in re.findall(r'\S+\s*', prose_text):
                        yield ChatEvent(event_type="token", data={"text": word})

                # Save the generated prose as a fragment container
                fragment_id = str(uuid.uuid4())
                fragment_container = GenericContainer(
                    id=fragment_id,
                    name=f"Fragment: {content[:40]}",
                    container_type="fragment",
                    attributes={
                        "prompt": content,
                        "prose": prose_text,
                    },
                    project_path=project_path,
                )

                container_repo.save_container(fragment_container)
                if kg_service:
                    kg_service.add_or_update_container(fragment_container)

                # Emit as artifact
                yield ChatEvent(
                    event_type="artifact",
                    data=ChatArtifact(
                        artifact_type="prose",
                        title="Generated Prose",
                        content=prose_text
                    ).model_dump()
                )

                yield ChatEvent(
                    event_type="complete",
                    data={"fragment_id": fragment_id}
                )

            except Exception as e:
                logger.error(f"Write tool error: {e}", exc_info=True)
                yield ChatEvent(
                    event_type="token",
                    data={"text": f"Write tool error: {str(e)}"}
                )

        registry["write"] = write_tool

    # ── BRAINSTORM: generate ideas via Brainstorm Agent ──────────────────────
    if agent_dispatcher:
        async def brainstorm_tool(content: str, entity_ids: List[str], **kwargs):
            """Generate creative ideas using the Brainstorm Agent skill."""
            import re

            session_id = kwargs.get("session_id")
            context_manager = kwargs.get("context_manager")

            # Build context from chat history
            context = {}
            if session_id and context_manager:
                try:
                    ctx = context_manager.build_context(session_id)
                    context["system_context"] = ctx.get("system_context", "")[:300]
                except Exception:
                    pass

            yield ChatEvent(
                event_type="action_trace",
                data={
                    "tool_name": "brainstorm_agent",
                    "context_summary": f"Brainstorming: {content[:60]}..."
                }
            )

            try:
                # Try to use brainstorm_agent skill
                brainstorm_skill = agent_dispatcher.skills.get("brainstorm_agent")

                if not brainstorm_skill:
                    # Fallback: use litellm directly
                    import litellm

                    system_prompt = (
                        "You are a creative brainstorming agent for fiction writers. "
                        "Generate 5-7 creative, engaging ideas that explore the user's prompt. "
                        "Each idea should be a 1-2 sentence concept that could drive a story forward. "
                        "Be imaginative, surprising, and considerate of the story context if provided."
                    )

                    user_message = content
                    if context.get("system_context"):
                        user_message = f"Story context:\n{context['system_context']}\n\nBrainstorm:\n{content}"

                    response = await litellm.acompletion(
                        model="gemini/gemini-2.0-flash",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        stream=True,
                    )

                    ideas_text = ""
                    async for chunk in response:
                        if chunk.choices[0].delta.content:
                            text = chunk.choices[0].delta.content
                            ideas_text += text
                            for word in re.findall(r'\S+\s*', text):
                                yield ChatEvent(event_type="token", data={"text": word})
                else:
                    # Use the brainstorm agent skill
                    result = await agent_dispatcher.execute(
                        skill=brainstorm_skill,
                        intent=content,
                        context=context,
                    )

                    if not result.success or not result.response:
                        yield ChatEvent(
                            event_type="token",
                            data={"text": f"Brainstorm failed: {result.error}"}
                        )
                        return

                    ideas_text = result.response
                    for word in re.findall(r'\S+\s*', ideas_text):
                        yield ChatEvent(event_type="token", data={"text": word})

                # Emit as artifact
                yield ChatEvent(
                    event_type="artifact",
                    data=ChatArtifact(
                        artifact_type="outline",
                        title="Brainstorm Ideas",
                        content=ideas_text
                    ).model_dump()
                )

                yield ChatEvent(
                    event_type="complete",
                    data={"type": "brainstorm"}
                )

            except Exception as e:
                logger.error(f"Brainstorm tool error: {e}", exc_info=True)
                yield ChatEvent(
                    event_type="token",
                    data={"text": f"Brainstorm tool error: {str(e)}"}
                )

        registry["brainstorm"] = brainstorm_tool

    # ── OUTLINE: hierarchical story structure ──────────────────────
    if agent_dispatcher and kg_service and container_repo:
        from showrunner_tool.schemas.chat import ChatEvent, ChatArtifact
        import json

        async def outline_tool(content: str, entity_ids: List[str], **kwargs):
            """Generate a hierarchical story outline (Season → Arc → Chapter → Scene)."""
            try:
                yield ChatEvent(
                    event_type="action_trace",
                    data={"step": "outline_tool", "action": "Starting outline generation"}
                )

                # Try agent_dispatcher first (story_architect skill)
                outline_text = ""
                try:
                    result = await agent_dispatcher.execute(
                        content,
                        skill_hint="story_architect"
                    )
                    if isinstance(result, dict):
                        outline_text = result.get("outline", str(result))
                    else:
                        outline_text = str(result)
                except Exception as e:
                    logger.warning(f"Story architect skill failed: {e}. Using fallback.")

                # Fallback to direct LLM call
                if not outline_text:
                    from litellm import acompletion
                    response = await acompletion(
                        model="gemini/gemini-2.0-flash",
                        messages=[
                            {
                                "role": "system",
                                "content": """You are a Story Architect. Generate a hierarchical outline for a story/narrative.
Structure: Season → Arc → Chapter → Scene.
Format: Use markdown with # for Season, ## for Arc, ### for Chapter, #### for Scene.
Include brief descriptions (1-2 lines) for each section.
Be creative but follow the user's intent."""
                            },
                            {"role": "user", "content": content}
                        ],
                        max_tokens=2000,
                    )
                    outline_text = response.choices[0].message.content

                # Stream the outline text as tokens
                for word in outline_text.split():
                    yield ChatEvent(
                        event_type="token",
                        data={"text": word}
                    )

                # Create a container for the outline
                outline_id = str(ulid.ULID())
                outline_container = GenericContainer(
                    id=outline_id,
                    name=f"Story Outline {datetime.utcnow().strftime('%Y-%m-%d')}",
                    container_type="outline",
                    schema_version=1,
                    attributes={
                        "outline_text": outline_text,
                        "created_from": content[:200],  # Store partial context
                    }
                )

                # Save to repo
                container_repo.write(outline_container)
                kg_service.index_container(outline_container)

                yield ChatEvent(
                    event_type="artifact",
                    data={
                        "type": "outline",
                        "title": outline_container.name,
                        "content": outline_text,
                        "container_id": outline_id,
                    }
                )

                yield ChatEvent(
                    event_type="complete",
                    data={
                        "status": "success",
                        "message": f"Outline saved as {outline_container.name}",
                        "container_id": outline_id,
                    }
                )

            except Exception as e:
                logger.error(f"Outline tool error: {e}", exc_info=True)
                yield ChatEvent(
                    event_type="token",
                    data={"text": f"Outline tool error: {str(e)}"}
                )

        registry["outline"] = outline_tool

    # ── RELATIONSHIP: analyze relationships ──────────────────────
    if kg_service:
        def relationship_tool(content: str, entity_ids: List[str], **kwargs) -> str:
            if not entity_ids:
                return "Please @mention at least one character or entity to analyze relationships."
                
            results = []
            for eid in entity_ids:
                # Look up the central entity to get its name
                center_nodes = kg_service.find_containers(filters={"id": eid})
                center_name = center_nodes[0].get("name", eid) if center_nodes else eid
                
                neighbors = kg_service.get_neighbors(eid)
                results.append(f"**Relationships for {center_name}:**")
                
                if not neighbors:
                    results.append("  (No recorded relationships found in the knowledge graph)")
                else:
                    for n in neighbors:
                        rel_type = n.get("_edge_type", "related to")
                        target = n.get("name", n.get("id", "Unknown"))
                        results.append(f"  - **{rel_type.replace('_', ' ').title()}**: {target}")
                results.append("")
                
            return "\n".join(results)
            
        registry["relationship"] = relationship_tool

    # ── WORLD_SUMMARY: compile world state ───────────────────────
    if kg_service:
        def world_summary_tool(content: str, entity_ids: List[str], **kwargs) -> str:
            chars = kg_service.find_containers(container_type="character")
            locs = kg_service.find_containers(container_type="location")
            scenes = kg_service.find_containers(container_type="scene")
            factions = kg_service.find_containers(container_type="faction")
            
            summary = [
                "🌍 **World Summary**",
                f"**Characters:** {len(chars)} | **Locations:** {len(locs)} | **Factions:** {len(factions)} | **Scenes:** {len(scenes)}",
                "",
                "**Key Characters:**",
            ]
            
            for c in chars[:5]:
                summary.append(f"  - {c.get('name')}")
            if len(chars) > 5:
                summary.append(f"  - *...and {len(chars) - 5} more*")
                
            summary.append("\n**Key Locations:**")
            for l in locs[:5]:
                summary.append(f"  - {l.get('name')}")
            if len(locs) > 5:
                summary.append(f"  - *...and {len(locs) - 5} more*")
                
            summary.append("\n**Factions / Groups:**")
            if factions:
                for f in factions[:3]:
                    summary.append(f"  - {f.get('name')}")
            else:
                summary.append("  - (None defined yet)")
                
            return "\n".join(summary)
            
        registry["world_summary"] = world_summary_tool

    # ── PIPELINE: list or trigger pipelines ──────────────────────
    if pipeline_service:
        from showrunner_tool.schemas.chat import ChatEvent, ChatArtifact
        import json

        async def pipeline_tool(content: str, entity_ids: List[str], **kwargs):
            try:
                definitions = pipeline_service.list_definitions()
                
                content_lower = content.lower()

                import re
                override_match = re.search(r"(?:use|switch to)\s+([\w-]+(?:\.[\w-]+)*)", content_lower)
                if override_match and not any(cmd in content_lower for cmd in ["run ", "start ", "execute "]):
                    target_model = override_match.group(1).strip()
                    paused_run = None
                    for r in getattr(pipeline_service, '_runs', {}).values():
                        if getattr(r, 'current_state', None) and r.current_state.value == "PAUSED_FOR_USER":
                            paused_run = r
                            break
                    
                    if paused_run and getattr(paused_run, 'current_step_id', None):
                        pipeline_service.set_step_model_override(paused_run.id, paused_run.current_step_id, target_model)
                        yield f"Model override set: The next step will use **{target_model}**.\n\nPlease approve or resume the pipeline to continue."
                        return
                    elif override_match:
                        yield "Could not find a paused pipeline step to apply the model override to."
                        return

                run_trigger = False
                target_name = ""
                extra_text = ""
                
                for prefix in ["run pipeline ", "start pipeline ", "execute pipeline ", "run ", "start ", "execute "]:
                    if content_lower.startswith(prefix):
                        run_trigger = True
                        remainder = content_lower[len(prefix):].strip()
                        # Try to match a definition name at the start of the remainder
                        for d in definitions:
                            dname = getattr(d, "name", "").lower()
                            if remainder.startswith(dname):
                                target_name = dname
                                extra_text = remainder[len(dname):].strip()
                                # Handle optional "with" or "for" connectors
                                if extra_text.startswith("with "):
                                    extra_text = extra_text[5:]
                                elif extra_text.startswith("for "):
                                    extra_text = extra_text[4:]
                                break
                        
                        # If no direct match, assume the whole remainder is the target name
                        if not target_name:
                            target_name = remainder
                        break
                
                if run_trigger and target_name:
                    target_def = next((d for d in definitions if getattr(d, "name", "").lower() == target_name or getattr(d, "id", "") == target_name), None)
                    
                    if target_def:
                        yield f"Starting pipeline: **{target_def.name}**...\n\n"
                        payload = {"prompt_text": extra_text or content, "text": extra_text or content}
                        
                        # Add any specified entities to payload pinned context
                        if entity_ids:
                            payload["pinned_context_ids"] = entity_ids

                        from showrunner_tool.services.job_service import JobService
                        job = JobService.create_job(job_type="pipeline", payload={"definition_id": target_def.id, "run_id": None})
                        
                        run_id = await pipeline_service.start_pipeline(payload, definition_id=target_def.id)
                        JobService.update_job(job.id, status="running", message=f"Pipeline {target_def.name} running...", result={"run_id": run_id})
                        
                        # Emit a special artifact that the frontend will render as an interactive pipeline viewer
                        yield ChatEvent(
                            event_type="artifact",
                            data=ChatArtifact(
                                artifact_type="pipeline_run",
                                title=f"Pipeline: {target_def.name}",
                                content=json.dumps({"run_id": run_id}),
                            ).model_dump()
                        )
                        return
                    else:
                        yield f"Could not find a pipeline named '{target_name}'.\n\n"

                # List pipelines
                if not definitions:
                    yield "No pipeline definitions found. Create one in the Pipeline Builder."
                    return

                lines = ["Available pipelines:\n"]
                for d in definitions[:10]:
                    name = getattr(d, "name", None) or getattr(d, "id", "?")
                    steps = len(getattr(d, "steps", []))
                    lines.append(f"  - **{name}** ({steps} steps)")
                lines.append("\nTo run one, say: `run pipeline <name>`")
                yield "\n".join(lines)
            except Exception as e:
                yield f"Pipeline service error: {e}"

        registry["pipeline"] = pipeline_tool

    # ── PLAUSIBILITY_CHECK: verify text against research ────────────────────────
    if kg_service:
        from showrunner_tool.schemas.chat import ChatEvent
        async def plausibility_check_tool(content: str, entity_ids: List[str], **kwargs):
            session_id = kwargs.get("session_id")
            context_manager = kwargs.get("context_manager")
            
            research_text = ""
            scene_text = content
            
            if session_id and context_manager:
                context = context_manager.build_context(session_id)
                system_context = context.get("system_context", "")
                if "Research Notes" in system_context:
                    research_text = system_context.split("Research Notes")[-1]
                
            if not research_text:
                try:
                    r_containers = kg_service.find_containers(container_type="research")
                    if r_containers:
                        research_text = "\n".join([str(c.get("attributes", {})) for c in r_containers])
                except Exception:
                    pass

            if not research_text:
                yield "No research buckets found to verify plausibility against."
                return

            yield ChatEvent(
                event_type="action_trace",
                data={"tool_name": "plausibility_check", "context_summary": "Cross-referencing text against research..."}
            )

            import litellm
            
            system_prompt = (
                "You are an expert fact-checker and narrative continuity editor. "
                "Analyze the provided scene excerpt against the provided Research Notes. "
                "1. Extract any concrete claims, facts, or descriptions from the excerpt. "
                "2. Compare them strictly against the Research Notes. "
                "3. Flag any implausible claims, contradictions, or unrealistic elements. "
                "Format as a concise markdown list of bullet points explaining WHY they are implausible. "
                "If everything appears plausible based on the research, state that no issues were found."
            )
            
            user_prompt = f"### Research Notes\n{research_text}\n\n### Excerpt to check\n{scene_text}"

            try:
                response = await litellm.acompletion(
                    model="gemini/gemini-2.0-flash",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                )
                yield response.choices[0].message.content.strip()
            except Exception as e:
                yield f"Plausibility check failed: {e}"

        registry["plausibility_check"] = plausibility_check_tool

    # ── SAVE_TO_MEMORY: auto-extract facts ──────────────
    if container_repo and kg_service:
        def save_to_memory_tool(content: str, entity_ids: List[str], **kwargs) -> str:
            import uuid
            from showrunner_tool.schemas.container import GenericContainer
            
            # Use LLM to extract the core fact to keep it clean
            try:
                import litellm
                system_prompt = (
                    "You are a Memory Extraction agent for a creative writing AI. "
                    "Extract the core, immutable fact or lore decision from the user's statement. "
                    "Keep it incredibly concise, like a wiki fact. Remove conversational filler."
                )
                response = litellm.completion(
                    model="gemini/gemini-2.5-flash",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content}
                    ],
                    max_tokens=150,
                )
                fact_str = response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"Memory extraction summarization failed: {e}")
                fact_str = content.strip()

            c = GenericContainer(
                id=str(uuid.uuid4()),
                name=f"Fact: {fact_str[:30]}...",
                container_type="project_memory",
                attributes={
                    "fact": fact_str,
                    "source": "auto_memory_trigger"
                },
                project_path=project_path,
                era_id=kwargs.get("era_id")
            )
            container_repo.save_container(c)
            
            return (
                f"Memory Triggered. Saved to Project Lore:\n"
                f"> {fact_str}\n\n"
                "This will prioritize across all future context windows."
            )

        registry["save_to_memory"] = save_to_memory_tool

    # ── DECIDE: record a policy or lore decision ───────────────
    if project_memory_service:
        def decide_tool(content: str, entity_ids: List[str], **kwargs) -> str:
            # Clean up content
            text = content.strip()
            if text.lower().startswith("remember that "):
                text = text[len("remember that "):].strip()
            
            # Simple key derivation for now
            key = text[:50].lower().replace(" ", "_")
            project_memory_service.add_entry(key=key, value=text)
            
            return (
                f"Decision recorded: **{key}**\n\n"
                f"I will remember this preference for future generations."
            )

        registry["decide"] = decide_tool

    return registry
