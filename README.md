# Stella

> **Turn a raw idea into a structured, living project plan — with an agent that knows where you are.**

Stella is an intelligent project planning assistant that transforms fuzzy ideas into actionable project plans. An AI agent interviews you to clarify your vision, suggests scaled goals, generates a structured plan with steps and milestones, and then becomes a focused thinking partner throughout your project's lifecycle.
## Demo Video
youtube.com/watch?v=KZgev5keaZI&source_ve_path=NzY3NTg&embeds_referring_euri=https%3A%2F%2Fdevpost.com%2F

## 🎯 Core Features

- **Idea Clarification** — Agent detects vagueness and asks targeted questions to hone your vision
- **Goal Suggestion** — Proposes 3–5 goals scaled by ambition with clear scope definitions
- **Plan Generation** — Creates ordered steps with timelines, milestones, and concrete tasks
- **Focused Chat** — Chat with the agent grounded in your specific project context and plan
- **Task Management** — Check off tasks, track progress through milestones, and celebrate wins
- **Project Memory** — Agent retains your project's plan and decisions for consistent, contextual help

## 🏗️ Architecture

Stella is a full-stack application split into three independent services:

| Service | Port | Purpose |
|---------|------|---------|
| **Frontend** | 5173 | React + TypeScript UI for idea intake and plan management |
| **Backend API** | 8000 | FastAPI server; handles projects, plans, chat sessions, and task persistence |
| **Agent Service** | 8001 | Python agent powered by LLMs; handles clarification, planning, and chat responses |

**Data Store:** SQLite (single-file, included in repo)  
**Styling:** CSS with responsive design  
**Real-time Chat:** Server-Sent Events (SSE) for streaming agent responses

## 📋 Prerequisites

- **Python** 3.12 or higher
- **Node.js** 18 or higher
- **Gemini API key** (for agent LLM calls; set in `.env`)

## 🚀 Quick Start

### 1. Backend Setup (port 8000)

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

### 4. Environment Variables

Create a `.env` file in the **project root** (next to `README.md`) with your Gemini API key:

```env
GEMINI_API_KEY=your_api_key_here
AGENT_URL=http://localhost:8001
```

Alternatively, copy from `.env.example` if it exists and fill in your key.

## 🔧 Running the Application

You'll need three terminals, one for each service:

**Terminal 1 — Backend (FastAPI)**
```bash
cd packages/backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Agent Service**
```bash
cd packages/agent
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uvicorn app.main:app --reload --port 8001
```

**Terminal 3 — Frontend (React + Vite)**
```bash
cd packages/frontend
npm run dev
```

Once all three are running, open your browser to **http://localhost:5173**.

### Service URLs
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000 (REST API)
- **Agent Service:** http://localhost:8001 (Agent API)
- **Backend Docs:** http://localhost:8000/docs (Swagger UI)
- **Agent Docs:** http://localhost:8001/docs (Swagger UI)

## 📁 Project Structure

```
.
├── README.md                    # This file
├── contracts/                   # API contracts & domain glossary
│   ├── openapi.yaml            # Backend API specification
│   ├── agent_api.yaml          # Agent API specification
│   ├── domain-glossary.md      # Shared vocabulary & concepts
│   └── tool-specs.md           # Agent tool specifications
│
├── packages/
│   │
│   ├── backend/                 # FastAPI backend (Python)
│   │   ├── app/
│   │   │   ├── main.py         # FastAPI app & routes
│   │   │   ├── models.py       # SQLAlchemy database models
│   │   │   ├── schemas.py      # Pydantic request/response schemas
│   │   │   ├── crud.py         # Database CRUD operations
│   │   │   ├── database.py     # Database configuration
│   │   │   ├── agent_client.py # Client for agent service
│   │   │   ├── serializers.py  # Response serialization
│   │   │   └── config.py       # App configuration
│   │   ├── requirements.txt
│   │   └── test_db.py
│   │
│   ├── agent/                   # Agent service (Python + LLM)
│   │   ├── app/
│   │   │   ├── main.py         # FastAPI app & agent endpoints
│   │   │   ├── llm.py          # LLM client (Gemini)
│   │   │   ├── prompts.py      # System prompts
│   │   │   ├── schemas.py      # Request/response schemas
│   │   │   └── config.py       # Agent configuration
│   │   ├── fixtures/           # Test data
│   │   ├── requirements.txt
│   │   ├── test_prompts.py
│   │   └── test_tools.py
│   │
│   └── frontend/                # React + TypeScript frontend
│       ├── src/
│       │   ├── App.tsx          # Root component
│       │   ├── main.tsx         # Entry point
│       │   ├── index.css        # Global styles
│       │   ├── api/             # HTTP client & hooks
│       │   │   ├── client.ts    # Fetch wrapper
│       │   │   ├── hook.ts      # React Query hooks
│       │   │   └── types.ts     # API types
│       │   └── features/        # Feature modules
│       │       ├── intake/      # Idea intake flow
│       │       └── project/     # Project dashboard
│       ├── package.json
│       ├── vite.config.ts
│       └── tsconfig.json
```

## 🔄 User Flow

1. **Idea Intake** — User selects a category, describes their idea, and writes a brief statement
2. **Clarification Loop** — Agent assesses idea clarity; if vague, asks targeted questions to improve
3. **Goal Suggestion** — Agent proposes 3–5 goals at different ambition levels
4. **Plan Generation** — Agent creates a structured plan with steps, tasks, and milestones
5. **Project Dashboard** — User views and manages the plan, can check off tasks
6. **Focused Chat** — User can focus the chat on a specific step or the entire project and ask questions

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|---|
| **Frontend** | React 19, TypeScript, Vite, React Query, React Markdown |
| **Backend** | FastAPI, SQLAlchemy, SQLite, Pydantic |
| **Agent** | Python, Gemini API, httpx |
| **DevTools** | ESLint, TypeScript compiler, Vite |

## 🧪 Testing

### Backend Tests
```bash
cd packages/backend
source .venv/bin/activate
python -m pytest test_db.py -v
```

### Agent Tests
```bash
cd packages/agent
source .venv/bin/activate
python test_prompts.py
python test_tools.py
```

### Frontend Linting
```bash
cd packages/frontend
npm run lint
```

## 📚 API Documentation

### Backend API
- **Route:** `http://localhost:8000/docs`
- **File:** [contracts/openapi.yaml](contracts/openapi.yaml)
- **Key endpoints:**
  - `POST /api/v1/projects/intake` — Submit initial idea
  - `POST /api/v1/projects/{id}/goals` — Get goal suggestions
  - `POST /api/v1/projects` — Create project from plan
  - `POST /api/v1/chat` — Send chat message

