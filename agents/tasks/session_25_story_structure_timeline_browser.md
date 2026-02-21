# Prompt: Phase Next-E Session A — Story Structure Visual Editor + Alternate Timeline Browser

**Goal**: Build an interactive story structure tree editor with drag-to-reorder, create/delete nodes, and click-to-open-in-Zen. Also build an alternate timeline browser with branch listing, side-by-side comparison, and SSE streaming.

**Context**:
Showrunner is a CLI + FastAPI + Next.js platform for AI-assisted manga/manhwa creation. The codebase has 18 routers, 28 services, and a Next.js frontend with 8 pages. The Timeline page (`/timeline`) already has a `StoryStructureTree` component (386 lines) with drag-reorder UI and a `TimelinePanel` component (162 lines) with SVG branch visualization. However, several backend endpoints are missing, and the frontend tree has gaps (no create/delete, no open-in-Zen, backend reorder calls fail).

This session adds two features:
1. **Story Structure Visual Editor** — Fix backend gaps and enhance `StoryStructureTree` with create node, delete node, open-in-Zen, and completion status color-coding
2. **Alternate Timeline Browser** — Add branch listing, branch comparison, SSE streaming, and a side-by-side diff view

**Read these files first** (essential context):
- `src/antigravity_tool/server/routers/projects.py` — Current project router with `GET /structure` (124 lines)
- `src/antigravity_tool/schemas/project.py` — `StructureTreeNode`, `StructureTree` models (71 lines)
- `src/antigravity_tool/schemas/container.py` — `GenericContainer` with `parent_id`, `sort_order` (112 lines)
- `src/antigravity_tool/repositories/container_repo.py` — `ContainerRepository` (50 lines, needs new methods)
- `src/antigravity_tool/repositories/sqlite_indexer.py` — SQLite indexer with `get_children()`, `get_roots()` (227 lines)
- `src/antigravity_tool/repositories/event_sourcing_repo.py` — `EventService` with `branch()`, `project_state()`, `get_all_events()` (189 lines)
- `src/antigravity_tool/server/routers/timeline.py` — Timeline router (37 lines, only `/events` and `/checkout`)
- `src/antigravity_tool/services/knowledge_graph_service.py` — `get_structure_tree()` (262 lines)
- `src/antigravity_tool/server/deps.py` — DI graph
- `src/web/src/components/timeline/StoryStructureTree.tsx` — Existing tree with drag-reorder (386 lines)
- `src/web/src/components/timeline/TimelineView.tsx` — Timeline with SSE polling (199 lines)
- `src/web/src/components/timeline/TimelinePanel.tsx` — SVG branch visualization (162 lines)
- `src/web/src/app/timeline/page.tsx` — Timeline page layout (133 lines)
- `src/web/src/lib/api.ts` — API client (check `getProjectStructure`, `checkoutEvent`, `createBranch`)

---

## Feature 1: Story Structure Visual Editor

### Backend

**1. Create a containers router for CRUD operations**

Create `src/antigravity_tool/server/routers/containers.py` with prefix `/api/v1/containers`:

```
POST   /api/v1/containers                    → Create a new container (any type)
GET    /api/v1/containers/{container_id}     → Get container by ID
PUT    /api/v1/containers/{container_id}     → Update container (name, sort_order, attributes, parent_id)
DELETE /api/v1/containers/{container_id}     → Delete container + remove from KG
POST   /api/v1/containers/reorder            → Bulk reorder siblings
```

Implementation details:

