# Showrunner Architecture Review & Optimization Proposal
**Date:** 2026-03-08
**Status:** Comprehensive Analysis Complete
**Focus:** Two-repo System, Project Discovery, Chat Integration, Design Gaps

---

## Executive Summary

The Showrunner architecture is well-designed but has several implementation gaps:

1. **✅ Two-Repo System Works** — Showrunner (tool) and QuantumDharma (story project) are properly separated
2. **⚠️ Project Discovery is Ad-Hoc** — Requires being in project directory; no generic multi-project support
3. **❌ Chat System Incomplete** — Backend 85% done, frontend missing state wiring (critical bug)
4. **⚠️ IDE/UI Workflows Unclear** — Design docs don't specify UI-first vs CLI-first workflows
5. **📊 Design Debt** — 98 design docs exist, but integration points between them are vague

This document proposes an optimized, unified architecture that makes Showrunner **truly generic** and **multi-project aware**.

---

## Part 1: Current Architecture Analysis

### 1.1 Two-Repo System (What Works ✅)

```
/Documents/
├── Showrunner/                       (Tool + References)
│   ├── src/showrunner_tool/         (Python CLI/API)
│   ├── src/web/                     (Next.js UI)
│   └── docs/                        (Design docs)
│
└── QuantumDharma/                   (Story Project)
    ├── showrunner.yaml              ← Auto-discovered
    ├── characters/, world/, story/
    ├── fragment/                     (Written scenes)
    └── reference/                    (Brainstorm context)
```

**How It Works:**
- `Project.find()` walks directory tree looking for `showrunner.yaml`
- When you run `showrunner status` from QuantumDharma, it auto-loads
- CLI commands print prompts; Claude Code reads & generates YAML