### Agent API
- **Route:** `http://localhost:8001/docs`
- **File:** [contracts/agent_api.yaml](contracts/agent_api.yaml)
- **Key endpoints:**
  - `POST /clarify` — Assess idea clarity
  - `POST /suggest-goals` — Generate goal options
  - `POST /generate-plan` — Create project plan
  - `POST /chat` — Chat with agent

## 📖 Domain Concepts

See [contracts/domain-glossary.md](contracts/domain-glossary.md) for the full shared vocabulary.

| Term | Definition |
|------|---|
| **Project** | One idea being taken to a goal; contains category, description, idea, goal, and plan |
| **Plan** | Steps + milestones + timeline for a project |
| **Step** | A major phase with order, dependencies, date range, status, and tasks |
| **Task** | A concrete checkbox-level to-do inside a step |
| **Milestone** | A checkpoint marker tied to completing a step |
| **Focus** | What the agent is grounded in: a single step or the whole project |

## 🚦 Development Workflow

1. **Start all three services** (see "Running the Application" above)
2. **Make changes** to any service — they auto-reload via `--reload`
3. **Test in browser** at http://localhost:5173
4. **Check API docs** for schema changes at `/docs` endpoints
5. **Run tests** before pushing

## 🐛 Troubleshooting

### "Connection refused" on port 5173, 8000, or 8001
- Ensure all three services are running in separate terminals
- Check that ports are not blocked by firewall or other apps
- Try different ports by modifying service startup commands

### "Module not found" or import errors
- Ensure you ran `pip install -r requirements.txt` in both backend and agent venvs
- Ensure you ran `npm install` in the frontend folder
- Verify Python venv is activated before running services

### Agent responses are slow or empty
- Check that `GEMINI_API_KEY` is set correctly in `.env`
- Verify agent service is running on port 8001
- Check backend logs for errors communicating with agent

### Frontend doesn't load
- Clear browser cache (Ctrl+Shift+Delete or Cmd+Shift+Delete)
- Check that Vite is running on port 5173
- Check browser console for error messages

## 📝 Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEMINI_API_KEY` | *required* | API key for Gemini LLM |
| `AGENT_URL` | `http://localhost:8001` | URL for agent service (from backend perspective) |
| `USE_MOCK_AGENT` | `false` | Use mock responses instead of real agent (for testing) |
| `CHAT_SUMMARY_TRIGGER` | `10` | Messages before chat summarization |
| `CHAT_SUMMARY_KEEP` | `3` | Summaries to retain in memory |
| `CHAT_SUMMARY_RE_EVERY` | `2` | Re-summarize every N summaries |

## 🤝 Contributing

This is a demo build. To extend it:

1. **Read the PRD:** [zero-to-one-PRD (1).md](zero-to-one-PRD%20(1).md) — explains the full vision and post-demo features
2. **Check contracts:** [contracts/](contracts/) — API specs and tool definitions
3. **Follow the stack:** Frontend changes in `packages/frontend/`, backend in `packages/backend/`, agent in `packages/agent/`
4. **Keep domains in sync:** Changes to data models must be reflected in schemas, CRUD, and serializers

## 📄 License

This project is part of the "Stella" initiative. See [LICENSE](LICENSE) if present.

## 🙋 Questions?

Refer to [contracts/domain-glossary.md](contracts/domain-glossary.md) for vocabulary and [contracts/tool-specs.md](contracts/tool-specs.md) for agent tool details. The [PRD](zero-to-one-PRD%20(1).md) contains the full product vision and reasoning.