**POST /containers** (Create):
```python
class ContainerCreateRequest(BaseModel):
    container_type: str  # "season", "arc", "act", "chapter", "scene"
    name: str
    parent_id: Optional[str] = None
    attributes: dict = {}
    sort_order: int = 0

@router.post("/")
async def create_container(
    req: ContainerCreateRequest,
    container_repo: ContainerRepository = Depends(get_container_repo),
    event_service: EventService = Depends(get_event_service),
):
    container = GenericContainer(
        container_type=req.container_type,
        name=req.name,
        parent_id=req.parent_id,
        sort_order=req.sort_order,
        attributes=req.attributes,
    )
    container_repo.save_container(container)
    event_service.append_event(
        parent_event_id=None,
        branch_id="main",
        event_type="CREATE",
        container_id=container.id,
        payload=container.model_dump(mode="json"),
    )
    return container.model_dump()
```

**PUT /containers/{container_id}** (Update):
- Load container by ID from the repository
- Update only the provided fields (name, sort_order, parent_id, attributes)
- Save back and emit UPDATE event

To find a container by ID, add a `get_by_id(container_id)` method to `ContainerRepository`:
```python
def get_by_id(self, container_id: str) -> Optional[GenericContainer]:
    """Search all type subdirectories for a container with this ID."""
    for type_dir in self.base_dir.iterdir():
        if type_dir.is_dir():
            for yaml_file in type_dir.glob("*.yaml"):
                container = self._load_file(yaml_file)
                if container.id == container_id:
                    return container
    return None
```

**DELETE /containers/{container_id}**:
- Find and delete the YAML file
- Emit DELETE event
- Remove from SQLite indexer

**POST /containers/reorder** (Bulk):
```python
class ReorderRequest(BaseModel):
    items: list[dict]  # [{ "id": "...", "sort_order": 0 }, ...]

@router.post("/reorder")
async def reorder_containers(req: ReorderRequest, ...):
    for item in req.items:
        container = container_repo.get_by_id(item["id"])
        if container:
            container.sort_order = item["sort_order"]
            container_repo.save_container(container)
```

**2. Fix the `getProjectStructure` API mismatch**

The frontend `api.ts` calls `GET /api/v1/projects/${id}/structure` but the backend serves `GET /api/v1/projects/structure` (no `{id}`). Fix in `api.ts`:
```typescript
getProjectStructure: () =>
  request<StructureTree>("/api/v1/projects/structure"),
```

**3. Register the containers router**

In `src/antigravity_tool/server/app.py`, add:
```python
from antigravity_tool.server.routers import containers
app.include_router(containers.router)
```

### Frontend

**4. Enhance `StoryStructureTree.tsx`**

The existing component (386 lines) already has drag-reorder with `@dnd-kit`. Enhance it with:

**a) "Add Child" button per node:**
- Season nodes get "Add Arc" button
- Arc nodes get "Add Act" button
- Act nodes get "Add Chapter" button
- Chapter nodes get "Add Scene" button
- Scene nodes get no add button (leaf)
- Clicking opens an inline input for the name
- On submit, calls `POST /api/v1/containers` with `parent_id` set to the parent node's ID and `container_type` set appropriately

The structural hierarchy type mapping:
```typescript
const CHILD_TYPES: Record<string, string> = {
  season: "arc",
  arc: "act",
  act: "chapter",
  chapter: "scene",
};
```

**b) Delete button per node:**
- Show a trash icon button (with confirmation dialog)
- Calls `DELETE /api/v1/containers/{id}`
- Refreshes the tree after deletion

**c) "Open in Zen" for scene nodes:**
- Scene nodes show a pen/edit icon button
- Clicking navigates to `/zen?scene_id={node.id}`
- Use `router.push()` from `next/navigation`

**d) Fix reorder backend call:**
- Currently `handleDragEnd` calls `api.updateContainer(node.id, { sort_order: i })` for each sibling
- Replace with a single `api.reorderContainers(items)` call using the new bulk endpoint

**e) Completion status color-coding:**
- Check node `attributes` for a `status` field (if present)
- Map to colors: `complete` = green left border, `in_progress` = amber, `draft` = blue, default = gray
- Add a colored left border to each tree item

**f) Fix `getProjectStructure` call:**
- Change from `api.getProjectStructure(activeProjectId)` to `api.getProjectStructure()`
- Or update the API method signature to not require a parameter

