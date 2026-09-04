# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Stella ("Zero to One"): turns a raw idea into a structured project plan via an LLM agent, then acts as a
context-grounded chat partner for the project's lifecycle. Three independent services in `packages/`:
`backend` (FastAPI + SQLite/PostgreSQL, port 8000), `agent` (FastAPI + Gemini, port 8001), `frontend`
(React 19 + Vite, port 5173). The backend never calls Gemini directly — it always proxies through the
agent service over HTTP (`AGENT_URL`, see `packages/backend/app/agent_client.py`).

## Commands

### Backend (`packages/backend`)
```bash
uvicorn app.main:app --reload --port 8000     # run (venv must be active)
python -m pytest test_db.py -v                # NOTE: test_db.py is a manual DB-inspection script,
                                               # not real pytest tests (no asserts) — it prints table contents
```

### Database migrations (`packages/backend`)
```bash
# generate a new migration after editing models
python -m alembic revision --autogenerate -m "description of change"

# apply all pending migrations
python -m alembic upgrade head

# roll back the last migration
python -m alembic downgrade -1

# show current revision
python -m alembic current

# see migration history
python -m alembic history
```
Migrations run automatically when the backend starts (`init_db()` calls `command.upgrade("head")`).
To switch from SQLite to PostgreSQL, set `DATABASE_URL=postgresql://user:pass@host:5432/dbname` in
`.env` — the same Alembic migrations work on both.

### Decision embeddings (backend data maintenance)
Decisions get a `gemini-embedding-001` vector (3072 dims) in `Decision.embedding`, generated in a
background task right after each decision is saved (intake clarifying answers and chat `DECISION:`
extraction). To backfill rows saved before embeddings existed (or any rows whose background embed
failed):

```bash
python -m app.backfill_embeddings     # postgres only; re-runnable (skips non-NULL rows)
```

The agent exposes `POST /agent/embed`; the backend proxies through it (`agent_client.embed_text`,
with a deterministic mock branch under `USE_MOCK_AGENT`). Embedding writes are skipped on SQLite.

Semantic search over decisions lives in `GET /internal/decisions/search` (backend) and the
`query_decisions` tool function (`packages/agent/app/tools.py`): the backend embeds the query via
`agent_client.embed_text`, then runs a project-scoped cosine-similarity search (`Decision.embedding
<=> query_vec`, `crud.search_decisions`) with a `min_score` cutoff (`DECISION_SEARCH_MIN_SCORE`,
default 0.5). PostgreSQL only — returns `[]` on SQLite. The tool is not yet wired into the chat
ReAct loop.

### Agent (`packages/agent`)
```bash
uvicorn app.main:app --reload --port 8001     # run (venv must be active; requires GEMINI_API_KEY unless under pytest)
python -m pytest test_prompts.py -v           # real unit tests: prompt builders return non-empty strings
python -m pytest test_prompts.py::test_all_prompt_builders_return_non_empty_strings  # single test
python test_tools.py [fixture.json]           # integration script, NOT pytest — requires the agent server
                                               # already running on :8001; hits every /agent/* route live
                                               # against a fixture from fixtures/ (default idea_clear.json)
```

### Frontend (`packages/frontend`)
```bash
npm run dev       # vite dev server on :5173
npm run build     # tsc -b && vite build
npm run lint      # eslint .
```

Root `.env` (next to README.md) holds `GEMINI_API_KEY`, `AGENT_URL`, and `DATABASE_URL`.
`packages/backend/app/config.py` is the single config module for the backend: it loads both the root `.env`
and any local `packages/backend/.env` on import, then exports all settings as module-level variables
(`DATABASE_URL`, `AGENT_URL`, `USE_MOCK_AGENT`, `CHAT_SUMMARY_*`). Both `main.py` and `agent_client.py`
import from `config` — there is no more scattered `load_dotenv()` or inline `os.environ.get()`.
The agent has its own `packages/agent/app/config.py` with the same two-tier loading pattern.

## Architecture

### Service boundary and why it exists
The agent service is a thin, stateless wrapper around Gemini: every route builds a prompt
(`agent/app/prompts.py`), calls `json_call`/`stream_text` (`agent/app/llm.py`), and returns/streams the
result — it holds no DB connection and no session state. The backend owns all persistence (SQLite via
SQLAlchemy) and orchestrates multi-step flows by calling the agent and then writing results to the DB.
`packages/backend/app/agent_client.py` is the single seam between the two: every function there has a
`USE_MOCK_AGENT` branch that returns a canned response instead of calling the agent over HTTP, which is
what lets the backend run standalone for frontend development without Gemini access.

