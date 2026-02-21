# Prompt: Phase Next-C/D Session C — Workflow Templates + Research Agent UI

**Goal**: Wire end-to-end workflow templates that actually execute, and build a dedicated Research UI surface for querying, browsing, and linking research to story elements.

**Context**:
Showrunner is a CLI + FastAPI + Next.js platform for AI-assisted manga/manhwa creation. The Pipeline Builder (`/pipelines`) has a visual DAG editor with a TemplateGallery component that shows hardcoded stub templates. The Research Agent backend exists (`research_service.py` + `research.py` router) with query/library/topic endpoints but has no dedicated frontend UI.

This session completes two features:
1. **Workflow Templates Library** — 5 ready-to-use templates that actually work end-to-end when clicked
2. **Research Agent UI Surface** — Dedicated research panel/page for searching, querying, viewing results, and linking research to scenes

**Read these files first** (essential context):
- `docs/PRD.md` §13 — Phase Next-D description
- `src/antigravity_tool/services/pipeline_service.py` — Pipeline execution (1273 lines). Pay attention to step handlers and how definitions are saved/run.
- `src/antigravity_tool/schemas/pipeline_steps.py` — StepType enum (14 types), STEP_REGISTRY, PipelineStepDef, PipelineDefinition (298 lines)
- `src/web/src/components/pipeline-builder/TemplateGallery.tsx` — Current gallery component (136 lines)
- `src/web/src/components/pipeline-builder/PipelineBuilder.tsx` — Pipeline builder layout
- `src/antigravity_tool/services/research_service.py` — Current research service (191 lines)
- `src/antigravity_tool/server/routers/research.py` — Research endpoints (49 lines)
- `src/web/src/lib/api.ts` — API client patterns
- `src/web/src/app/pipelines/page.tsx` — Pipeline page
- `src/antigravity_tool/server/routers/pipeline.py` — Pipeline run/definition endpoints

---

## Feature 1: Workflow Templates Library

### Backend

**1. Create `src/antigravity_tool/templates/workflow_templates.py`**

Define 5 ready-to-use PipelineDefinition objects as Python data:

