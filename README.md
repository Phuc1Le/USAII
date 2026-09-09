# Stella

> **Turn a raw idea into a structured, living project plan — with an agent that remembers your progress.**

## Demo Video
youtube.com/watch?v=KZgev5keaZI&source_ve_path=NzY3NTg&embeds_referring_euri=https%3A%2F%2Fdevpost.com%2F

## Why

Most AI assistants can answer questions, but they struggle to guide users through long-term projects.

When starting a software project, people often have vague ideas but don't know how to turn them into concrete milestones. Existing chatbots also lose context over time, forcing users to repeatedly explain previous decisions.

We built Stella to explore whether an AI agent could act as a long-term project planning partner—clarifying ideas, generating structured plans, and remembering project context across multiple conversations.

## What Stella Does

Stella guides users from idea to execution in four stages.

1. Clarifies vague ideas through an adaptive interview.
2. Generates project goals and milestones.
3. Builds an actionable project plan.
4. Acts as a context-aware assistant throughout the project.

Unlike a traditional chatbot, Stella stores project state so conversations remain grounded in previous decisions instead of starting over every session.

## Core Features

- **Idea Clarification** — Agent detects vagueness and asks targeted questions to hone your vision
- **Goal Suggestion** — Proposes 3–5 goals scaled by ambition with clear scope definitions
- **Plan Generation** — Creates ordered steps with timelines, milestones, and concrete tasks
- **Focused Chat** — Chat with the agent grounded in your specific project context and plan
- **Agent Tools** — During chat the agent can look up its own milestones, step details, past decisions, and the web instead of guessing
- **Task Management** — Check off tasks, track progress through milestones, and celebrate wins
- **Project Memory** — Agent retains your project's plan and decisions for consistent, contextual help
- **Accounts** — Start using Stella immediately with no sign-up; register later and the work you already did comes with you

## How It Works

Stella is a full-stack application built as three independently deployable services:

| Service | Port | Tech stack |
|---------|------|---------|
| **Frontend** | 5173 | React + TypeScript UI |
| **Backend API** | 8000 | FastAPI server, Pydantic, SQLAlchemy |
| **Agent Service** | 8001 | Python agent powered by Gemini |

**Data Store:** SQLite by default, PostgreSQL in Docker — the same Alembic migrations run on both
**Styling:** CSS with responsive design
**Real-time Chat:** Server-Sent Events (SSE) for streaming agent responses

### Decoupled Services

We separated the frontend, backend, and AI agent into independent services.

This keeps business logic isolated from prompting logic, allows the agent to evolve independently, and makes replacing the underlying LLM straightforward.

### Persistent Project Memory

Projects, tasks, milestones, decisions and conversations are stored separately, allowing the agent to retrieve project-specific decision throughout a user's workflow.

### Accounts and Access

Every visitor gets an anonymous account on their first request, so nothing is gated behind a sign-up form. Registering attaches an email and password to that same account, which is why the projects made before signing up are still there afterwards.

Once an account has a password it can only be reached with a signed token — the anonymous identifier stops working for it, so signing up never leaves a way in that skips the password. Every project route is scoped to its owner, and routes addressed by an id check ownership through the project they belong to.

## What I Learned

Building Stella taught me that most of the complexity wasn't prompting the LLM—it was managing application state around it.

Separating the agent from the backend, defining API contracts first, and maintaining conversational memory made the system significantly easier to extend. To continue this project, we are introducing retrieval-augmented memory for Decisions retrieval, production deployment, context caching, and cross step memory.

## Prerequisites

- **Python** 3.12 or higher
- **Node.js** 18 or higher
- **Gemini API key** — required for the agent
- **Docker** — optional, only for the Docker route below

## Running with Docker (recommended)

```bash
cp .env.example .env
# edit .env and add your GEMINI_API_KEY
docker compose up -d --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Agent: http://localhost:8001

This route gives you PostgreSQL, which the manual route does not — decision search needs pgvector and returns nothing on SQLite.

Stop with:

```bash
docker compose down
```

## Running manually

### 1. Install dependencies

```bash
# from the repo root
cp .env.example .env
# edit .env and add your GEMINI_API_KEY
```

**Backend**

```bash
cd packages/backend
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