### Backend request flow (`packages/backend/app/main.py`)
- Route handlers stay thin: they call `agent_client` for anything LLM-shaped and `crud` for anything
  DB-shaped, then serialize with `serializers`.
- `POST /api/v1/projects` is the key multi-step flow: create the project row → call
  `agent_client.generate_plan` → persist steps + milestones from the plan → reload and return. If you
  change plan shape, `schemas.PlanResponse`/`StepPlan`/`MilestonePlan`, `crud.create_steps_from_plan`, and
  the agent's `PlanResponse` schema all have to move together.
- Tasks are generated lazily: `GET /api/v1/steps/{id}/tasks` only calls the agent
  (`agent_client.generate_tasks`) the first time a step has no tasks yet, then persists and reuses them.
- Chat (`POST /api/v1/chat/sessions/{id}/messages`) streams via SSE end-to-end: frontend → backend →
  agent, all `data: {...}\n\n` framed, terminated by a literal `data: [DONE]\n\n`. The backend saves the
  user's new message to the DB *before* building the agent request, so `history` is built from
  `session.messages[:-1][-10:]` (`main.py`) — excluding the just-saved message, which is sent
  separately as `new_message` — to avoid sending the same message twice. The backend re-parses the
  agent's own SSE stream token-by-token (see `real_stream()`) to accumulate the full response so it can
  persist it after the stream ends — the client only ever talks to the backend, never to the agent
  service directly.
