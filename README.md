# Showrunner (Showrunner Studio)

**Agentic AI-Powered Writing Tool for Complex Narratives**

Showrunner is a full-stack creative writing studio that pairs with LLMs (Gemini, Claude, GPT-4) to help you build, manage, and write complex multi-season narratives — manga, comics, screenplays, and more. It features an autonomous Director agent, an agentic chat system, a visual pipeline builder, semantic zoom, Google Drive cloud sync, and a rich Zen Editor.

---

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup on a New Machine](#setup-on-a-new-machine)
  - [1. Clone the Repo](#1-clone-the-repo)
  - [2. Copy Secrets](#2-copy-secrets)
  - [3. Backend Setup (Python)](#3-backend-setup-python)
  - [4. Frontend Setup (Next.js)](#4-frontend-setup-nextjs)
  - [5. Start the App](#5-start-the-app)
  - [6. Connect Google Drive](#6-connect-google-drive)
- [Project Structure](#project-structure)
- [Configuration Files Reference](#configuration-files-reference)
- [What Gets Rebuilt Automatically](#what-gets-rebuilt-automatically)
- [What Needs Manual Migration](#what-needs-manual-migration)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (:3000)                      │
│            Next.js 16 + React 19 + TailwindCSS 4        │
│     TipTap Editor · React Flow Canvas · Zustand State    │
└──────────────────────────┬──────────────────────────────┘
                           │  REST + SSE
┌──────────────────────────▼──────────────────────────────┐
│                  FastAPI Backend (:8000)                  │
│   Routers: project, characters, world, chapters,         │
│   workflow, director, pipeline, chat, sync, writing ...   │
├──────────────────────────────────────────────────────────┤
│  Services: ChatOrchestrator · PipelineService ·           │
│  KnowledgeGraph · CloudSync · ModelConfigRegistry         │
├──────────────────────────────────────────────────────────┤
│  Data: SQLite (KG + Events + Chat) · ChromaDB (Vectors)  │
│  Storage: YAML files on disk · Google Drive (cloud sync)  │
└──────────────────────────────────────────────────────────┘
```

---

## Prerequisites

| Tool       | Version  | Notes                     |
|------------|----------|---------------------------|
| **Python** | ≥ 3.11   | Required for backend      |
| **Node.js**| ≥ 18     | Required for frontend     |
| **npm**    | ≥ 9      | Comes with Node.js        |
| **Git**    | Any      | For cloning               |

---

## Setup on a New Machine

### 1. Clone the Repo

```bash
git clone <your-repo-url> showrunner
cd showrunner
```

### 2. Copy Secrets

You need to copy **two files** from your existing machine that are **not tracked by Git**:

| File               | What it is                                       | Where to place it          |
|--------------------|--------------------------------------------------|----------------------------|
| `.env`             | API keys & Google OAuth client config             | Project root (`./`)        |
| `credentials.json` | Google Cloud OAuth 2.0 client secret file         | Project root (`./`)        |

```bash
# From your existing machine, copy these to the new clone:
scp user@old-machine:~/Documents/writing_tool/.env ./
scp user@old-machine:~/Documents/writing_tool/credentials.json ./
```

**`.env` contents reference:**

```env
GEMINI_API_KEY=your_gemini_api_key

# Google Drive Sync
GOOGLE_DRIVE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_DRIVE_CLIENT_SECRET=GOCSPX-your_secret
GOOGLE_DRIVE_PROJECT_ID=your-gcp-project-id
GOOGLE_DRIVE_REDIRECT_URI=http://localhost:3000/auth/callback
```

### 3. Backend Setup (Python)

```bash
# Create a clean virtual environment
python3.11 -m venv .venv_clean
source .venv_clean/bin/activate

# Install the project and its dependencies
pip install -e .

# Install additional dependencies not yet in pyproject.toml
pip install \
  python-dotenv \
  google-auth \
  google-auth-oauthlib \
  google-api-python-client
```

> **Note:** The project uses `litellm` for LLM routing (supports Gemini, Claude, GPT-4, and many other providers). It's listed in `pyproject.toml` and will be installed automatically.

### 4. Frontend Setup (Next.js)

```bash
cd src/web

# Create the local environment file
cp .env.local.example .env.local
# .env.local should contain: NEXT_PUBLIC_API_URL=http://localhost:8000

# Install Node.js dependencies
npm install

cd ../..
```

### 5. Start the App

**Option A — Use the all-in-one launcher:**

```bash
bash start_studio.sh
```

This starts both the backend (port 8000) and frontend (port 3000) simultaneously.

**Option B — Run them separately (recommended for development):**

```bash
# Terminal 1: Backend
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
.venv_clean/bin/python -c "import uvicorn; uvicorn.run('showrunner_tool.server.app:app', host='0.0.0.0', port=8000)"

# Terminal 2: Frontend
cd src/web && npm run dev
```

Open **http://localhost:3000** in your browser.

### 6. Connect Google Drive

After the app is running:

1. Open the app at `http://localhost:3000`
2. Click the **cloud sync icon** in the navbar (or find "Connect Google Drive")
3. Complete the Google OAuth flow in the browser popup
4. Once authenticated, a `token.json` is saved at `.showrunner/token.json`
5. Your projects from Drive will now be accessible

> **Important:** `credentials.json` is the *app-level* OAuth client config. The *user-level* access token (`token.json`) is generated fresh through the browser OAuth flow and cannot be simply copied between machines — **you must re-authenticate on each new machine.**

---

## Project Structure

```
showrunner/
├── showrunner.yaml          # Project manifest (name, schema version)
├── .env                      # API keys & secrets (GITIGNORED)
├── credentials.json          # Google OAuth client config (GITIGNORED)
├── pyproject.toml            # Python package definition & dependencies
├── start_studio.sh           # One-command launcher (backend + frontend)
├── start_server.sh           # Backend-only launcher
├── run_tests.sh              # Test runner script
│
├── src/
│   ├── showrunner_tool/     # Python backend
│   │   ├── core/             #   Project model, errors, constants
│   │   ├── schemas/          #   Pydantic models (containers, sync, etc.)
│   │   ├── repositories/     #   Data access (SQLite, ChromaDB, file-based)
│   │   ├── services/         #   Business logic (KG, chat, pipeline, sync)
│   │   └── server/           #   FastAPI app, routers, middleware
│   │       ├── app.py        #     Application entry point & lifespan
│   │       └── routers/      #     REST API endpoints
│   │
│   └── web/                  # Next.js frontend
│       ├── src/
│       │   ├── app/          #   Next.js App Router pages
│       │   ├── components/   #   React components (Zen Editor, Canvas, etc.)
│       │   ├── lib/          #   API client, utilities
│       │   └── stores/       #   Zustand state management
│       └── package.json
│
├── schemas/                  # User-defined YAML schemas for entities
├── agents/                   # Agent skills & workflow definitions
├── docs/                     # Design docs, PRD, vision, CUJs
└── tests/                    # Python test suite (pytest)
```

### Gitignored Data Directories (created at runtime)

```
.showrunner/                 # App data (chat.db, token.json)
.chroma/                      # ChromaDB vector store
characters/                   # Character YAML files
containers/                   # Generic container entities
world/                        # World-building YAML files
fragment/                     # Writing fragments
idea_card/                    # Idea cards
pipeline_def/                 # Pipeline definitions
knowledge_graph.db            # SQLite knowledge graph
event_log.db                  # Event sourcing database
```

---

## Configuration Files Reference

| File | Tracked in Git? | Purpose |
|------|:-:|---------|
| `showrunner.yaml` | ✅ | Project manifest — identifies this as a Showrunner project |
| `pyproject.toml` | ✅ | Python dependencies & build config |
| `src/web/package.json` | ✅ | Frontend dependencies |
| `.env` | ❌ | API keys (`GEMINI_API_KEY`) and Google OAuth client config |
| `credentials.json` | ❌ | Google Cloud OAuth 2.0 client secrets JSON |
| `.showrunner/token.json` | ❌ | User's Google Drive access/refresh token (generated via OAuth flow) |
| `src/web/.env.local` | ❌ | Frontend API URL config (`NEXT_PUBLIC_API_URL`) |

---

## What Gets Rebuilt Automatically

When you start the server on a fresh clone, these are **rebuilt automatically**:

| Data | How |
|------|-----|
| `knowledge_graph.db` | Full sync runs on startup (`kg_service.sync_all()`) |
| `.showrunner/` directory | Created automatically on startup |
| `.chroma/` | Rebuilt as entities are indexed |

---

## What Needs Manual Migration

If you want to preserve project **content** (not just code) across machines:

| Data | How to Migrate |
|------|---------------|
| Character/World/Chapter YAML files | Copy the `characters/`, `world/`, `containers/` directories manually, or re-sync from Google Drive |
| Chat history | Copy `.showrunner/chat.db` |
| Event log | Copy `event_log.db` |
| Pipeline definitions | Copy `pipeline_def/` |
| Google Drive connection | Re-authenticate via OAuth on the new machine (cannot be copied) |

---

## Running Tests

```bash
# Using the test script
bash run_tests.sh

# Or manually
source .venv_clean/bin/activate
PYTHONPATH=src pytest tests/ -v
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'showrunner_tool'`

Make sure `PYTHONPATH` includes the `src/` directory:

```bash
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
```

### `No showrunner.yaml found`

You must run the server from the project root directory (where `showrunner.yaml` lives). The server discovers the project by walking up from the current working directory.

### Google Drive OAuth fails

1. Ensure `credentials.json` exists in the project root
2. Ensure `.env` has the correct `GOOGLE_DRIVE_CLIENT_ID` and `GOOGLE_DRIVE_CLIENT_SECRET`
3. The redirect URI must be `http://localhost:3000/auth/callback` — both in `.env` and in the Google Cloud Console's authorized redirect URIs
4. If you get a "token expired" error, disconnect and reconnect via the UI

### ChromaDB warnings

ChromaDB is optional — if it fails to initialize, the app continues with semantic search disabled. To fix, ensure `chromadb` is installed:

```bash
pip install chromadb
```

### Port already in use

```bash
# Kill processes on ports 8000 / 3000
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

---

## Documentation

Detailed design and planning documents are in the `docs/` directory:

- **[`docs/VISION.md`](docs/VISION.md)** — Product vision and philosophy
- **[`docs/PRD.md`](docs/PRD.md)** — Product Requirements Document
- **[`docs/DESIGN.md`](docs/DESIGN.md)** — High-level system design
- **[`docs/LOW_LEVEL_DESIGN.md`](docs/LOW_LEVEL_DESIGN.md)** — Detailed technical design
- **[`docs/MASTER_CUJS.md`](docs/MASTER_CUJS.md)** — Customer User Journeys

---

*Built with ❤️ by Vikas Ahlawat*