```python
WORKFLOW_TEMPLATES = {
    "scene_to_panels": {
        "name": "Scene → Panels",
        "description": "Gather scene context, compose image prompts, and generate storyboard panels",
        "category": "production",
        "steps": [
            {"id": "gather", "step_type": "gather_buckets", "label": "Gather Scene Context",
             "config": {"container_types": ["character", "scene", "location"], "max_items": 10},
             "position": {"x": 100, "y": 200}},
            {"id": "prompt", "step_type": "prompt_template", "label": "Compose Panel Prompts",
             "config": {"template": "Based on this scene context:\n\n{{context}}\n\nGenerate detailed panel descriptions for a manga/webtoon scene. Include camera angles, character positions, and visual mood."},
             "position": {"x": 400, "y": 200}},
            {"id": "review", "step_type": "review_prompt", "label": "Review Prompts",
             "config": {},
             "position": {"x": 700, "y": 200}},
            {"id": "generate", "step_type": "llm_generate", "label": "Generate Panel Descriptions",
             "config": {"model": "", "temperature": 0.8, "max_tokens": 4096},
             "position": {"x": 1000, "y": 200}},
            {"id": "save", "step_type": "save_to_bucket", "label": "Save Panels",
             "config": {"container_type": "panel"},
             "position": {"x": 1300, "y": 200}},
        ],
        "edges": [
            {"source": "gather", "target": "prompt"},
            {"source": "prompt", "target": "review"},
            {"source": "review", "target": "generate"},
            {"source": "generate", "target": "save"},
        ]
    },
    "concept_to_outline": {
        "name": "Concept → Outline",
        "description": "Brainstorm ideas from a concept, then architect a structured story outline",
        "category": "writing",
        "steps": [
            {"id": "input", "step_type": "review_prompt", "label": "Enter Your Concept",
             "config": {},
             "position": {"x": 100, "y": 200}},
            {"id": "brainstorm", "step_type": "llm_generate", "label": "Brainstorm Ideas",
             "config": {"model": "", "temperature": 1.0, "max_tokens": 2048},
             "position": {"x": 400, "y": 200}},
            {"id": "review_ideas", "step_type": "review_prompt", "label": "Review Ideas",
             "config": {},
             "position": {"x": 700, "y": 200}},
            {"id": "architect", "step_type": "llm_generate", "label": "Build Story Outline",
             "config": {"model": "", "temperature": 0.7, "max_tokens": 4096},
             "position": {"x": 1000, "y": 200}},
            {"id": "approve", "step_type": "approve_output", "label": "Approve Outline",
             "config": {},
             "position": {"x": 1300, "y": 200}},
            {"id": "save", "step_type": "save_to_bucket", "label": "Save Outline",
             "config": {"container_type": "outline"},
             "position": {"x": 1600, "y": 200}},
        ],
        "edges": [
            {"source": "input", "target": "brainstorm"},
            {"source": "brainstorm", "target": "review_ideas"},
            {"source": "review_ideas", "target": "architect"},
            {"source": "architect", "target": "approve"},
            {"source": "approve", "target": "save"},
        ]
    },
    "outline_to_draft": {
        "name": "Outline → Draft",
        "description": "Gather context from outline and characters, generate prose draft, extract entities",
        "category": "writing",
        "steps": [
            {"id": "gather", "step_type": "gather_buckets", "label": "Gather Story Context",
             "config": {"container_types": ["character", "scene", "outline", "location"], "max_items": 15},
             "position": {"x": 100, "y": 200}},
            {"id": "prompt", "step_type": "prompt_template", "label": "Compose Writing Prompt",
             "config": {"template": "You are a skilled prose writer. Using the following story context:\n\n{{context}}\n\nWrite a vivid, engaging scene draft. Focus on:\n- Show don't tell\n- Character voice consistency\n- Sensory details\n- Natural dialogue"},
             "position": {"x": 400, "y": 200}},
            {"id": "review", "step_type": "review_prompt", "label": "Review Writing Prompt",
             "config": {},
             "position": {"x": 700, "y": 200}},
            {"id": "draft", "step_type": "llm_generate", "label": "Generate Draft",
             "config": {"model": "", "temperature": 0.85, "max_tokens": 8192},
             "position": {"x": 1000, "y": 200}},
            {"id": "save", "step_type": "save_to_bucket", "label": "Save Fragment",
             "config": {"container_type": "fragment"},
             "position": {"x": 1300, "y": 200}},
        ],
        "edges": [
            {"source": "gather", "target": "prompt"},
            {"source": "prompt", "target": "review"},
            {"source": "review", "target": "draft"},
            {"source": "draft", "target": "save"},
        ]
    },
    "topic_to_research": {
        "name": "Topic → Research",
        "description": "Deep-dive into a real-world topic and save structured findings to the Research Library",
        "category": "research",
        "steps": [
            {"id": "input", "step_type": "review_prompt", "label": "Enter Research Topic",
             "config": {},
             "position": {"x": 100, "y": 200}},
            {"id": "research", "step_type": "research_deep_dive", "label": "Research Deep Dive",
             "config": {},
             "position": {"x": 400, "y": 200}},
            {"id": "review", "step_type": "approve_output", "label": "Review Findings",
             "config": {},
             "position": {"x": 700, "y": 200}},
            {"id": "save", "step_type": "save_to_bucket", "label": "Save to Library",
             "config": {"container_type": "research_topic"},
             "position": {"x": 1000, "y": 200}},
        ],
        "edges": [
            {"source": "input", "target": "research"},
            {"source": "research", "target": "review"},
            {"source": "review", "target": "save"},
        ]
    },
    "draft_to_polish": {
        "name": "Draft → Polish",
        "description": "Review draft for style consistency, check continuity, and produce final edit",
        "category": "quality",
        "steps": [
            {"id": "gather", "step_type": "gather_buckets", "label": "Gather Draft + Style Guide",
             "config": {"container_types": ["fragment", "character"], "max_items": 10},
             "position": {"x": 100, "y": 200}},
            {"id": "style_check", "step_type": "llm_generate", "label": "Style & Voice Check",
             "config": {"model": "", "temperature": 0.3, "max_tokens": 4096},
             "position": {"x": 400, "y": 200}},
            {"id": "review_style", "step_type": "review_prompt", "label": "Review Style Notes",
             "config": {},
             "position": {"x": 700, "y": 200}},
            {"id": "final_edit", "step_type": "llm_generate", "label": "Final Polish",
             "config": {"model": "", "temperature": 0.5, "max_tokens": 8192},
             "position": {"x": 1000, "y": 200}},
            {"id": "approve", "step_type": "approve_output", "label": "Approve Final",
             "config": {},
             "position": {"x": 1300, "y": 200}},
            {"id": "save", "step_type": "save_to_bucket", "label": "Save Polished Draft",
             "config": {"container_type": "fragment"},
             "position": {"x": 1600, "y": 200}},
        ],
        "edges": [
            {"source": "gather", "target": "style_check"},
            {"source": "style_check", "target": "review_style"},
            {"source": "review_style", "target": "final_edit"},
            {"source": "final_edit", "target": "approve"},
            {"source": "approve", "target": "save"},
        ]
    }
}
```

