# AI Product-to-Code Platform

Backend service that turns a natural-language requirement into research, epics, user stories, a technical specification, generated code, and an automated validation report.

**Stack:** FastAPI, SQLAlchemy 2 (async + asyncpg), PostgreSQL + **pgvector**, LangGraph, OpenAI (chat + embeddings), optional Tavily (web research), JWT auth, WebSockets.

---

## What it does

| Area | Description |
|------|-------------|
| **Auth** | Register and login; JWT bearer tokens; admin-only routes for analytics and user management. |
| **Projects** | Users own projects; each project can have documents for RAG and multiple workflow **runs**. |
| **Runs** | POST a requirement → background pipeline runs; pause/resume; optional validate-and-fix loop. |
| **Pipeline** | **Research → Epic → Story → Spec → Code → Validation**; each step persists an **artifact** (JSON) on the run. |
| **RAG** | Upload PDF / TXT / DOCX → text extraction → chunking → OpenAI embeddings → stored in pgvector; **semantic search** by cosine distance. |
| **Exports** | Per-artifact PDF/Markdown/ZIP; full run ZIP; structured ZIP (epics, stories, spec, validation JSON, code tree). |
| **Realtime** | WebSocket on `/ws/progress/{run_id}` for questions, feedback, pause/resume signals. |

---

## Requirements

- **Python** 3.11+
- **PostgreSQL** with **pgvector** (embeddings + similarity search)
- **OpenAI API key** (required)
- **Tavily API key** (optional; improves research agent when set)

---

## Environment variables

Create a `.env` next to `requirements.txt`.

**Required**

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL URL. `postgresql://user:pass@host:5432/dbname` works; the app normalizes to `postgresql+asyncpg://...` for async SQLAlchemy. |
| `OPENAI_API_KEY` | OpenAI API key (LLM calls + `text-embedding-3-small` embeddings). |
| `SECRET_KEY` | Long random string used to sign JWTs (do not commit real secrets). |

**Optional**

| Variable | Default | Description |
|----------|---------|-------------|
| `TAVILY_API_KEY` | — | Enables Tavily-backed web research in the research agent. |
| `ALGORITHM` | `HS256` | JWT algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token lifetime. |
| `UPLOAD_DIR` | `uploads` | Uploaded files directory. |
| `OUTPUT_DIR` | `generated_code` | Output path hint for generated assets. |

**Example `.env` (replace values):**

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/product_to_code
OPENAI_API_KEY=sk-...
SECRET_KEY=change-this-to-a-long-random-string
# TAVILY_API_KEY=tvly-...
```

---

## Setup

1. **Database** — create a database; enable pgvector (superuser or allowed role):

   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Install**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure** `.env` (see above).

4. **Run** — on startup the app creates tables and runs `CREATE EXTENSION IF NOT EXISTS vector` (needs DB permission):

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Docs** — Swagger UI: `http://localhost:8000/docs`

---

## API overview (all under `/api/v1` unless noted)

| Method | Path | Notes |
|--------|------|--------|
| POST | `/users/register` | Body: email, password → returns `access_token`. |
| POST | `/users/login` | Body: email, password → `access_token`. |
| GET | `/users/me` | Current user (Bearer required). |
| POST | `/projects/` | Create project. |
| GET | `/projects/` | List my projects. |
| GET | `/projects/{id}` | Get one project. |
| POST | `/runs/` | Body: `project_id`, `requirement` → starts workflow (Bearer). |
| GET | `/runs/{run_id}` | Run status and stage. |
| POST | `/runs/{run_id}/pause` | Pause (also WS). |
| POST | `/runs/{run_id}/resume` | Resume. |
| POST | `/runs/{run_id}/validate-and-fix` | Starts background validation loop. |
| GET | `/artifacts/{artifact_id}` | Fetch artifact JSON. |
| GET | `/artifacts/{id}/export/pdf` | PDF export. |
| GET | `/artifacts/{id}/export/markdown` | Markdown export. |
| GET | `/artifacts/{id}/export/code-zip` | ZIP of generated code (Code artifact). |
| GET | `/artifacts/run/{run_id}/export/full-report` | Full run ZIP. |
| GET | `/artifacts/run/{run_id}/export/structured` | Structured bundle ZIP. |
| POST | `/rag/{project_id}/upload` | Multipart file upload (PDF/TXT/DOCX). |
| GET | `/rag/{project_id}/search?query=...&limit=5` | Semantic search over project chunks. |
| DELETE | `/rag/{document_id}` | Delete document + chunks. |
| GET | `/admin/...` | Admin analytics, users, projects, runs (admin user only). |

**Auth header:** `Authorization: Bearer <access_token>`

---

## Workflow stages (artifacts)

1. **Research** — requirement (+ optional user questions via WS) + optional web research.  
2. **Epic** — high-level epics.  
3. **Story** — user stories.  
4. **Spec** — technical specification.  
5. **Code** — stored as `{"files": { "path/to/file.py": "content", ... }}`.  
6. **Validation** — lint/tests in a temp directory; report JSON as **Validation** artifact; run may be marked completed.

---

## WebSocket

- **URL:** `ws://localhost:8000/ws/progress/{run_id}`
- **Messages (JSON):** `type` = `question` | `feedback` | `pause` | `resume` (see `app/core/ws_manager.py` for fields).

---

## Repository layout

```
app/
  main.py                 # FastAPI, CORS, WebSocket, startup
  core/                   # config, security, logging, ws_manager
  db/session.py           # async engine, get_db
  api/v1/                 # users, projects, runs, artifacts, rag, admin
  workflows/orchestrator.py
  workflows/state.py
  agents/                 # research, epic, story, spec, code, validation
  models/                 # SQLAlchemy models
  services/               # rag_service, export_service
requirements.txt
```

---

## License

Use and modify for your own projects; no license file is included by default.
