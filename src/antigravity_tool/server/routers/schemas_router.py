"""Schemas router -- CRUD for ContainerSchema and NL generation."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

import litellm
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ValidationError

from antigravity_tool.repositories.container_repo import SchemaRepository
from antigravity_tool.schemas.container import ContainerSchema, FieldDefinition
from antigravity_tool.server.deps import get_schema_repo

router = APIRouter(prefix="/api/v1/schemas", tags=["schemas"])

# ── Request / Response models ──────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str


class ValidateRequest(BaseModel):
    payload: Dict[str, Any]


# ── Helpers ────────────────────────────────────────────────────────────

def _load_wizard_system_prompt() -> str:
    """Load the schema wizard system prompt, stripping YAML frontmatter."""
    from pathlib import Path

    wizard_path = Path(__file__).resolve().parents[4] / "agents" / "skills" / "schema_wizard.md"
    text = wizard_path.read_text()
    # Strip YAML frontmatter (--- ... ---)
    text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)
    return text.strip()


def _schema_to_dict(schema: ContainerSchema) -> dict:
    return schema.model_dump(mode="json")


# ── CRUD endpoints ─────────────────────────────────────────────────────

@router.get("/", response_model=List[dict])
async def list_schemas(repo: SchemaRepository = Depends(get_schema_repo)):
    """List all schemas."""
    files = repo._list_files()
    schemas = [repo._load_file(f) for f in files]
    return [_schema_to_dict(s) for s in schemas]


@router.get("/{name}")
async def get_schema(name: str, repo: SchemaRepository = Depends(get_schema_repo)):
    """Get a single schema by name."""
    schema = repo.get_by_name(name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Schema '{name}' not found")
    return _schema_to_dict(schema)


@router.post("/", status_code=201)
async def create_schema(
    schema: ContainerSchema,
    repo: SchemaRepository = Depends(get_schema_repo),
):
    """Create a new schema."""
    existing = repo.get_by_name(schema.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Schema '{schema.name}' already exists")
    path = repo._save_file(repo.base_dir / f"{schema.name}.yaml", schema)
    return _schema_to_dict(schema)


@router.put("/{name}")
async def update_schema(
    name: str,
    schema: ContainerSchema,
    repo: SchemaRepository = Depends(get_schema_repo),
):
    """Update an existing schema."""
    existing = repo.get_by_name(name)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Schema '{name}' not found")
    # If the name changed, delete the old file
    if schema.name != name:
        repo.delete(name)
    repo._save_file(repo.base_dir / f"{schema.name}.yaml", schema)
    return _schema_to_dict(schema)


@router.delete("/{name}", status_code=204)
async def delete_schema(
    name: str,
    repo: SchemaRepository = Depends(get_schema_repo),
):
    """Delete a schema by name."""
    existing = repo.get_by_name(name)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Schema '{name}' not found")
    repo.delete(name)


# ── Generate (NL → Schema via LLM) ────────────────────────────────────

@router.post("/generate")
async def generate_schema(
    req: GenerateRequest,
    repo: SchemaRepository = Depends(get_schema_repo),
):
    """Generate a ContainerSchema from a natural language prompt via the Schema Wizard agent."""
    system_prompt = _load_wizard_system_prompt()

    try:
        response = await litellm.acompletion(
            model="gemini/gemini-2.0-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.prompt},
            ],
            response_format={"type": "json_object"},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"LLM returned invalid JSON: {e}")

    # Map the LLM output keys to ContainerSchema fields
    try:
        fields = [FieldDefinition(**f) for f in data.get("fields", [])]
        draft = ContainerSchema(
            name=data.get("container_type", "unnamed"),
            display_name=data.get("display_name", data.get("container_type", "Unnamed")),
            description=data.get("description"),
            fields=fields,
        )
    except ValidationError as e:
        raise HTTPException(status_code=502, detail=f"LLM output failed schema validation: {e}")

    return _schema_to_dict(draft)


# ── Validate payload against dynamic model ─────────────────────────────

@router.post("/{name}/validate")
async def validate_payload(
    name: str,
    req: ValidateRequest,
    repo: SchemaRepository = Depends(get_schema_repo),
):
    """Validate a sample payload against the dynamic Pydantic model for a schema."""
    schema = repo.get_by_name(name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Schema '{name}' not found")

    DynamicModel = schema.to_pydantic_model()
    try:
        instance = DynamicModel(**req.payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    return {"valid": True, "parsed": instance.model_dump(mode="json")}