**5. Add API client methods**

```typescript
// Containers CRUD
createContainer: (body: { container_type: string; name: string; parent_id?: string; attributes?: Record<string, unknown>; sort_order?: number }) =>
  post<GenericContainer>("/api/v1/containers", body),
getContainer: (id: string) =>
  request<GenericContainer>(`/api/v1/containers/${encodeURIComponent(id)}`),
updateContainer: (id: string, body: Partial<{ name: string; sort_order: number; parent_id: string; attributes: Record<string, unknown> }>) =>
  put<GenericContainer>(`/api/v1/containers/${encodeURIComponent(id)}`, body),
deleteContainer: (id: string) =>
  del(`/api/v1/containers/${encodeURIComponent(id)}`),
reorderContainers: (items: Array<{ id: string; sort_order: number }>) =>
  post("/api/v1/containers/reorder", { items }),

// Fix project structure (remove id parameter)
getProjectStructure: () =>
  request<StructureTree>("/api/v1/projects/structure"),
```

---

## Feature 2: Alternate Timeline Browser

### Backend

**6. Add methods to `EventService`**

Add these methods to `src/antigravity_tool/repositories/event_sourcing_repo.py`:

```python
def get_branches(self) -> List[Dict[str, Any]]:
    """List all branches with their head event IDs and event counts."""
    cursor = self.conn.execute("""
        SELECT b.id, b.head_event_id,
               (SELECT COUNT(*) FROM events e WHERE e.branch_id = b.id) as event_count
        FROM branches b
        ORDER BY b.id
    """)
    return [dict(row) for row in cursor.fetchall()]

def get_events_for_branch(self, branch_id: str) -> List[Dict[str, Any]]:
    """Get all events that belong to a specific branch."""
    cursor = self.conn.execute("""
        SELECT id, parent_event_id, branch_id, timestamp, event_type, container_id, payload_json
        FROM events
        WHERE branch_id = ?
        ORDER BY timestamp ASC
    """, (branch_id,))
    events = []
    for row in cursor.fetchall():
        evt = dict(row)
        evt['payload'] = json.loads(evt.pop('payload_json'))
        events.append(evt)
    return events

def compare_branches(self, branch_a: str, branch_b: str) -> Dict[str, Any]:
    """Compare two branches by projecting their states and computing diffs."""
    state_a = self.project_state(branch_a)
    state_b = self.project_state(branch_b)

    all_ids = set(state_a.keys()) | set(state_b.keys())
    only_in_a = []
    only_in_b = []
    different = []
    same = []

    for cid in all_ids:
        in_a = cid in state_a
        in_b = cid in state_b
        if in_a and not in_b:
            only_in_a.append({"container_id": cid, "state": state_a[cid]})
        elif in_b and not in_a:
            only_in_b.append({"container_id": cid, "state": state_b[cid]})
        elif state_a[cid] != state_b[cid]:
            different.append({
                "container_id": cid,
                "state_a": state_a[cid],
                "state_b": state_b[cid],
            })
        else:
            same.append(cid)

    return {
        "branch_a": branch_a,
        "branch_b": branch_b,
        "only_in_a": only_in_a,
        "only_in_b": only_in_b,
        "different": different,
        "same_count": len(same),
    }
```

**7. Extend `timeline.py` router**

Add these endpoints to the existing `src/antigravity_tool/server/routers/timeline.py`:

