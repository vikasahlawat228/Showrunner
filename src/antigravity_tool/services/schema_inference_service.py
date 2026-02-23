"""Schema Inference Service — detects patterns across schema-less containers
and suggests formal ContainerSchema definitions.

Also provides LLM-powered text extraction to create GenericContainers from
unstructured prose snippets (drag-and-drop worldbuilding).
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

import litellm

from antigravity_tool.repositories.container_repo import ContainerRepository, SchemaRepository
from antigravity_tool.schemas.container import ContainerSchema, FieldDefinition, FieldType, GenericContainer

logger = logging.getLogger(__name__)

# ── Extraction prompt ────────────────────────────────────────────────

_EXTRACT_SYSTEM_PROMPT = """\
You are a worldbuilding assistant for a creative writing tool.
The user will give you a short snippet of prose / lore from their manuscript.

Your job is to extract structured data from it and return a JSON object with:
  - "name": A short descriptive name for the entity/concept (2-5 words).
  - "container_type": One of "lore", "character", "location", "item", "faction",
    "concept", "event", "rule". Pick the best fit.
  - "attributes": A flat JSON object of key-value pairs that capture the
    important facts.  Keys should be snake_case identifiers.  Values should be
    short strings, numbers, or lists of strings.
  - "tags": A list of 1-4 hashtag-style labels (e.g. ["#magic-system", "#act1"]).
  - "relationships": (optional) A list of objects with "target_name" and "type"
    for any other entities referenced.

Rules:
- Be concise. Attribute keys must be descriptive (e.g. "power_source",
  "allegiance", "weakness").
- If the text is too vague to extract structured data, still return a
  best-effort result with at least a name, type, and one attribute.
- Return ONLY valid JSON, no markdown.
"""


# ── Inference prompt ────────────────────────────────────────────────

_INFER_SCHEMA_PROMPT = """\
You are a data-modelling assistant.
Given a set of container instances that share a common `container_type`,
analyse their attribute keys and types and propose a formal schema.

Return a JSON object with:
  - "name": The schema name matching the container_type.
  - "display_name": A human-friendly name.
  - "description": One-sentence description of the schema.
  - "fields": Array of field definitions, each with:
      - "name": snake_case field name
      - "field_type": one of "string", "integer", "float", "boolean",
        "list[string]", "json", "enum", "reference"
      - "description": one-line purpose
      - "required": boolean
      - "options": (only for enum) list of allowed values
  - "confidence": float 0.0-1.0 indicating how confident you are.

