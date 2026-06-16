# Zero to One

Turn a raw idea into a structured, living project plan — with an agent that knows where you are.

## Prerequisites

- Python 3.12+
- Node.js 18+

## Installation

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

### Agent (port 8001)

```bash
cd packages/agent
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

### Frontend (port 5173)

```bash
cd packages/frontend
npm install
```

### Environment variables

Copy `.env.example` to `.env` and fill in your Gemini API key:

```bash
cp .env.example .env
```

## Running

Open three terminals:

```bash
# Terminal 1 — Backend
cd packages/backend && uvicorn app.main:app --reload

# Terminal 2 — Agent
cd packages/agent && uvicorn app.main:app --reload --port 8001

# Terminal 3 — Frontend
cd packages/frontend && npm run dev
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Agent: http://localhost:8001