```python
@router.get("/branches")
async def get_branches(
    svc: EventService = Depends(get_event_service),
) -> List[Dict[str, Any]]:
    """List all timeline branches."""
    return svc.get_branches()

@router.post("/branch")
async def create_branch(
    req: BranchCreateRequest,
    svc: EventService = Depends(get_event_service),
):
    """Create a new alternate timeline branch from a historical event."""
    try:
        svc.branch(
            source_branch_id=req.source_branch_id or "",
            new_branch_name=req.branch_name,
            checkout_event_id=req.parent_event_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"status": "created", "branch_name": req.branch_name, "parent_event_id": req.parent_event_id}

@router.get("/branch/{branch_id}/events")
async def get_branch_events(
    branch_id: str,
    svc: EventService = Depends(get_event_service),
) -> List[Dict[str, Any]]:
    """Get all events for a specific branch."""
    return svc.get_events_for_branch(branch_id)

@router.get("/compare")
async def compare_branches(
    branch_a: str,
    branch_b: str,
    svc: EventService = Depends(get_event_service),
) -> Dict[str, Any]:
    """Compare two branches and return their diffs."""
    try:
        return svc.compare_branches(branch_a, branch_b)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/stream")
async def stream_timeline_events(
    request: Request,
    svc: EventService = Depends(get_event_service),
):
    """SSE endpoint for real-time timeline event streaming."""
    from starlette.responses import StreamingResponse
    import asyncio

    last_count = len(svc.get_all_events())

    async def event_generator():
        nonlocal last_count
        while True:
            if await request.is_disconnected():
                break
            events = svc.get_all_events()
            if len(events) > last_count:
                new_events = events[last_count:]
                for evt in new_events:
                    yield f"data: {json.dumps(evt)}\n\n"
                last_count = len(events)
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

Add the request model:
```python
class BranchCreateRequest(BaseModel):
    branch_name: str
    parent_event_id: str
    source_branch_id: Optional[str] = None
