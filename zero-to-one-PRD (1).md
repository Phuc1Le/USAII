# Zero to One — Product Requirements Document (DEMO build)

**Status:** Demo plan v2 · **Timeline: 5 days** · **Scope: DEMO ONLY**
**Stack (locked):** React + TypeScript (frontend) · FastAPI / Python (backend) · OpenAI (agent) · **SQLite** (data)
**Team:** 3 engineers, split by layer (Frontend · Backend · Agent)
**No authentication. No Docker.** (Both are post-demo — see §16.)
**Last updated:** 2026-06-16

---

## 0. How to read this doc

This is the **demo cut** of the PRD. Sections 1–7 are *what we're building* (trimmed to what fits in 5 days). Sections 8–14 are *how it's built*. **Section 15 is Phase 0 — the only phase with hour-by-hour instructions, because it's the hard part; the rest can be vibe-coded against the contract Phase 0 produces.** Section 16 lists what we cut and how to add it back later. **Appendix A explains the `contracts/` folder in plain language.**

`[DEMO]` marks a deliberate simplification for the 5-day build. `[POST-DEMO]` marks something intentionally deferred.

---

## 1. Vision (unchanged)

People rarely fail an idea for lack of motivation — they fail because they don't know the *sequence* of steps from "I have an idea" to "I shipped a thing," and they get stuck mid-way with no one to ask. **Zero to One** turns a raw idea into a structured, living plan (steps → tasks → milestones on a timeline) and pairs it with an agent that knows *where you are in that plan*, so help is grounded in the actual project.

**Demo one-liner:** *Type a fuzzy idea, watch the agent interview you, pick a goal, and get a real project plan you can then chat through — with an agent that remembers the plan.*

---

## 2. Demo scope (what we will and won't show)

**The demo spine (must work end-to-end):**
1. Pick a category + write a description + write the idea.
2. **Clarification loop** — agent detects vagueness and asks targeted questions. *(Great live moment.)*
3. **Goal suggestion** — agent proposes scaled goals; user picks.
4. **Plan generation** — steps + timeline + milestones appear as a real project.
5. **Tasks** inside steps; user can check them off.
6. **Focused chat** — user focuses a step (or whole project) and the agent answers *grounded in that project*. *(The core wow.)*

**Stretch (only if days 4–5 allow, in this order):**
- Milestone **celebration** moment (frontend-only, cheapest crowd-pleaser).
- **"I'm stuck" → decompose** a step into smaller tasks.
- Manual **plan editing**.
- Dependency **soft-lock warnings**.

**Explicitly NOT in the demo (`[POST-DEMO]`):** authentication, multi-user, mobile app, background jobs / overdue alerts, vector search / RAG memory, rolling summarization, cross-project memory, plan version history, agent replan-diff approval.

---

## 3. Personas (unchanged)

- **Capable beginner** — clear-ish idea, limited execution experience, will get stuck. Drives the (stretch) decompose feature.
- **Experienced builder** — wants structure and a thinking partner, edits plans, works out of order. Drives (stretch) editing/soft-locks.

For the demo, design for the **beginner** — that's the more compelling story to show.

---

## 4. Domain model (shared vocabulary — contract-critical)

Everyone, every layer, uses these exact words.

| Concept | Definition |
|---|---|
| **Project** | One idea being taken to its goal. Has `category`, `description`, `idea`, `goal`, `status`, and one `plan`. |
| **Plan** | The steps + milestones + timeline for a project. `[DEMO]` one plan per project; regenerating replaces it. |
| **Step** | A major phase (e.g., "Build the API server"). Has `order`, optional dependencies, an intended date range, a status, and tasks. |
| **Task** | A concrete checkbox-level to-do inside a step. |
| **Milestone** | A checkpoint marker tied to completing a step (drives the celebration moment). |
| **Chat session** | A conversation scoped to a focus target (one step, or the whole project). |
| **Focus / Scope** | What the agent is grounded in: a single step, or the whole project. |
| **Project memory** | `[DEMO]` the project's plan + recorded decisions as plain text, passed into the agent prompt. (`[POST-DEMO]`: structured + embeddings.) |

