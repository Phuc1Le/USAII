# Stella

> **Turn a raw idea into a structured, living project plan — with an agent that remember your progress.**

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
- **Task Management** — Check off tasks, track progress through milestones, and celebrate wins
- **Project Memory** — Agent retains your project's plan and decisions for consistent, contextual help

## How It Works

Stella is full-stack application built as three independently deployable services:

| Service | Port | Tech stackc |
|---------|------|---------|
| **Frontend** | 5173 | React + TypeScript UI  |
| **Backend API** | 8000 | FastAPI server, Pydantic |
| **Agent Service** | 8001 | Python agent powered by Gemini |

**Data Store:** SQLite, SQLAlchemy (migrating to PostgreSql...)  
**Styling:** CSS with responsive design  
**Real-time Chat:** Server-Sent Events (SSE) for streaming agent responses

### Decoupled Services

We separated the frontend, backend, and AI agent into independent services.

This keeps business logic isolated from prompting logic, allows the agent to evolve independently, and makes replacing the underlying LLM straightforward.

### Persistent Project Memory

Projects, tasks, milestones, decisions and conversations are stored separately, allowing the agent to retrieve project-specific decision throughout a user's workflow.

## Prerequisites

- **Python** 3.12 or higher
- **Node.js** 18 or higher
- **Gemini API key** (for agent LLM calls; set in `.env`)

## Quick Start

### 1. Backend Setup (port 8000)
- Python 3.12+
- Node.js 18+
- Docker (optional)

## Running with Docker (recommended)

```bash
cp .env.example .env
# edit .env and add your GEMINI_API_KEY
docker compose up -d --build
```

- Backend: http://localhost:8000
- Agent: http://localhost:8001

Stop with:

```bash
docker compose down
```

## Manual Installation

### Backend (port 8000)

```bash
cd packages/backend
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Agent Setup (port 8001)

```bash
cd packages/agent
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Frontend Setup (port 5173)

```bash
cd packages/frontend
npm install
```


Once all three are running, open your browser to **http://localhost:5173**.
### 4. Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEMINI_API_KEY` | *required* | API key for Gemini LLM |
| `AGENT_URL` | `http://localhost:8001` | URL for agent service (from backend perspective) |
| `USE_MOCK_AGENT` | `false` | Use mock responses instead of real agent (for testing) |
| `CHAT_SUMMARY_TRIGGER` | `10` | Messages before chat summarization |
| `CHAT_SUMMARY_KEEP` | `3` | Summaries to retain in memory |
| `CHAT_SUMMARY_RE_EVERY` | `2` | Re-summarize every N summaries |

### 5. Running the application
You'll need three terminals, one for each service:

**Terminal 1 — Backend (FastAPI)**
```bash
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Agent Service**
```bash
uvicorn app.main:app --reload --port 8001
```

**Terminal 3 — Frontend (React + Vite)**
```bash
npm run dev
```

## API Documentation

### Backend API
- **Route:** `http://localhost:8000/docs`
- **File:** [contracts/openapi.yaml](contracts/openapi.yaml)

### Agent API
- **Route:** `http://localhost:8001/docs`
- **File:** [contracts/agent_api.yaml](contracts/agent_api.yaml