```

### Frontend

**8. Add branch listing sidebar to `timeline/page.tsx`**

Enhance the existing Timeline page layout. Currently it has:
- Left panel (w-80): `StoryStructureTree`
- Right panel (flex-1): `TimelineView`

Add a **Branches section** below the `StoryStructureTree` in the left panel:

```
┌──────────────────────────────────────────────────────────────────┐
│ /timeline                                                        │
├──────────────────┬───────────────────────────────────────────────┤
│ Story Structure  │                                               │
│ ┌──────────────┐ │  Timeline Events                              │
│ │ Season 1     │ │  (TimelineView with branch SVG)               │
│ │  ├─ Arc 1    │ │                                               │
│ │  │  ├─ Ch.1  │ │                                               │
│ │  │  └─ Ch.2  │ │                                               │
│ │  └─ Arc 2    │ │                                               │
│ └──────────────┘ │                                               │
│                  │                                               │
│ Branches         │                                               │
│ ┌──────────────┐ │                                               │
│ │ ● main (12)  │ │                                               │
│ │ ○ what-if (5)│ │  ┌─────────────────────────────────────────┐ │
│ │              │ │  │ Branch Comparison (side-by-side diff)    │ │
│ │ [Compare ▼]  │ │  │ main vs what-if                         │ │
│ └──────────────┘ │  │ Only in main: Scene 6 (Zara's Death)   │ │
│                  │  │ Only in what-if: Scene 6' (Zara Lives)  │ │
│                  │  │ Different: Scene 5 (text changed)       │ │
│                  │  └─────────────────────────────────────────┘ │
└──────────────────┴───────────────────────────────────────────────┘
```

**9. Create `BranchList.tsx` component**

`src/web/src/components/timeline/BranchList.tsx`:
- Fetch branches via `api.getBranches()`
- Show each branch: name, event count, colored dot (using `BRANCH_COLORS` from `TimelinePanel`)
- Active branch indicator (filled dot)
- "Compare" dropdown: select two branches → triggers comparison view
- "New Branch" link (navigates to an event in the timeline to branch from)

**10. Create `BranchComparison.tsx` component**

`src/web/src/components/timeline/BranchComparison.tsx`:
- Fetches `api.compareBranches(branchA, branchB)`
- Shows a two-column diff view:
  - Left column: "Only in {branch_a}" — list of containers with names and types
  - Right column: "Only in {branch_b}" — same
  - Middle section: "Different" — containers that exist in both but have different state. Show a compact diff (field name: old → new)
  - Summary: "{N} containers identical, {M} different, {X} unique to each"
- Color-coded: green for additions, red for removals, amber for changes
- Dark theme styling (bg-gray-900, border-gray-800)

**11. Add API client methods**

```typescript
// Branches
getBranches: () =>
  request<Array<{ id: string; head_event_id: string | null; event_count: number }>>("/api/v1/timeline/branches"),
createBranch: (body: { branch_name: string; parent_event_id: string; source_branch_id?: string }) =>
  post<{ status: string; branch_name: string; parent_event_id: string }>("/api/v1/timeline/branch", body),
getBranchEvents: (branchId: string) =>
  request<TimelineEvent[]>(`/api/v1/timeline/branch/${encodeURIComponent(branchId)}/events`),
compareBranches: (branchA: string, branchB: string) =>
  request<BranchComparison>(`/api/v1/timeline/compare?branch_a=${encodeURIComponent(branchA)}&branch_b=${encodeURIComponent(branchB)}`),
```

Add interfaces:
```typescript
export interface BranchInfo {
  id: string;
  head_event_id: string | null;
  event_count: number;
}

export interface BranchComparison {
  branch_a: string;
  branch_b: string;
  only_in_a: Array<{ container_id: string; state: Record<string, unknown> }>;
  only_in_b: Array<{ container_id: string; state: Record<string, unknown> }>;
  different: Array<{ container_id: string; state_a: Record<string, unknown>; state_b: Record<string, unknown> }>;
  same_count: number;
}
```

---

## Output Specification

Provide the complete code for:
1. `src/antigravity_tool/server/routers/containers.py` (new file — container CRUD + reorder)
2. Updates to `src/antigravity_tool/repositories/container_repo.py` (add `get_by_id`, `delete_by_id`)
3. Updates to `src/antigravity_tool/server/api_schemas.py` (container create/update request models)
4. Updates to `src/antigravity_tool/server/app.py` (register containers router)
5. Updates to `src/antigravity_tool/repositories/event_sourcing_repo.py` (add `get_branches`, `get_events_for_branch`, `compare_branches`)
6. Updates to `src/antigravity_tool/server/routers/timeline.py` (add `/branches`, `/branch`, `/branch/{id}/events`, `/compare`, `/stream`)
7. Updates to `src/web/src/components/timeline/StoryStructureTree.tsx` (add create, delete, open-in-Zen, fix reorder, completion colors)
8. `src/web/src/components/timeline/BranchList.tsx` (new file)
9. `src/web/src/components/timeline/BranchComparison.tsx` (new file)
10. Updates to `src/web/src/app/timeline/page.tsx` (integrate BranchList + BranchComparison)
11. Updates to `src/web/src/lib/api.ts` (add methods + interfaces + fix `getProjectStructure`)

---

## Important Notes

- **A parallel session is implementing Spatial Brainstorm Canvas + Voice-to-Scene (Session 26).** Do NOT modify `Canvas.tsx` nav links, `ZenEditor.tsx`, `storyboard/page.tsx`, or create any `/brainstorm` or `/voice` routes.
- The `StoryStructureTree.tsx` already has `@dnd-kit` drag-reorder (386 lines). Build on it — do NOT rewrite from scratch. Only add the create/delete/open-in-Zen features and fix the backend wiring.
- The `TimelinePanel.tsx` already renders SVG branch visualization (162 lines). Do NOT modify it. The new `BranchList.tsx` is a sidebar complement.
- Use `toast.success()` / `toast.error()` from `sonner`.
- Use `ConfirmDialog` from `@/components/ui/ConfirmDialog` for delete confirmation.
- Use `useRouter()` from `next/navigation` for "Open in Zen" navigation.
- Run `cd src/web && npx tsc --noEmit` to verify TypeScript compiles.
