# Coding Task: Schema CRUD Router & NL Generation (Phase 6 Backend)

**Context:** We are building "Showrunner", an AI co-writer. Users need to create custom entity types ("Spell", "Spaceship") without code. The backend already has:
- `ContainerSchema` and `FieldDefinition` Pydantic models in `src/showrunner_tool/schemas/container.py`
- `SchemaRepository` in `src/showrunner_tool/repositories/container_repo.py` that persists schemas as YAML files in `/schemas/`
- A `FieldType` enum with 6 types (`string`, `integer`, `float`, `boolean`, `list[string]`, `json`)

**Your Objective: Write the Python Backend Code**

### 1. Extend `FieldType` enum and `FieldDefinition` (in `schemas/container.py`)
Add two new types:
- `ENUM = "enum"` → maps to `Literal[...]` with an `options: Optional[List[str]]` field on `FieldDefinition`
- `REFERENCE = "reference"` → maps to `str` (UUID) with a `target_type: Optional[str]` field on `FieldDefinition`

Update `ContainerSchema.to_pydantic_model()` to handle these two new types properly (use `Literal` for enum, `str` for reference).

### 2. Create Schema CRUD Router (new file: `src/showrunner_tool/server/routers/schemas_router.py`)
Implement these 7 endpoints:
```
GET    /api/v1/schemas/                → List all schemas
GET    /api/v1/schemas/{name}          → Get one schema
POST   /api/v1/schemas/               → Create a schema
PUT    /api/v1/schemas/{name}          → Update a schema
DELETE /api/v1/schemas/{name}          → Delete a schema
POST   /api/v1/schemas/generate        → NL prompt → Schema Wizard Agent (LLM call via litellm)
POST   /api/v1/schemas/{name}/validate → Validate a sample payload against the dynamic Pydantic model
```

For the `/generate` endpoint:
- Accept `{ "prompt": "A spaceship tracking fuel and captain" }`
- Load the system prompt from `agents/skills/schema_wizard.md` (strip the YAML frontmatter)
- Call `litellm.completion()` with the system prompt + user prompt
- Parse the JSON response into a `ContainerSchema` object
- Return it as a draft (unsaved)

### 3. Mount the router
Add the router to the main FastAPI app.

**Output:** Provide the exact, production-ready Python code for the modified `container.py` and the new `schemas_router.py`.