Return ONLY valid JSON.
"""


class SchemaInferenceService:
    """Analyses schema-less GenericContainers and suggests formal schemas."""

    def __init__(
        self,
        container_repo: ContainerRepository,
        schema_repo: SchemaRepository,
    ):
        self.container_repo = container_repo
        self.schema_repo = schema_repo

    # ------------------------------------------------------------------
    # Text → Container extraction (used by drag-and-drop endpoint)
    # ------------------------------------------------------------------

    async def extract_container_from_text(self, text: str) -> GenericContainer:
        """Use an LLM to parse a prose snippet into a GenericContainer."""
        try:
            response = await litellm.acompletion(
                model="gemini/gemini-2.0-flash",
                messages=[
                    {"role": "system", "content": _EXTRACT_SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
            )
        except Exception as e:
            logger.error("LLM extraction failed: %s", e)
            # Fallback: create a bare lore bucket with the raw text
            return GenericContainer(
                container_type="lore",
                name=text[:60].strip().replace("\n", " "),
                attributes={"raw_text": text},
                tags=["#auto-extracted"],
            )

        raw = response.choices[0].message.content
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Strip markdown fences if present
            cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`")
            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError:
                data = {}

        container = GenericContainer(
            container_type=data.get("container_type", "lore"),
            name=data.get("name", text[:60].strip()),
            attributes=data.get("attributes", {"raw_text": text}),
            tags=data.get("tags", ["#auto-extracted"]),
        )

        # Attach relationships if extracted
        for rel in data.get("relationships", []):
            if isinstance(rel, dict) and "target_name" in rel:
                container.relationships.append({
                    "target_id": rel["target_name"],  # resolved later
                    "type": rel.get("type", "related_to"),
                })

        # Keep original text as a source attribute
        container.attributes["_source_text"] = text

        return container

    # ------------------------------------------------------------------
    # Schema inference from existing containers
    # ------------------------------------------------------------------

    def _gather_unschematised_containers(self) -> Dict[str, List[GenericContainer]]:
        """Group containers by container_type, excluding those with formal schemas."""
        existing_schemas = {s.name for s in self._list_schemas()}
        buckets: Dict[str, List[GenericContainer]] = defaultdict(list)

        all_containers = self.container_repo.list_all()
        for c in all_containers:
            if c.container_type not in existing_schemas and c.attributes:
                buckets[c.container_type].append(c)

        return buckets

    def _list_schemas(self) -> List[ContainerSchema]:
        """Load all existing schemas from the repo."""
        files = self.schema_repo._list_files()
        return [self.schema_repo._load_file(f) for f in files]

    def analyze_unstructured_containers(self) -> List[Dict[str, Any]]:
        """Heuristic analysis — find container_types with ≥2 instances
        sharing similar attribute keys and propose a schema.

        Returns a list of suggestion dicts (one per proposed schema).
        """
        buckets = self._gather_unschematised_containers()
        suggestions: List[Dict[str, Any]] = []

        for ctype, containers in buckets.items():
            if len(containers) < 2:
                continue

            # Collect attribute key frequencies
            key_counter: Counter = Counter()
            for c in containers:
                key_counter.update(c.attributes.keys())

            # Keys appearing in ≥50 % of containers are "common"
            threshold = len(containers) * 0.5
            common_keys = [k for k, count in key_counter.items() if count >= threshold]

            if not common_keys:
                continue

            # Infer simple types from values
            inferred_fields: List[Dict[str, Any]] = []
            for key in common_keys:
                if key.startswith("_"):
                    continue  # skip internal keys
                sample_values = [
                    c.attributes[key]
                    for c in containers
                    if key in c.attributes
                ]
                field_type = _infer_field_type(sample_values)
                inferred_fields.append({
                    "name": key,
                    "field_type": field_type,
                    "required": key_counter[key] >= len(containers) * 0.8,
                    "description": "",
                })

            suggestions.append({
                "container_type": ctype,
                "instance_count": len(containers),
                "common_keys": common_keys,
                "inferred_fields": inferred_fields,
                "sample_names": [c.name for c in containers[:5]],
            })

        return suggestions

    async def suggest_schema_from_containers(
        self, container_type: str
    ) -> Optional[Dict[str, Any]]:
        """Use an LLM to propose a formal schema for a specific container_type."""
        buckets = self._gather_unschematised_containers()
        containers = buckets.get(container_type)
        if not containers or len(containers) < 2:
            return None

        # Build a sample payload for the LLM
        samples = []
        for c in containers[:8]:
            samples.append({"name": c.name, "attributes": c.attributes})

        prompt = (
            f"Container type: {container_type}\n"
            f"Number of instances: {len(containers)}\n"
            f"Sample instances:\n{json.dumps(samples, indent=2, default=str)}"
        )

        try:
            response = await litellm.acompletion(
                model="gemini/gemini-2.0-flash",
                messages=[
                    {"role": "system", "content": _INFER_SCHEMA_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            data = json.loads(raw)
            return data
        except Exception as e:
            logger.error("Schema inference LLM call failed: %s", e)
            return None


# ── Helpers ──────────────────────────────────────────────────────────

def _infer_field_type(values: list) -> str:
    """Heuristically infer a FieldType string from sample values."""
    types_seen = set()
    for v in values:
        if isinstance(v, bool):
            types_seen.add("boolean")
        elif isinstance(v, int):
            types_seen.add("integer")
        elif isinstance(v, float):
            types_seen.add("float")
        elif isinstance(v, list):
            types_seen.add("list[string]")
        elif isinstance(v, dict):
            types_seen.add("json")
        else:
            types_seen.add("string")

    if len(types_seen) == 1:
        return types_seen.pop()
    if types_seen <= {"integer", "float"}:
        return "float"
    return "string"  # default fallback
