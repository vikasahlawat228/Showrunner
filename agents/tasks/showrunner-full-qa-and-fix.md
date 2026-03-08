# Task: Full QA Sweep & Fix — Showrunner App

**Priority**: High
**Type**: Testing + Bug Fixing
**Scope**: Backend tests, frontend build, API health, UI smoke testing

## Objective

Run a complete quality pass on Showrunner. Fix all test failures, verify the backend API is healthy, verify the frontend builds and all pages render without errors. Loop until everything is green.

## Prerequisites

- Backend running: `showrunner server start --reload` (port 8000)
- Frontend running: `cd src/web && npm run dev` (port 3000)
- Python venv active: `source .venv/bin/activate`

---

## Phase 1: Fix the 8 Failing Tests

There are 8 known test failures. Fix them in this order:

### 1A. Missing dependency (1 test)

**File**: `tests/test_nl_to_dag.py`
**Test**: `TestGeneratePipelineEndpoint::test_generate_pipeline_api_endpoint`
**Error**: `RuntimeError: Form data requires "python-multipart" to be installed.`
**Fix**:
- `pip install python-multipart`
- Add `python-multipart >= 0.0.6` to `pyproject.toml` dependencies
- Re-run this test to confirm it passes

### 1B. Gemini model version mismatch (1 test)

**File**: `tests/test_phase_f.py`
**Test**: `TestModelConfigRegistry::test_missing_yaml_uses_defaults`
**Error**: `assert 'gemini/gemini-2.5-flash' == 'gemini/gemini-2.0-flash'`
**Fix**: The production code was updated to use `gemini-2.5-flash` but the test still expects `2.0-flash`. Update the test expectation to match the current default in the codebase. Search for where the default model is defined (likely in `src/showrunner_tool/core/` or `src/showrunner_tool/schemas/`) and make the test match.

### 1C. Async generator pipeline bugs (3 tests)

**File**: `tests/test_chat_tool_registry.py`
**Tests**:
- `TestPipelineTool::test_pipeline_lists_definitions` — `TypeError: argument of type 'async_generator' is not iterable`
- `TestPipelineTool::test_pipeline_empty` — `TypeError: argument of type 'async_generator' is not iterable`
- `TestPipelineTool::test_pipeline_error` — `AttributeError: 'async_generator' object has no attribute 'lower'`

**Root cause**: The pipeline tool was refactored to return an async generator (for SSE streaming), but the tests (and possibly the consuming code in the tool registry) still treat the return value as a plain string.

**Fix approach**:
1. Find the pipeline tool implementation (likely in `src/showrunner_tool/agent/` or `src/showrunner_tool/services/`)
2. Check whether the tool registry's pipeline handler properly collects the async generator into a string
3. Either fix the tool to return a collected string when not streaming, or fix the tests to properly consume the async generator (using `async for` or `[chunk async for chunk in result]`)
4. All 3 tests should pass after the fix

### 1D. Tool registry mock mismatches (2 tests)

**File**: `tests/test_chat_plan_mode.py`
**Test**: `TestToolExecution::test_registered_tool_called` — `assert 0 == 1`

**File**: `tests/test_integration_dal_chat.py`
**Test**: `TestToolExecution::test_registered_tool_executes` — `assert 0 == 1`

**Root cause**: The tool registry has been updated with new tools, but the mocks in these tests are stale. The test expects a tool to be called (call count == 1) but it's never invoked (call count == 0).

**Fix approach**:
1. Read each test to understand what tool it's trying to invoke
2. Check if the tool name or registration changed
3. Update the mock setup to match the current tool registry structure

### 1E. Tool registry completeness (1 test)

**File**: `tests/test_chat_tool_registry.py`
**Test**: `TestRegistryBuilding::test_full_registry_has_all_tools`
**Error**: Set mismatch — expected tools don't match actual registered tools

**Fix**: Update the expected tool set in the test to match the current registry. List all tools from the actual registry implementation and update the test assertion.

### Verification

After all fixes:
```bash
pytest tests/ -v 2>&1 | tail -30
```

**Target: 407/407 tests passing (0 failures).**

If any test still fails, read the error, fix it, and re-run. Loop until all green.

---

## Phase 2: Backend API Health Check

With the backend running on port 8000, verify these critical endpoints respond:

```bash
# Core health
curl -s http://localhost:8000/api/v1/project | python3 -m json.tool | head -20
curl -s http://localhost:8000/api/v1/project/health | python3 -m json.tool

# Database health
curl -s http://localhost:8000/api/v1/db/health | python3 -m json.tool

# Key data endpoints
curl -s http://localhost:8000/api/v1/characters | python3 -m json.tool | head -20
curl -s http://localhost:8000/api/v1/containers | python3 -m json.tool | head -20
curl -s http://localhost:8000/api/v1/graph | python3 -m json.tool | head -20
curl -s http://localhost:8000/api/v1/timeline/events | python3 -m json.tool | head -20
curl -s http://localhost:8000/api/v1/chat/sessions | python3 -m json.tool | head -20
curl -s http://localhost:8000/api/v1/schemas | python3 -m json.tool | head -20
curl -s http://localhost:8000/api/v1/search?q=test | python3 -m json.tool | head -20
curl -s http://localhost:8000/api/v1/models | python3 -m json.tool | head -20
curl -s http://localhost:8000/api/v1/git/status | python3 -m json.tool | head -20

# OpenAPI docs load
curl -s http://localhost:8000/docs | head -5
curl -s http://localhost:8000/openapi.json | python3 -m json.tool | head -20
```

For any endpoint returning a 500 error or crash, investigate the server logs, find the bug, fix it, and re-test. The goal is zero 500 errors on GET endpoints.

---

## Phase 3: Frontend Build Verification

```bash
cd src/web
npm run build 2>&1
```

If the build fails:
1. Read the error output carefully
2. Fix TypeScript errors, missing imports, or build issues
3. Re-run `npm run build` until it succeeds

Also run the linter:
```bash
npm run lint 2>&1
```

Fix any critical lint errors (warnings are OK to skip for now).

---

## Phase 4: Frontend Page Smoke Test

With the dev server running on port 3000, use `curl` or a browser to verify each route loads without a React error screen:

**All 13 routes to check:**
1. `http://localhost:3000/` — Home/landing
2. `http://localhost:3000/dashboard` — Project dashboard
3. `http://localhost:3000/zen` — Writing desk (Zen mode)
4. `http://localhost:3000/storyboard` — Storyboard canvas
5. `http://localhost:3000/pipelines` — Pipeline builder (DAG)
6. `http://localhost:3000/timeline` — Timeline view
7. `http://localhost:3000/brainstorm` — Brainstorm interface
8. `http://localhost:3000/research` — Research agent
9. `http://localhost:3000/translation` — Translation interface
10. `http://localhost:3000/schemas` — Schema manager
11. `http://localhost:3000/preview` — Content preview
12. `http://localhost:3000/auth/callback` — Auth callback (may redirect, that's OK)
13. `http://localhost:3000/timeline-test` — Timeline test page

For each page:
```bash
curl -s http://localhost:3000/<route> | grep -i "error\|exception\|failed" || echo "OK: no errors detected"
```

Also check the browser console for JavaScript errors on each page. If you have browser access, open each page and check DevTools console.

If any page crashes or shows a React error boundary, investigate and fix.

---

## Phase 5: Cross-Cutting Checks

### 5A. Check for console warnings in backend logs
Look at the terminal running the backend for any warnings, deprecation notices, or errors during the API tests.

### 5B. Verify SSE streaming works
```bash
curl -s -N http://localhost:8000/api/v1/project/events --max-time 3 2>&1 | head -10
```

### 5C. Check database integrity
```bash
curl -s http://localhost:8000/api/v1/db/check -X POST | python3 -m json.tool
```

---

## Completion Criteria

You are done when ALL of the following are true:
- [ ] `pytest tests/ -v` shows 407/407 passing (0 failures)
- [ ] All backend GET endpoints return 200 (no 500 errors)
- [ ] `npm run build` succeeds with zero errors
- [ ] All 13 frontend routes load without React error screens
- [ ] No critical errors in backend server logs during testing

## Output

When complete, write a summary to `agents/tasks/qa-results-{date}.md` with:
- Test results (pass/fail counts)
- Any endpoints that needed fixing and what you changed
- Frontend build status
- List of pages tested and their status
- Any remaining warnings or non-critical issues noted for future cleanup