**2. Add templates endpoint to pipeline router**

```python
@router.get("/templates")
async def get_workflow_templates() -> list[dict]:
    """Return available workflow templates."""
```

This returns the WORKFLOW_TEMPLATES dict as a list, each with an added `template_id` key.

**3. Add "create from template" endpoint**

```python
@router.post("/templates/{template_id}/create")
async def create_from_template(
    template_id: str,
    svc: PipelineService = Depends(get_pipeline_service),
) -> PipelineDefinitionResponse:
    """Create a new PipelineDefinition from a template."""
```

This copies the template into a new PipelineDefinition, saves it via `svc.save_definition()`, and returns it.

### Frontend

**4. Replace hardcoded templates in `workflowTemplates.ts`**

Find/create `src/web/src/lib/workflowTemplates.ts` and make it fetch from the API instead of hardcoding. Or modify `TemplateGallery.tsx` to fetch templates from `api.getWorkflowTemplates()`.

**5. Update `TemplateGallery.tsx`**

- Fetch templates from `GET /api/pipeline/templates` on mount
- "Use Template" button calls `POST /api/pipeline/templates/{id}/create`
- After creation, navigate to the pipeline builder with the new definition loaded
- Show template step count and description
- Keep existing category color coding

**6. Add API client methods**

```typescript
getWorkflowTemplates: () =>
  request<WorkflowTemplate[]>("/api/pipeline/templates"),
createFromTemplate: (templateId: string) =>
  post<any>(`/api/pipeline/templates/${encodeURIComponent(templateId)}/create`),
```

---

## Feature 2: Research Agent UI Surface

### Frontend (Primary — Backend Already Exists)

**7. Create `src/web/src/app/research/page.tsx`**

A dedicated research page at `/research`:

```
┌──────────────────────────────────────────────────────────┐
│ Research Library                    [New Research Query]   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Search: [_________________________] 🔍                   │
│                                                           │
│  ┌─────────────────────┐  ┌─────────────────────────────┐│
│  │ Research Topics      │  │ Topic Detail                ││
│  │                      │  │                             ││
│  │ ▸ Railgun Physics   │  │ Railgun Physics in Low G    ││
│  │   ★★★★☆ (high)     │  │ Category: Physics/Weapons   ││
│  │                      │  │ Confidence: High ★★★★☆     ││
│  │ ▸ Orbital Mechanics │  │                             ││
│  │   ★★★☆☆ (medium)   │  │ Summary:                    ││
│  │                      │  │ In low gravity, railgun...  ││
│  │ ▸ Medieval Armor    │  │                             ││
│  │   ★★★★★ (high)     │  │ Key Facts:                  ││
│  │                      │  │ • Projectile velocity un... ││
│  │                      │  │ • Trajectory curves less... ││
│  │                      │  │                             ││
│  │                      │  │ Constraints:                ││
│  │                      │  │ • Shooter pushed backward   ││
│  │                      │  │                             ││
│  │                      │  │ Story Implications:         ││
│  │                      │  │ • Combat at longer ranges   ││
│  │                      │  │                             ││
│  │                      │  │ [Link to Scene ▼] [Delete]  ││
│  └─────────────────────┘  └─────────────────────────────┘│
│                                                           │
│  New Research Query:                                      │
│  [How would a railgun work in low gravity?        ] [Go]  │
│  [Researching...]  ████████░░ (spinner during LLM call)   │
└──────────────────────────────────────────────────────────┘
```