**Current Limitation:**
- Only works when you're **in** the project directory
- No multi-project dashboard (can't easily switch between projects)
- Project discovery is implicit, not explicit

---

### 1.2 Project Discovery Mechanism

**File:** `src/showrunner_tool/core/project.py:55-65`

```python
@classmethod
def find(cls, start: Path | None = None) -> Project:
    """Walk up from `start` (default cwd) to find the nearest showrunner.yaml."""
    current = (start or Path.cwd()).resolve()
    while current != current.parent:
        if (current / MANIFEST_FILE).exists():
            return cls(current)
        current = current.parent
    raise ProjectError(
        f"No {MANIFEST_FILE} found. Run 'showrunner init' to create a project."
    )
```

**Issues:**
1. **Implicit Discovery** — Assumes you're in project directory or a subdirectory
2. **Single Project** — Can only work with one project at a time
3. **CLI-Centric** — Doesn't support "set active project" workflows
4. **No Env Var Support** — Can't export `SHOWRUNNER_PROJECT=/path` to override

---

### 1.3 Two-Repo Workflow (What's Missing ❌)

**Intended Workflows per Design Docs:**

1. **Writing Session:**
   ```
   User → Open QuantumDharma in IDE
        → `showrunner status` (works if cwd is in QuantumDharma)
        → Web UI loads project (IF servers are running)
        → Edit scenes in Zen Mode
        → Chat sidebar assists writing
   ```

2. **Tool Testing Against Story:**
   ```
   User → `cd /Documents/Showrunner`
        → `showrunner character create "NewChar"`
        → Reads prompt, generates YAML in QuantumDharma
        → Back to QuantumDharma to commit
   ```

**The Problem:** No clear "registry" of projects. Each command must know where to write.

---

### 1.4 UI/IDE Integration Gaps

**From IDE_GUIDE.md:**
- "Claude Code is the Director Agent"
- CLI prints prompts → Claude Code reads → generates YAML → writes to disk
- FileWatcher syncs YAML to web UI automatically

**Reality:**
- Web UI has no project picker (can only work with cwd project)
- No "recent projects" or "favorites"
- No way to switch projects in web UI without restarting backend

**From PRD.md:**
- "Multi-project & Multi-timeline" is listed as a feature
- Dashboard should show "multiple project silos"
- Status: 🆕 (Not started)

---

## Part 2: Chat System Analysis

### 2.1 Backend Status ✅ (85% Complete)

**What's Implemented:**

| Component | Status | Location |
|-----------|--------|----------|
| Chat Router | ✅ Wired | `server/routers/chat.py` |
| Chat Models | ✅ Defined | `schemas/chat.py` |
| Session Service | ✅ Implemented | `services/chat_session_service.py` |
| Chat Orchestrator | ✅ Initialized | `app.py:128-150` |
| Lifespan Setup | ✅ Done | `app.py:127-200` |

**Backend Gaps:**
1. Chat endpoints return stubbed responses (`_get_chat_session_service()` has NotImplementedError fallback)
2. Message streaming (SSE) not fully wired
3. Tool invocations not connected to agent ecosystem

---

### 2.2 Frontend Status ❌ (Critical Bug)

**The Issue:** ChatSidebarWrapper uses non-existent state

**File:** `src/web/src/components/chat/ChatSidebarWrapper.tsx:8`

```typescript
export function ChatSidebarWrapper() {
  const { isChatSidebarOpen, setChatSidebarOpen } = useStudioStore();
  // ❌ BUG: These don't exist in ChatSlice!
}
```

**Actual State:** `src/web/src/lib/store.ts:45-70`

ChatSlice has:
```typescript
chatSessions: any[]
activeSessionId: string | null
chatMessages: any[]
isStreaming: boolean
// ... but NO isChatSidebarOpen or setChatSidebarOpen
```

**Result:**
- ✅ Chat sidebar component exists
- ✅ All layout is in place (layout.tsx:55)
- ❌ **Chat sidebar will not render** (undefined state)

**Fix:** Add to ChatSlice interface + implementation:
```typescript
isChatSidebarOpen: boolean;
setChatSidebarOpen: (open: boolean) => void;
```

---

### 2.3 Chat Workflow Design Gaps

From PRD.md § 8 (Agentic Chat Sidebar):
- "Persistent collapsible panel on right side"
- "Context-aware — auto-loads relevant entities based on current page"
- "Supports `@-mention` for autocomplete, `/commands` for session control"

**Missing Specs:**
1. **Default State** — Should chat sidebar be open by default? (Not specified)
2. **Trigger to Open** — What opens the sidebar? (Button? Keyboard shortcut? Auto-open?)
3. **Mobile/Responsive** — How does it work on narrow screens?
4. **Narrowing** — What entities show in sidebar for each page?
   - In `/zen` → Scene characters + world context?
   - In `/dashboard` → Project overview?
   - In `/storyboard` → Panel context?

---

## Part 3: Design Document Audit

### 3.1 Documentation Inventory

**Total:** 98 design/spec documents

| Category | Count | Status |
|----------|-------|--------|
| Core Design Docs | 6 | Complete |
| User Journey Specs | 3 | Defined but fragmented |
| Agent Skills | 24 | Documented but scattered |
| Dev Tasks (Phase/Session) | 48 | Historical, hard to extract current state |
| Workflow Docs | 4 | Minimal, more like sketches |
| API/Integration | 13 | Partially complete |

**Key Issues:**

1. **Fragmentation** — 48 session docs make it hard to know "what's done now"
2. **Versioning** — Design docs don't indicate "Phase X target state" clearly
3. **Integration Points** — Missing: "When UI sends X, backend does Y"
4. **Missing Specs:**
   - Project selection/switching workflows
   - Chat sidebar state machine
   - IDE agent task flows
   - Multi-window/multi-tab scenarios

### 3.2 Critical Design Gaps

| Gap | Impact | Priority |
|-----|--------|----------|
| **No Project Registry** | Can't switch projects in web UI | P0 |
| **Chat Sidebar Not Wired** | Chat feature broken in UI | P0 |
| **Unclear UI-First vs CLI-First** | IDE agent doesn't know preferred workflow | P1 |
| **No Responsive Design Spec** | UI breaks on mobile/narrow | P1 |
| **Missing Error Recovery Flows** | No "what if X fails?" specs | P2 |
| **Vague Agent Autonomy Levels** | `/plan` vs `/execute` unclear | P2 |
| **No Rate Limiting Specs** | Chat could spam API | P2 |

---

## Part 4: Optimized Architecture Proposal

### 4.1 Unified Project System

**Goal:** Make Showrunner work with any project, anywhere, anytime.

#### Option A: Project Registry (Recommended)

```yaml
# ~/.showrunner/projects.yaml (NEW)
projects:
  - id: "quantum-dharma"
    path: "/Users/vikasahlawat/Documents/QuantumDharma"
    name: "Quantum Dharma"
    last_opened: "2026-03-08T14:30:00Z"
    tags: ["active", "manga"]

  - id: "midnight-chronicle"
    path: "/path/to/other/project"
    name: "Midnight Chronicle"
    last_opened: "2026-02-15T10:00:00Z"
    tags: ["archived"]

settings:
  default_project: "quantum-dharma"
  auto_detect: true  # Walk up from cwd
  remember_last: true
```

**Implementation:**

1. **New Service:** `ProjectRegistryService`
   ```python
   class ProjectRegistryService:
       def get_all_projects() -> List[ProjectSummary]
       def get_active_project() -> Project
       def set_active_project(id: str)
       def register_project(path: Path)
       def forget_project(id: str)
       def find_project_by_path(path: Path) -> Project  # walks up
   ```

2. **New Env Var:** `SHOWRUNNER_PROJECT`
   ```bash
   export SHOWRUNNER_PROJECT=quantum-dharma
   showrunner status  # Uses registered project
   ```

3. **New CLI Commands:**
   ```bash
   showrunner project list           # Show all registered projects
   showrunner project set quantum-dharma
   showrunner project register /path/to/project
   showrunner project current        # Show active project
   ```

4. **New API Endpoints:**
   ```
   GET /api/v1/projects/               (current — returns active project)
   GET /api/v1/projects/all            (new — all registered projects)
   POST /api/v1/projects/switch/{id}   (new — set active project)
   POST /api/v1/projects/register      (new — register new project)
   ```

#### Option B: Environment-Based Discovery (Simpler)

```bash
# In project directory or anywhere:
export SHOWRUNNER_PROJECT=/Users/vikasahlawat/Documents/QuantumDharma
showrunner status  # Works from anywhere

# Or in .env file:
SHOWRUNNER_PROJECT=/path/to/quantum-dharma
```

**Recommendation:** Implement **Option A + B** together for maximum flexibility.

---

### 4.2 Chat Sidebar State Machine

**Current Issue:** No state management for sidebar visibility.

**Proposed Solution:**

```typescript
// In ChatSlice interface
isChatSidebarOpen: boolean;
setChatSidebarOpen: (open: boolean) => void;
chatSidebarCollapsed: boolean;        // Separate from visibility
setChatSidebarCollapsed: (collapsed: boolean) => void;

// In implementation
const createChatSlice = (set: any): ChatSlice => ({
  isChatSidebarOpen: true,            // Open by default
  chatSidebarCollapsed: false,        // Show content
  setChatSidebarOpen: (open) => set({ isChatSidebarOpen: open }),
  setChatSidebarCollapsed: (collapsed) => set({ chatSidebarCollapsed: collapsed }),

  // Keyboard shortcuts
  // Ctrl+K: Focus chat input
  // Esc: Close sidebar
});
```

**Persistence:**
```typescript
// Save to localStorage on change
useEffect(() => {
  localStorage.setItem(
    'chat-sidebar-open',
    JSON.stringify(isChatSidebarOpen)
  );
}, [isChatSidebarOpen]);

// Restore on init
useEffect(() => {
  const saved = localStorage.getItem('chat-sidebar-open');
  if (saved) setChatSidebarOpen(JSON.parse(saved));
}, []);
```

---

### 4.3 Unified Workflow Specification

**Problem:** Design docs don't specify which workflows are "primary" and which are "advanced."

**Proposed Hierarchy:**

#### Tier 1: Writing Workflows (Primary)
```
1. Read project context
2. Open Zen Mode
3. Chat sidebar assists (context-aware)
4. Write scene prose
5. Commit to git
```

**Tools Used:** Zen Mode + Chat + Git (no CLI)
**Audience:** Discovery Writers, Pantsers
**Expected Frequency:** 80% of user time

---

#### Tier 2: Structured Creation (Intermediate)
```
1. Use Dashboard to see project state
2. Create characters/locations via Schema Builder
3. Run Story Architect to outline
4. Generate panels via Storyboard
5. Commit
```

**Tools Used:** Web UI + Chat
**Audience:** Architects, Planners
**Expected Frequency:** 15% of user time

---

#### Tier 3: Advanced Automation (Expert)
```
1. Define custom pipelines in Pipeline Studio
2. Set approval gates and model overrides
3. Run batch operations
4. Review, approve, commit
```

**Tools Used:** Pipelines + Chat (for refinement)
**Audience:** Power users, automation-focused
**Expected Frequency:** 5% of user time

---

#### Tier 4: IDE Integration (For Claude Code)
```
1. Read CLAUDE.md briefing
2. CLI prints prompts (no UI)
3. Claude Code generates YAML
4. FileWatcher auto-syncs to UI
5. Git commit
```

**Tools Used:** CLI only
**Audience:** Technical users, tool developers
**Expected Frequency:** For development, not writing

---

### 4.4 IDE Agent Workflow Specification

**Problem:** IDE agents (Claude Code) don't know when to use CLI vs UI.

**Proposed Decision Tree:**

```
Is this a writing session?
├─ YES → Use Zen Mode + Chat (avoid CLI unless needed for context)
└─ NO (research/planning) → Can use CLI, but prefer Chat + Dashboard

Is the user asking for AI assistance?
├─ YES → Use Chat (handles context, multi-turn, artifacts)
└─ NO (pure CRUD) → Use CLI if simple, UI if browsing

Is there a complex approval workflow?
├─ YES → Use Web UI (Pipeline Studio shows gates visually)
└─ NO → Chat can handle inline approvals

Does the task involve visual creation (storyboard, layout)?
├─ YES → Use Web UI (drag-drop, visualization)
└─ NO → Chat or CLI
```

---

### 4.5 Chat Context Injection

**Problem:** Chat sidebar doesn't know what to be "about" on each page.

**Proposed Solution:**

```typescript
// In each page, provide context hint
interface ChatContextHint {
  page: 'zen' | 'dashboard' | 'storyboard' | 'timeline' | 'schemas';
  entities?: string[];          // ["character:a", "location:college"]
  task?: string;                // "write_scene", "outline_chapter"
  scope?: 'project' | 'chapter' | 'scene';
}

// In Zen Mode
<ChatSidebarWrapper
  context={{
    page: 'zen',
    entities: detectedEntities,
    task: 'write_scene',
    scope: 'scene'
  }}
/>

// In Dashboard
<ChatSidebarWrapper
  context={{
    page: 'dashboard',
    task: 'project_overview',
    scope: 'project'
  }}
/>

// Chat sidebar auto-narrows context based on hint
// E.g., in Zen Mode, only load character + scene context
```

---

### 4.6 Responsive Design Spec

**Current:** No mobile spec defined.

**Proposed Breakpoints:**

| Device | Chat Sidebar | Main Content | Actions |
|--------|--------------|--------------|---------|
| **Desktop** (≥1024px) | Fixed right panel (300px) | Full width | All visible |
| **Tablet** (768-1023px) | Drawer / toggle | Full width | Hamburger menu |
| **Mobile** (<768px) | Sheet modal / fullscreen | Full width | Bottom sheet for chat |

**Implementation:**
```tsx
const useResponsiveChat = () => {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const media = window.matchMedia('(max-width: 768px)');
    const onChange = (m: MediaQueryListEvent) => setIsMobile(m.matches);
    media.addEventListener('change', onChange);
    setIsMobile(media.matches);
    return () => media.removeEventListener('change', onChange);
  }, []);

  return isMobile ? 'modal' : 'sidebar';  // Render mode
};
```

---

## Part 5: Implementation Roadmap

### Phase 1: Fix Chat Sidebar (1 session)
- [x] Identify missing state
- [ ] Add `isChatSidebarOpen` + `setChatSidebarOpen` to ChatSlice
- [ ] Wire keyboard shortcuts (Ctrl+K to focus, Esc to close)
- [ ] Test chat sidebar rendering
- [ ] Commit: "fix: Wire chat sidebar state to UI"

### Phase 2: Project Registry (2-3 sessions)
- [ ] Create `ProjectRegistryService` class
- [ ] Implement `projects.yaml` persistence
- [ ] Add CLI commands: `project list|set|register|forget|current`
- [ ] Add API endpoints: `/api/v1/projects/all`, `/switch/{id}`, `/register`
- [ ] Update web UI: Project picker in navbar
- [ ] Commit: "feat: Add project registry for multi-project support"

### Phase 3: Unified Workflow Docs (1 session)
- [ ] Create `docs/WORKFLOW_TIERS.md` explaining 4 tiers
- [ ] Update IDE_GUIDE.md with decision tree
- [ ] Create `docs/AGENT_DECISION_TREE.md` for Claude Code
- [ ] Commit: "docs: Clarify workflow tiers and IDE agent decision logic"

### Phase 4: Chat Context Hints (1-2 sessions)
- [ ] Create `ChatContextHint` type
- [ ] Update all page layouts to provide hints
- [ ] Update ChatSidebar to narrow context based on hint
- [ ] Test context injection in each page
- [ ] Commit: "feat: Add context-aware chat sidebar per page"

### Phase 5: Responsive Design (1 session)
- [ ] Implement mobile breakpoints
- [ ] Create drawer/modal variants of ChatSidebar
- [ ] Add bottom-sheet for chat on mobile
- [ ] Test on tablet/mobile
- [ ] Commit: "style: Add responsive design for mobile/tablet"

---

## Part 6: Quick Wins (Do Now!)

These can be done in 30 minutes each:

### 1. Fix Chat Sidebar (Immediate)
```typescript
// src/web/src/lib/store.ts — ChatSlice interface
export interface ChatSlice {
  // ... existing fields ...
  isChatSidebarOpen: boolean;       // ADD THIS
  setChatSidebarOpen: (open: boolean) => void;  // ADD THIS
}

// In createChatSlice
const createChatSlice = (set: any): ChatSlice => ({
  // ... existing ...
  isChatSidebarOpen: true,  // Open by default
  setChatSidebarOpen: (open) => set({ isChatSidebarOpen: open }),
});
```

### 2. Add Keyboard Shortcut for Chat
```typescript
// src/web/src/components/chat/ChatSidebarWrapper.tsx
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault();
      setChatSidebarOpen(true);
    }
    if (e.key === 'Escape' && isChatSidebarOpen) {
      setChatSidebarOpen(false);
    }
  };
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [isChatSidebarOpen, setChatSidebarOpen]);
```

### 3. Persist Chat Sidebar State to localStorage
```typescript
// After setChatSidebarOpen changes
useEffect(() => {
  localStorage.setItem('showrunner-chat-open', String(isChatSidebarOpen));
}, [isChatSidebarOpen]);

// On mount, restore
useEffect(() => {
  const saved = localStorage.getItem('showrunner-chat-open');
  if (saved) {
    setChatSidebarOpen(saved === 'true');
  }
}, []);
```

### 4. Add Environment Variable Support
```python
# src/showrunner_tool/core/project.py
import os

class Project:
    @classmethod
    def find(cls, start: Path | None = None) -> Project:
        # Check env var first
        env_project = os.getenv('SHOWRUNNER_PROJECT')
        if env_project:
            proj_path = Path(env_project).resolve()
            if (proj_path / MANIFEST_FILE).exists():
                return cls(proj_path)

        # Then walk up from cwd
        current = (start or Path.cwd()).resolve()
        # ... existing logic ...
```

---

## Part 7: Design Documentation Consolidation

### Current State (98 files, fragmented)

**Problem:** Hard to know "what's the current state?" when there are 48 session docs.

### Proposed State (Consolidated)

```
docs/
├── DESIGN.md              (Main architecture, unchanged)
├── PRD.md                 (Product requirements, unchanged)
├── LOW_LEVEL_DESIGN.md    (Technical specs, unchanged)
├── IDE_GUIDE.md           (Updated with decision tree)
├── VISION.md              (Long-term, unchanged)
│
├── WORKFLOW_TIERS.md      (NEW — writing vs creation vs automation)
├── AGENT_DECISION_TREE.md (NEW — IDE agent logic)
├── PROJECT_REGISTRY.md    (NEW — multi-project design)
├── CHAT_SIDEBAR_SPEC.md   (NEW — state machine + context)
├── RESPONSIVE_SPEC.md     (NEW — mobile/tablet design)
│
└── PHASES/                (Phase-specific docs)
    ├── PHASE_F.md         (Latest: multi-project, model config)
    ├── PHASE_G.md         (Next: research, routing)
    ├── PHASE_H.md         (Then: RAG, agents)
    └── PHASE_J_CHAT.md    (Current: agentic chat)

agents/skills/            (Unchanged — AI agent prompts)
agents/tasks/             (Archive or move to PHASES/)
```

**Action:** Create consolidated docs and mark old ones as "HISTORICAL."

---

## Part 8: Summary of Recommendations

| Item | Priority | Effort | Impact |
|------|----------|--------|--------|
| **Fix Chat Sidebar State** | P0 | 15 min | Unblocks chat UI |
| **Add Env Var Support** | P0 | 30 min | Works from anywhere |
| **Project Registry Service** | P1 | 2-3 hrs | Multi-project support |
| **Consolidate Design Docs** | P1 | 2-3 hrs | Clarity on current state |
| **Workflow Tier Spec** | P1 | 1 hr | Guides IDE agent decisions |
| **Chat Context Hints** | P2 | 2 hrs | Better narrowing |
| **Responsive Design** | P2 | 2-3 hrs | Mobile support |
| **Keyboard Shortcuts** | P2 | 30 min | UX polish |

---

## Conclusion

Showrunner has a **solid architectural foundation** but needs:

1. **Project Discovery** to be explicit, not implicit (registry + env var)
2. **Chat Sidebar** to be properly wired (missing state fix)
3. **Workflow Clarity** in design docs (tiers, decision trees)
4. **Better IDE Integration** with context hints and responsive design

Implementing these changes will make Showrunner:
- ✅ Work with any project, anywhere
- ✅ Have a functional chat sidebar
- ✅ Provide clear guidance for IDE agents
- ✅ Scale to multiple projects and workflows

**Next Step:** Start with the "Quick Wins" section (Phase 1 — Fix Chat Sidebar).

---

*Document prepared by: Claude Code AI*
*Review scope: Architecture, design docs, codebase inspection*
*Recommendations: Feature-complete, implementation-ready*