**Agent**

```bash
cd packages/agent
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

**Frontend**

```bash
cd packages/frontend
npm install
```

### 2. Run the three services

One terminal each, started in this order — the backend calls the agent, and the frontend calls the backend.

**Terminal 1 — Agent** (`packages/agent`)
```bash
uvicorn app.main:app --reload --port 8001
```

**Terminal 2 — Backend** (`packages/backend`)
```bash
uvicorn app.main:app --reload --port 8000
```

Database migrations run automatically on startup; there is no separate migration step.

**Terminal 3 — Frontend** (`packages/frontend`)
```bash
npm run dev
```

Then open **http://localhost:5173**.

Set `USE_MOCK_AGENT=true` to run the backend and frontend without the agent at all — every LLM call returns a canned response, which is enough to work on the UI without spending quota.

### 3. Environment variables

Everything lives in one `.env` at the repo root. Start from `.env.example`.

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEMINI_API_KEY` | *required* | API key for Gemini |
| `GEMINI_MODEL` | `gemini-3.6-flash` | Model used for every text call |
| `EMBEDDING_MODEL` | `gemini-embedding-001` | Model used for decision embeddings |
| `DATABASE_URL` | `sqlite:///./app.db` | Postgres URL when running under Docker |
| `AGENT_URL` | `http://localhost:8001` | Where the backend reaches the agent |
| `BACKEND_URL` | `http://localhost:8000` | Where the agent reaches the backend, for its tools |
| `USE_MOCK_AGENT` | `false` | Return canned responses instead of calling Gemini |
| `JWT_SECRET` | *dev key* | Signs login tokens. **Set this before deploying** — the fallback is public |
| `JWT_EXPIRE_MINUTES` | `10080` (7 days) | How long a login lasts |
| `INTERNAL_API_TOKEN` | *empty* | Shared secret for `/internal/*`. Empty leaves those routes open; **set before deploying** |
| `ALLOWED_ORIGINS` | localhost dev ports | Comma-separated browser origins allowed to call the backend |
| `SERP_API_KEY` | *empty* | Optional; only the agent's `web_search` tool needs it |
| `CLARITY_THRESHOLD` | `0.7` | Score above which an idea is considered clear enough to plan |
| `CHAT_SUMMARY_TRIGGER` | `6` | Messages before chat summarization starts |
| `CHAT_SUMMARY_KEEP` | `3` | Recent messages left out of the summary |
| `CHAT_SUMMARY_RE_EVERY` | `2` | Re-summarize every N messages after that |
| `DECISION_SEARCH_MIN_SCORE` | `0.5` | Similarity cutoff for decision search |

The backend logs a warning at startup for each of `JWT_SECRET` and `INTERNAL_API_TOKEN` that is unset. Generate either with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Tests

```bash
cd packages/backend
pip install -r requirements-dev.txt
python -m pytest                  # 49 tests: projects, tasks, chat, auth, ownership
```

They run against a throwaway SQLite database with `USE_MOCK_AGENT`, so they need no Gemini key and cost nothing. Alembic migrations are applied to that database on startup, which means the migrations are covered too.

```bash
cd packages/agent
python -m pytest test_prompts.py  # prompt builders
```

`packages/agent/test_tools.py`, `test_react.py`, and `test_react_step4.py` are manual scripts rather than pytest — they make real Gemini and API calls to check the agent's tool selection, which a mock cannot verify. Run them with `python <file>` while the services are up.

## API Documentation

### Backend API
- **Route:** `http://localhost:8000/docs`
- **File:** [contracts/openapi.yaml](contracts/openapi.yaml)

### Agent API
- **Route:** `http://localhost:8001/docs`
- **File:** [contracts/agent_api.yaml](contracts/agent_api.yaml)