Requirements:
- **Left panel**: Research topic list
  - Fetched from `GET /api/v1/research/library`
  - Each item shows name + confidence stars
  - Click to view detail in right panel
  - Search/filter input at top
- **Right panel**: Selected topic detail
  - Full structured display: summary, key_facts (bullet list), constraints, story_implications
  - Confidence badge with stars
  - "Link to Scene" dropdown — lists available scenes, creates a KG relationship
  - "Delete" button with confirmation
- **Bottom**: New research query input
  - Text input + "Research" button
  - Calls `POST /api/v1/research/query`
  - Shows loading spinner during LLM agent execution
  - On completion, adds to topic list and selects it
  - Toast notification on success/error
- Follow dark theme styling

**8. Create `src/web/src/components/research/ResearchTopicCard.tsx`**

List item component for the left panel:
- Topic name, confidence indicator (star rating or color badge)
- Truncated summary preview
- Click handler to select

**9. Create `src/web/src/components/research/ResearchDetailPanel.tsx`**

Right panel component showing full topic detail:
- Structured sections: Summary, Key Facts, Constraints, Story Implications
- Confidence badge
- Sources list (if available)
- "Link to Scene" action:
  - Dropdown of available scenes (fetch from `api.getScenes(chapter)`)
  - On select, create a relationship via `api.updateContainer(researchId, { relationships: [..., { target_id: sceneId, type: "references" }] })`
  - Toast: "Linked to Scene X"
- "Delete" button with ConfirmDialog

**10. Add API client methods (some may already exist)**

Ensure these exist in `api.ts`:
```typescript
// Research (verify these exist, add if missing)
queryResearch: (query: string) =>
  post<ResearchResult>("/api/v1/research/query", { query }),
getResearchLibrary: () =>
  request<ResearchLibraryResponse>("/api/v1/research/library"),
getResearchTopic: (id: string) =>
  request<ResearchResult>(`/api/v1/research/library/${encodeURIComponent(id)}`),
```

Add TypeScript interfaces:
```typescript
export interface ResearchResult {
  id: string;
  name: string;
  original_query: string;
  summary: string;
  confidence_score: string;
  key_facts: string[];
  constraints: string[];
  story_implications: string[];
  sources: string[];
}

export interface ResearchLibraryResponse {
  items: ResearchResult[];
  total: number;
}
```

**11. Add navigation link**

Add `/research` link in the Canvas.tsx header nav bar (alongside Zen, Pipelines, Storyboard):
```tsx
<a href="/research" className="px-3 py-1 text-xs font-medium rounded-md text-gray-500 hover:text-gray-300">
  Research
</a>
```

---

## Output Specification

Provide the complete code for:
1. `src/antigravity_tool/templates/workflow_templates.py` (new file — 5 templates)
2. Updates to `src/antigravity_tool/server/routers/pipeline.py` (add templates + create-from-template endpoints)
3. Updates to `src/web/src/components/pipeline-builder/TemplateGallery.tsx` (fetch from API)
4. Updates to `src/web/src/lib/api.ts` (add template + research methods + interfaces)
5. `src/web/src/app/research/page.tsx` (new file)
6. `src/web/src/components/research/ResearchTopicCard.tsx` (new file)
7. `src/web/src/components/research/ResearchDetailPanel.tsx` (new file)
8. Updates to `src/web/src/components/workbench/Canvas.tsx` (add Research nav link)
9. Any necessary updates to `src/antigravity_tool/server/api_schemas.py` for template response types

---

## Important Notes

- **Parallel sessions are implementing Panel Layout Intelligence + Approval Gate (Session 22) and Character Progressions + Reader Sim (Session 23).** Do NOT modify StoryboardService, SceneStrip, PromptReviewModal, CharacterInspector, or the `/preview` route.
- The Research backend (`research_service.py` + `research.py` router) already exists and works. The main work here is building the frontend UI.
- For workflow templates, the key insight is that `PipelineService` already handles all these step types. The templates just need to be valid `PipelineDefinition` objects.
- The `workflowTemplates.ts` file may contain hardcoded data — replace it with API fetching.
- Use `toast.success()` / `toast.error()` from `sonner`.
- Use confirmation dialogs (the `ConfirmDialog` component already exists at `src/web/src/components/ui/ConfirmDialog.tsx`) for delete actions.
- Run `cd src/web && npx tsc --noEmit` to verify TypeScript compiles.