- Project-returning routes (`get_all_projects`/`get_project`/`update_project` in `crud.py`) eager-load
  `steps`→`tasks`/`dependencies` and `milestones` via `selectinload(...)` — none of the relationships in
  `models.py` set a non-default `lazy` strategy, so an un-optioned query becomes an N+1 once
  `serializers.serialize_project`/`serialize_step` loop over them. `update_project` deliberately does
  *not* call `db.refresh(project)` after committing — `refresh()` expires relationship attributes too,
  which would silently undo the eager load right before `serialize_project` runs on the same object.
  `get_step_chat_sessions` eager-loads `.messages` for the same reason (it's read in a loop while
  building chat context in the `/agent/chat` handler's prior-step-summary assembly).
- `_maybe_summarize` never touches the `ChatSession.messages` relationship directly — it uses
  `crud.get_len_message` (a `COUNT` query), `get_messages_range` (offset/limit), and `get_first_message`
  instead, so counting/slicing messages doesn't require loading the whole collection into memory.
- Rolling chat summarization (`_maybe_summarize`) runs as a `BackgroundTasks` job after the chat response
  is sent, not inline in `send_message` — otherwise every turn crossing the threshold would block the SSE
  stream on a full extra Gemini round-trip. `send_message` schedules `_summarize_in_background`, which
  opens its own DB session via `session_scope()` (`database.py`) since the request's session is closed by
  the time the background task runs. It fires once `msg_count >= CHAT_SUMMARY_TRIGGER`, then again every
  `CHAT_SUMMARY_KEEP + CHAT_SUMMARY_RE_EVERY` messages after that. It always resends the session's first
  message alongside whatever's new, because that message carries the original project context.
  Summarization failures are logged (`logger.exception`) but swallowed — chat must keep working even if
  summarization breaks. Because background tasks for the same session can run concurrently (e.g. two
  messages sent in quick succession) and finish out of order, `crud.update_session_summary` refuses to move
  `summary_message_count` backwards — the guard prevents bookmark corruption but does not prevent both
  tasks from independently calling Gemini before either commits, so an occasional duplicate summarization
  call is possible and accepted as a low-cost tradeoff.
- `DECISION:`-prefixed lines in an assistant response are parsed out of the finished stream and persisted
  as `Decision` rows — this is the only place decisions get written, and it's a plain string convention
  from the chat prompt, not a structured field the agent returns.

### Data model (`packages/backend/app/models.py`)
`Project 1—N Step 1—N Task`, plus `Milestone` (optionally tied to a `Step`), `ChatSession 1—N ChatMessage`,
`StepDependency` (join table, currently written but not read anywhere in `main.py`), and `Decision`
(project-scoped free-text log). Several columns are string enums documented only as comments on the model
(`Project.status`, `Step.status`, `Task.status`, `ChatSession.scope_type`, `ChatMessage.role`) — there is
no DB-level constraint, so validate against those comments rather than assuming the column accepts
anything.

Schema changes are managed via Alembic migrations (not `create_all`). The engine, session factory, and
`init_db` live in `database.py` (was inline in models.py). On startup `init_db()` calls
`alembic upgrade head` — no manual migration step is required for deployment. The database URL is
read from `DATABASE_URL` (defaults to `sqlite:///./app.db`) via `config.py`; SQLite gets
`check_same_thread=False` automatically.

### Agent internals (`packages/agent/app`)
- `main.py` routes are all one-shot: build a prompt from typed request schemas, call Gemini, return a
  typed response — except `/agent/chat`, which streams token-by-token via `stream_text`.
- `/agent/chat`'s prompt is not a flat string like the other routes: `build_chat_prompt` (`prompts.py`)
  returns a `ChatPrompt(system_instruction, contents)` named tuple. `system_instruction` holds the fixed
  rules text, the stable project-context JSON, and the rolling summary — nothing there was "said" by
  either party, so it's not part of the conversation. `contents` is a `list[types.Content]`, one
  role-tagged turn per real message (`history` + the latest message), built via `_to_gemini_role()`,
  which maps the wire format's `"assistant"` to Gemini's own `"model"` role — that mapping exists only
  at this one boundary; the DB, backend API, and frontend all use `"assistant"` and must keep doing so.
  `stream_text` (`llm.py`) takes `contents` and `system_instruction` separately and passes them to
  Gemini as `contents=` and `GenerateContentConfig(system_instruction=...)`.
- `_normalize_clarity` is applied after every clarity call (`/agent/clarity` and `/agent/clarity/answers`)
  to clamp `clarity_score` to [0,1], recompute `needs_clarification` from `CLARITY_THRESHOLD`, cap
  questions at 3, and inject a fallback question if the model claims low clarity but returned none.
- `config.py` loads env at import time and will raise if `GEMINI_API_KEY` is missing — *unless* `pytest`
  is in `sys.modules`, which is how `test_prompts.py` can import the app without a real key.
- Prompt text lives entirely in `prompts.py`; if you change what a route expects back from Gemini, the
  prompt's instructions and the corresponding Pydantic response schema in `schemas.py` must stay in sync
  (Gemini is called with `response_schema=` for structured JSON, so drift there causes a 502 from
  `json_call`, not a silent shape mismatch).

### Frontend (`packages/frontend/src`)
- No router library: `App.tsx` reads `window.location.pathname` and gates on `"/home"` vs `"/dashboard"`,
  manipulating history with a hand-rolled `navigate()` (pushState + manual `popstate` dispatch).
- Client-side project state is persisted to `sessionStorage` (`zero-to-one:projects`,
  `zero-to-one:last-project`) as the source of truth for "which project(s) exist" and "which is selected"
  — the backend is not re-queried for the project list on navigation, *except* as a fallback: `App.tsx`
  has an effect that calls `GET /projects` only when local `projects` state is empty (a fresh tab/session
  has no `sessionStorage` yet even though the backend already has projects), then hydrates both state
  and storage from that response.
- In `IntakeFlow.tsx`'s clarifying-question loop, "Skip question" and "Skip assessment" both explicitly
  exclude the in-progress (unsaved) answer and force it blank before advancing — neither should let
  whatever's currently typed leak into `confirmedAnswers` or the agent's re-assessment call. "Skip
  assessment" only re-assesses (calls `/projects/intake/answers`) if at least one earlier question in
  the round was actually answered; otherwise it skips straight to goal suggestions, same as
  `submitClarifyingAnswers` short-circuiting when a whole round ends up blank.
- `features/intake/` is the pre-project-creation flow (category/idea intake → clarify → goals → plan
  preview); `features/project/` is the post-creation dashboard. `api/client.ts` is the only place that
  knows the backend's base URL and SSE framing (`streamChat` parses `data: ...\n\n` the same way the
  backend parses the agent's stream).

## Contracts

`contracts/` is documentation, not enforced/generated code — `openapi.yaml` (backend),
`agent_api.yaml` (agent), `domain-glossary.md` (shared vocabulary: Project/Plan/Step/Task/Milestone/Focus),
and `tool-specs.md` (agent tool specs). When changing a route's request/response shape, update the
matching contract file by hand; nothing checks that they stay in sync with the Pydantic schemas.
