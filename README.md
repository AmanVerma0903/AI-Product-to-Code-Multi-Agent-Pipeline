# 🚀 AI Product-to-Code Platform

An advanced, multi-agent AI backend service that transforms natural language business requirements into comprehensive software deliverables. The platform automates the entire software development lifecycle—from research and agile planning (epics and user stories) to technical specifications, code generation, and automated validation.

## 🏗️ System Architecture

<p align="center">
  <img src="./diagram-expor![Uploading diagram-export-4-22-2026-1_35_26-PM.png…]()
t-4-22-2026-1_35_26-PM.png" alt="System Architecture Diagram" width="100%">
</p>

---

## ✨ Key Features

- **🤖 Multi-Agent Workflow**: Powered by LangGraph, the pipeline progresses autonomously through distinct stages: **Research → Epic → Story → Spec → Code → Validation**.
- **🧠 Retrieval-Augmented Generation (RAG)**: Upload documents (PDF, TXT, DOCX) to enrich the context. Extracts text, chunks data, and stores OpenAI embeddings in a PostgreSQL database using `pgvector` for semantic search.
- **⚡ Real-time Progress Tracking**: Connect via WebSockets to monitor run progress, answer AI clarifying questions, provide feedback, or pause/resume workflows.
- **🔄 Validation Loop**: Runs generated code against linting and tests in an isolated temporary directory, providing detailed JSON validation reports.
- **📦 Versatile Exports**: Download individual artifacts as PDF or Markdown, or export full runs and generated code as structured ZIP bundles.
- **🔒 Secure Authentication**: Robust user management with JWT bearer tokens and admin-only routes for analytics.

---

## 🛠️ Technology Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
- **AI & Orchestration**: [LangGraph](https://python.langchain.com/v0.1/docs/langgraph/), [LangChain](https://python.langchain.com/), OpenAI (Chat + Embeddings)
- **Database & ORM**: PostgreSQL with [pgvector](https://github.com/pgvector/pgvector), SQLAlchemy 2.0 (Async + `asyncpg`), Alembic
- **Real-time & Auth**: WebSockets, Passlib, Python-JOSE (JWT)
- **Web Research**: [Tavily API](https://tavily.com/) (Optional)

---

## 📋 Prerequisites

Before running the application locally, ensure you have the following:

- **Python**: 3.11 or higher
- **PostgreSQL**: Running instance with the `pgvector` extension enabled
- **OpenAI API Key**: Required for LLM calls and embeddings
- **Tavily API Key**: Optional, but highly recommended for enhanced web research

---

## ⚙️ Setup & Installation

### 1. Database Configuration
Create a PostgreSQL database and enable the `pgvector` extension. Connect to your database and run:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Install Dependencies
Clone the repository and install the required Python packages:
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory (next to `requirements.txt`). Use the following template:

**Required:**
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (e.g., `postgresql://user:pass@localhost:5432/dbname`). The app automatically adjusts this for async compatibility (`postgresql+asyncpg://...`). |
| `OPENAI_API_KEY` | Your OpenAI API key for `text-embedding-3-small` and chat models. |
| `SECRET_KEY` | A long, cryptographically secure random string used to sign JWT tokens. |

**Optional:**
| Variable | Default | Description |
|----------|---------|-------------|
| `TAVILY_API_KEY` | — | Enables Tavily-backed web research during the Research phase. |
| `ALGORITHM` | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT token expiration time. |
| `UPLOAD_DIR` | `uploads` | Directory for uploaded RAG documents. |
| `OUTPUT_DIR` | `generated_code`| Directory path for exporting generated code assets. |

*Example `.env`:*
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/product_to_code
OPENAI_API_KEY=sk-...
SECRET_KEY=your-super-secret-key
# TAVILY_API_KEY=tvly-...
```

### 4. Run the Application
Start the FastAPI server. On startup, the app automatically creates the necessary database tables.
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Visit `http://localhost:8000/docs` to access the interactive Swagger UI API documentation.

---

## 🔄 Workflow Stages (Artifacts)

1. **Research**: Processes the initial requirement, executes optional web research, and can ask clarifying questions via WebSocket.
2. **Epic**: Synthesizes research into high-level product epics.
3. **Story**: Breaks down epics into actionable user stories.
4. **Spec**: Translates stories into detailed technical specifications and architecture.
5. **Code**: Generates a complete codebase, mapped as `{"files": { "path/to/file.py": "content", ... }}`.
6. **Validation**: Executes linting and testing in a secure temporary environment, producing a comprehensive JSON validation report.

---

## 🔌 API Overview (v1)

All endpoints are prefixed with `/api/v1` and require an `Authorization: Bearer <token>` header unless specified.

### Authentication
- `POST /users/register` - Create a new account
- `POST /users/login` - Authenticate and receive an access token
- `GET /users/me` - Retrieve current user profile

### Projects & Runs
- `POST /projects/` - Create a new project
- `GET /projects/` - List all user projects
- `POST /runs/` - Start a new workflow run with a requirement prompt
- `GET /runs/{run_id}` - Check workflow status and current stage
- `POST /runs/{run_id}/validate-and-fix` - Trigger the background validation/fix loop

### WebSocket Integration
Monitor and interact with runs in real-time.
- **URL**: `ws://localhost:8000/ws/progress/{run_id}`
- **Supported Messages**: Send JSON payloads with `type` set to `question`, `feedback`, `pause`, or `resume`.

### RAG (Retrieval-Augmented Generation)
- `POST /rag/{project_id}/upload` - Upload PDF, TXT, or DOCX files for project context
- `GET /rag/{project_id}/search` - Perform semantic search via pgvector over document chunks
- `DELETE /rag/{document_id}` - Remove a document and its embeddings

### Exports & Artifacts
- `GET /artifacts/{id}` - Fetch raw artifact JSON
- `GET /artifacts/{id}/export/pdf` - Export an artifact as a PDF
- `GET /artifacts/{id}/export/markdown` - Export an artifact as Markdown
- `GET /artifacts/run/{run_id}/export/full-report` - Download a complete ZIP report of the run

---

## 🗂️ Project Structure

```text
app/
├── main.py                 # FastAPI application, CORS, WebSocket mounts, and startup logic
├── core/                   # Configuration, JWT security, logging, and WS manager
├── db/                     # Async SQLAlchemy engine and session dependency
├── api/v1/                 # API routers (users, projects, runs, artifacts, rag, admin)
├── workflows/              # LangGraph orchestrator and state definitions
├── agents/                 # Specialized AI agents (research, epic, story, spec, code, validation)
├── models/                 # SQLAlchemy ORM definitions
├── schemas/                # Pydantic validation models
├── services/               # Core business logic (RAG service, Export service)
└── utils/                  # Helper functions and utilities
requirements.txt            # Python dependencies
```

---

## 📄 License
Use and modify for your own projects. No formal license file is included by default.