---

## 5. Core user flow

### 5.1 Idea intake
Pick category/skill/hobby (searchable list + free-text), write a short description, write the idea.

### 5.2 Clarification loop
On submit, the agent scores idea clarity against fixed dimensions (problem, audience, core feature, scope, definition of done). If clear → goal suggestion. If vague → ask ≤3 targeted questions, loop until clear or the user clicks **"Proceed anyway."** (Adaptive: clear ideas aren't punished; vague ones get interviewed.)

### 5.3 Goal suggestion
Agent proposes 3–5 goals scaled by ambition (e.g., for an app: prototype → MVP → production-ready), each with a one-line scope. User picks one or writes their own.

### 5.4 Plan generation
From `idea + goal`, agent generates ordered **steps** with an intended date range and **milestones**. User reviews → commit creates the `Project`.

### 5.5 Tasks inside steps
Each step has tasks. `[DEMO]` generate tasks for a step when it's first opened (lazy), so the initial plan stays readable. User can check/add/edit tasks.

### 5.6 Focused chat
From a step (or the project header) the user clicks **"Focus in chat"** → a chat session scoped to that target. The agent answers grounded in the project's idea, goal, plan, and recorded decisions. Responses **stream** (SSE).

---

## 6. The open questions — demo answers

| Question | Demo answer | Later |
|---|---|---|
| User can't finish a step | Stretch feature: **"I'm stuck" → decompose** into smaller tasks. | Full 5-rung assist ladder. |
| Modify a step / plan | Stretch: direct manual edit. | Versioned plans + agent replan-diff approval. |
| Memory over long sessions | `[DEMO]` stuff plan + recorded decisions into the prompt as text (demo projects are small). | 3-tier memory + summarization. |
| Forget previous steps in step chat? | No — agent always gets the project's idea/goal/plan outline; current step in full detail. | Layered scope with semantic retrieval. |
| Step order / locks | `[DEMO]` any order; stretch: soft-lock **warning** with override (never a hard lock). | Optional per-project strict mode. |

---

## 7. Optional features — all `[POST-DEMO]`

Overdue alerts, cross-project memory: deferred. **Milestone celebration** is the one optional that's worth attempting as a demo stretch because it's frontend-only and delightful.

---

## 8. The Agent: planning loop & tools

OpenAI **function-calling** driven by an explicit **state machine**. State lives in the DB; the agent is re-grounded each turn from stored project state. `[DEMO]` no vector retrieval — context is assembled by reading the project's plan + decisions directly.

### 8.1 State machine (planning loop)

```
IDEA_INTAKE ─▶ CLARIFY ─(clear)─▶ GOAL_SELECT ─▶ PLAN_GEN ─▶ PLAN_REVIEW ─▶ EXECUTION_ASSIST
                 ▲ │                                                              │
                 └─┘ (≤3 Qs, loop; "Proceed anyway" exits)        (focused chat per step/project)
                                                                                  │
                                                              (stretch) decompose_step
```

### 8.2 Tools (OpenAI function schemas)

| Tool | Purpose | Inputs | Output |
|---|---|---|---|
| `assess_idea_clarity` | Score idea, find gaps | `category, description, idea` | `clarity_score 0–1`, `missing_dimensions[]` |
| `ask_clarifying_questions` | Targeted Qs | `idea, missing_dimensions` | `questions[]` (≤3) |
| `suggest_goals` | Scaled goals | `category, idea` | `goals[]{title, scope}` |
| `generate_plan` | Build plan | `idea, goal` | `steps[]{title, deps, date_range}`, `milestones[]` |
| `generate_tasks` | Explode a step | `step, project_context` | `tasks[]{title, detail}` |
| `decompose_step` *(stretch)* | Break a stuck step down | `step, blocker` | `subtasks[]` |

The agent calls back into the **Backend** for any persistence/reads. `[DEMO]` the agent owns **no tables**.

### 8.3 Prompting notes
System prompt encodes role + the rule *"advise and structure; never claim the user's work is done."* `[DEMO]` whole-project context fits in the prompt; no token-budget machinery yet.

---

## 9. System design (demo)

Three tiny services, no Docker. Frontend → Backend over HTTP/SSE; Backend → Agent over HTTP; Agent → OpenAI.

```
┌──────────────┐   HTTP / SSE   ┌──────────────────┐  HTTP   ┌────────────────────┐
│  Frontend    │ ─────────────▶ │   Backend (core) │ ──────▶ │   Agent service    │
│  React :5173 │ ◀───────────── │   FastAPI :8000  │ ◀────── │  FastAPI :8001     │
└──────────────┘                └──────────────────┘         └────────────────────┘
   (Person A)                          (Person B)        │           (Person C) ──▶ OpenAI
                                           │             │
                                           ▼             ▼ (calls Backend to read/write)
                                     ┌───────────┐
                                     │  SQLite   │  app.db (single file)
                                     └───────────┘
```

**Rules:** Frontend talks only to Backend (keeps the OpenAI key server-side, one client contract). Agent talks to OpenAI and back to Backend for data. Backend owns the SQLite file and is the single source of truth. Chat streams Backend → Frontend via **SSE** (one-way token stream; simpler than WebSockets).

---

## 10. Data model (SQLite, via SQLAlchemy `create_all()` — no migrations for demo)

Owned by the Backend engineer. No `users` table for the demo.

| Table | Key columns | Notes |
|---|---|---|
| `projects` | `id, title, category, description, idea, goal, status, created_at` | One per idea. |
| `steps` | `id, project_id, title, description, order_index, status, intended_start, intended_end` | `status ∈ {todo, in_progress, blocked, deferred, done}`. |
| `step_dependencies` | `step_id, depends_on_step_id` | For stretch soft-locks. |
| `tasks` | `id, step_id, title, detail, status, order_index` | Checkbox-level. |
| `milestones` | `id, project_id, title, step_id, achieved_at` | Drives celebration. |
| `chat_sessions` | `id, project_id, scope_type, scope_step_id` | `scope_type ∈ {step, project}`. |
| `chat_messages` | `id, session_id, role, content, created_at` | Transcript. |
| `decisions` | `id, project_id, content, created_at` | `[DEMO]` plain-text project memory. |

---

## 11. API (Backend ↔ Frontend, REST + SSE) — demo set

All under `/api/v1`. (A worked starter spec ships as `contracts/openapi.yaml`.)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/projects/intake` | category+description+idea → clarity result / clarifying questions |
| `POST` | `/projects/intake/answers` | answers → re-assess |
| `POST` | `/projects/goals` | suggested goals |
| `POST` | `/projects` | create project from idea+goal (triggers plan gen) |
| `GET` | `/projects/{id}` | full project: plan, steps, tasks, milestones |
| `GET` | `/steps/{id}/tasks` | lazy-generate + return tasks for a step |
| `PATCH` | `/tasks/{id}` | toggle/edit a task |
| `POST` | `/chat/sessions` | open/get a scoped chat session |
| `POST` | `/chat/sessions/{id}/messages` | send message → **SSE** token stream |
| `POST` | `/steps/{id}/decompose` *(stretch)* | "I'm stuck" |

**Internal (Backend ↔ Agent):** `/agent/clarity`, `/agent/goals`, `/agent/plan`, `/agent/chat` (streamed). Mirrors §8.2.

---

## 12. Tech stack (demo)

| Layer | Choice | Note |
|---|---|---|
| Frontend | React + TypeScript via **Vite** | `npm create vite@latest` |
| Styling | Tailwind CSS (+ optional shadcn/ui) | speed |
| Server state | TanStack Query | caching |
| Streaming client | native **EventSource (SSE)** | matches backend |
| Backend | **FastAPI (Python 3.12)** | async, Pydantic, auto OpenAPI |
| ORM | **SQLAlchemy 2.0**, `create_all()` | `[DEMO]` no Alembic |
| DB | **SQLite** (`app.db`) | zero setup; swap to Postgres later via connection string |
| Agent | FastAPI + **OpenAI SDK** | function calling + streaming |
| Contract→types | OpenAPI → TS codegen (`openapi-typescript`) | FE/BE can't silently diverge |
| Tests | pytest / Vitest | light; demo-grade |
| CI | *optional* GitHub Action: lint + type-check | skip if time-boxed |

Removed for demo: Docker/Compose, Postgres, pgvector, Alembic, Redis/Celery, APScheduler, auth libraries.

---

## 13. Repository layout

Monorepo, three top-level packages (one owner each) + a shared `contracts/`.

```
zero-to-one/
├── packages/
│   ├── frontend/                # Person A — React (Vite) :5173
│   │   └── src/{features,components,api,store}/
│   ├── backend/                 # Person B — FastAPI :8000  (owns SQLite)
│   │   └── app/{routers,models,schemas,services,agent_client}/
│   └── agent/                   # Person C — FastAPI :8001  (owns no tables)
│       └── app/{state_machine,tools,prompts,backend_client}/
├── contracts/                   # SHARED — jointly owned, rarely changed
│   ├── domain-glossary.md       # §4 vocabulary
│   ├── openapi.yaml             # Backend↔Frontend contract
│   ├── agent_api.yaml           # Backend↔Agent contract
│   └── tool-specs.md            # §8.2 agent tool schemas
└── README.md                    # how to run all three
```

**Merge-conflict defense:** (1) one directory per owner → two people rarely touch the same file; (2) `contracts/` is frozen in Phase 0 and changes only via a small PR all three review; (3) everyone builds behind a **mock** so no one waits; (4) the frontend API client is **generated** from `openapi.yaml`, so drift fails fast.

---

## 14. Task split (by layer)

**Person A — Frontend:** intake flow, clarification-question UI, goal picker, plan/timeline view, step view with tasks, "Focus in chat," chat UI with **SSE streaming** + scope toggle, milestone celebration (stretch). Consumes the generated API client.

**Person B — Backend (contract steward):** SQLite schema (§10), all REST endpoints + SSE proxy of the agent stream, business logic (status transitions, lazy task fetch), `agent_client`, persistence of decisions/messages. Publishes `openapi.yaml`.

**Person C — Agent (co-steward of `agent_api.yaml`):** the state machine (§8.1), all tools (§8.2), prompt engineering, OpenAI streaming, assembling project context as text. Calls back to Backend for data.

`contracts/` is jointly owned; changes need all-three review.

---

## 15. PHASE 0 — Foundation (the hard, important part) · ~Day 1 to mid-Day 2

> **Why this phase matters most:** Phase 0 produces the *contract* — the written agreement that lets three people build three pieces simultaneously and have them snap together. Get this right and days 2–5 are smooth parallel work. Skip it and you'll spend day 5 in integration hell. **Do every block below together, in one room / one call.**

### Block 0.1 — Repo + three runnable "hello worlds" (together, ~1 hr)
Goal: everyone can start all three services with one command each.

1. Create the repo and folders from §13. `git init`, push to GitHub.
2. **Frontend:** `npm create vite@latest packages/frontend -- --template react-ts`, then `cd packages/frontend && npm install && npm run dev` → blank page at `http://localhost:5173`.
3. **Backend:** in `packages/backend`: create a venv (`python -m venv .venv && source .venv/bin/activate`), `pip install fastapi uvicorn[standard] sqlalchemy openai`, write `app/main.py` with one endpoint:
   ```python
   from fastapi import FastAPI
   app = FastAPI()
   @app.get("/health")
   def health(): return {"ok": True}
   ```
   Run: `uvicorn app.main:app --reload` → `http://localhost:8000/health`.
4. **Agent:** same as backend but in `packages/agent`, run on port 8001: `uvicorn app.main:app --reload --port 8001`.
5. Write the root `README.md` with these three commands. Commit.
   **Done when:** all three start and respond.

### Block 0.2 — Domain glossary (together, ~30 min)
Paste §4 into `contracts/domain-glossary.md` and agree on the words out loud. This prevents the classic "one of us says *phase*, another says *stage*, another says *step*" bug. Commit.

### Block 0.3 — Agree the data shapes, then write the models (together, ~2–3 hrs) — **most important block**
1. On a shared screen, write **real example JSON** for a Project, Step, Task, Milestone — actual field names and example values. Argue about field names *now*, while it's cheap.
2. Person B turns those into **SQLAlchemy models** (§10) and adds a one-time `Base.metadata.create_all(engine)` on startup so `app.db` is created from the models — **no migration tool needed**.
   **Done when:** running the backend creates `app.db` with the right tables, and everyone agrees the JSON shapes are final-ish.

### Block 0.4 — Write `openapi.yaml` by stubbing the backend (together, ~2–3 hrs)
The easy way to "write" the API contract with FastAPI: **write the Pydantic request/response models and stub each endpoint to return fake data** — FastAPI then *generates* the OpenAPI spec for you.
1. For each endpoint in §11, Person B defines Pydantic `Request`/`Response` models and a stub that returns canned data matching the example JSON from 0.3.
2. Export the spec: visit `http://localhost:8000/openapi.json`, save it (or `curl` it) into `contracts/openapi.yaml`. (Use the starter file we shipped as the template — see the separate `openapi.yaml`.)
3. **This stubbed backend doubles as the Frontend's mock** — Person A points at `http://localhost:8000` and immediately gets correctly-shaped fake data. No separate FE mock server needed.
   **Done when:** `contracts/openapi.yaml` exists and the stubbed backend returns fake projects/plans.

### Block 0.5 — Write `agent_api.yaml` + tool specs (together, ~1–2 hrs)
1. Define the Backend↔Agent calls (`/agent/clarity`, `/agent/goals`, `/agent/plan`, `/agent/chat`) with request/response JSON. Save to `contracts/agent_api.yaml`.
2. Copy the §8.2 tool schemas into `contracts/tool-specs.md` — this is Person C's checklist.
3. Person B writes a **mock agent client**: a function that returns a canned clarity result / plan in the `agent_api.yaml` shape, used when an env flag `USE_MOCK_AGENT=true` is set. Now Backend runs without the real agent.
   **Done when:** Backend works end-to-end with the mock agent; the two contract files are committed.

### Block 0.6 — Each person stands up their workspace (split, ~half day, parallel)
- **Person A:** generate the TS client from `openapi.yaml` (`npx openapi-typescript contracts/openapi.yaml -o src/api/types.ts`), wire TanStack Query, point at the stubbed backend, render the first real screen with fake data.
- **Person B:** confirm all stub endpoints return contract-shaped data with `USE_MOCK_AGENT=true`.
- **Person C:** create `packages/agent/fixtures/` with 2–3 sample ideas, and a script that runs each tool against a fixture and prints output, checking it matches `tool-specs.md`. (Real OpenAI calls fine here — just you, small volume.)

### Phase 0 EXIT CRITERIA (don't start Day 2 until all true)
- [ ] Fresh clone + README → all three services start with one command each.
- [ ] Frontend shows real screens populated by the stubbed backend's fake data.
- [ ] `contracts/` has all four files, committed and agreed by all three.
- [ ] Backend runs with `USE_MOCK_AGENT=true` end-to-end.
- [ ] Agent dev can run tools against fixtures and see contract-shaped output.

**After Phase 0, the contract is law.** Each person works only inside their package; the rest can be vibe-coded.

---

## 15b. Days 2–5 (vibe-codeable against the contract)

- **Day 2–3 — Happy path, real.** Replace mocks with real code behind the contract: intake → clarify → goals → plan → project view. A builds the real screens; B builds real endpoints + SQLite writes; C builds clarity/goals/plan tools. **Integrate midday Day 3** (turn off `USE_MOCK_AGENT`, point FE at the same backend).
- **Day 4 — Focused chat (the wow).** A: chat UI + SSE streaming + scope toggle. B: chat endpoints + SSE proxy + message/decision persistence. C: `EXECUTION_ASSIST` grounded in project text. Integrate.
- **Day 5 — Polish + one stretch + rehearse.** Add the milestone celebration (cheapest win), fix empty/error states, and **rehearse the exact demo path twice**. Pick one stretch feature only if Day 4 finished clean.

---

## 16. What we cut, and how to add it back

| Cut for demo | Add-back path |
|---|---|
| Auth + `users` table | Add a managed provider (Clerk/Auth.js); add `user_id` FKs; scope queries by current user. |
| Postgres + pgvector | Change the SQLAlchemy connection string to Postgres; add pgvector for memory. |
| Migrations | Introduce Alembic, baseline off the current models. |
| Vector/RAG memory | Embed decisions → pgvector; swap the text-stuffing for `retrieve_context` (top-k). |
| Rolling summarization | Add when chat sessions get long. |
| Background jobs / overdue alerts | Add APScheduler (or Celery+Redis) worker + `notifications` table. |
| Plan versioning + replan diff | Add `plans.version` history + diff/approve flow. |
| Docker | Add a Compose file once you have >1 stateful dependency. |

---

## 17. Risks (demo)

| Risk | Mitigation |
|---|---|
| Phase 0 runs long, eats build days | Time-box each block; the starter `openapi.yaml` removes guesswork. |
| OpenAI latency hurts the live demo | Pre-warm; have a recorded fallback of the demo path. |
| Plan/clarity output is mediocre | Iterate prompts against the fixtures on Day 2; keep ideas demo-friendly. |
| Last-day integration surprises | First integration is **Day 3**, not Day 5 — surprises surface early. |

---

## Appendix A — What `contracts/` is, in plain language

`contracts/` is **the written agreement the three of you sign before writing real code.** Its only job: let three people build three separate pieces at the same time and have them fit together — without editing each other's files (the cause of merge conflicts) and without anyone waiting on someone else.

It holds four things:

- **`domain-glossary.md`** — plain-English definitions of Project, Step, Task, etc. Stops the three of you from using three different words for the same thing.
- **`openapi.yaml`** — the **Frontend↔Backend** contract: every endpoint's URL, method, the JSON you send, and the JSON you get back. With FastAPI you don't hand-write it — you write Pydantic models and FastAPI *generates* it. The frontend then runs a tool that reads it and produces TypeScript types, so the compiler refuses to let the frontend call an endpoint wrong. The frontend never waits for the real backend: it builds against the stubbed backend (fake data, right shape), then flips to the real one with no code change.
- **`agent_api.yaml`** — the same idea for the **Backend↔Agent** calls. Backend builds against a fake agent that returns canned, correctly-shaped results; the agent dev builds the real thing to the same shape. Neither blocks the other.
- **`tool-specs.md`** — the agent's OpenAI tool schemas (inputs/outputs). The agent dev's checklist; also tells the backend exactly what data the agent will read/write.

**The peace-keeping rule:** you co-write all four *together* in Phase 0. After that they change **rarely**, and any change is a small PR all three review — so a contract change is something everyone sees coming, not a 2am surprise. Day-to-day, nobody touches anyone else's package; they only read the shared contract.

**A "mock" / "stub"** is a tiny fake version of a service returning hardcoded data in the contract's exact shape. It's what lets all three of you start on Day 1 instead of standing in a line.

*End of demo PRD v2.*
