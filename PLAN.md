# Agent Chat: ReAct Loop Implementation Plan

## Context

The chat route (`/agent/chat`) is currently a single-shot LLM wrapper: `build_chat_prompt`
flattens the whole request into one prompt string, `stream_text` sends it to Gemini once, and
whatever comes back streams straight to the user. This plan turns it into a ReAct-style loop with
four tools (`web_search`, `query_decisions`, `retrieve_step`, `retrieve_milestones`), building on
the prompt restructuring already done (stable project-context block vs. per-turn variable block in
`prompts.py`).

## Architecture decisions (locked in before implementation)

1. **Tools that touch persistence are backend-proxied, not direct-DB.** `query_decisions` and
   `retrieve_step` call new internal backend HTTP endpoints (e.g. `GET /internal/decisions/search`,
   `GET /internal/steps/{id}`) rather than opening a DB connection from the agent service. This
   preserves the existing rule that the agent holds no DB connection/session state and the backend
   is the sole owner of persistence. `web_search` has no persistence concern and calls its external
   API directly.
2. **`query_decisions` is project-scoped from line one.** Every call is scoped to a `project_id` —
   this is the tenancy boundary and must not be retrofitted later.
3. **Embeddings on `Decision.embedding` are a prerequisite, owned separately** (someone is already
   on it). `query_decisions` cannot return meaningful results until decisions are embedded on save
   and backfilled for existing rows. Interface/plumbing for the tool can be built ahead of this
   landing, but semantic-search acceptance tests are blocked on it.
4. **Once `query_decisions` exists, `project_context.decisions` (the full-text array sent on every
   turn) is dropped.** No more double-paying for the same data as both an unconditional dump and an
   on-demand tool.
5. **Framework: Pydantic AI**, not a hand-rolled loop. It provides tool registration, the
   iterate-until-final-answer loop, the iteration cap, and Logfire tracing out of the box — cheaper
   than building and debugging the same pieces by hand for three tools.
6. **`DECISION:` line parsing targets only the final synthesized answer**, never intermediate
   ReAct thought/tool-observation text, now that a turn can involve multiple model calls.
7. **History moves to native role-tagged `contents` turns** (Gemini's `{"role": "user"/"model",
   "parts": [...]}` structure) instead of the flattened `[user]: ...` text block. This is done first
   because tool calls and tool results are threaded through the model via that same turns mechanism
   — building the ReAct loop on top of flattened text would mean redoing this later anyway.

8. **A fourth tool, `retrieve_milestones`, is needed** — `ProjectContext` (`agent/app/schemas.py`)
   has no `milestones` field, and none of the other three tools cover it either. `Milestone` is a
   first-class entity (`Project 1—N Milestone`, optionally tied to a `Step`) that the chat agent
   currently cannot see or answer questions about at all (e.g. "are we on track for the MVP
   milestone"). Same shape as `retrieve_step`: backend-proxied, e.g. `GET /internal/milestones?project_id=`.

## Open dependency

- Decision embedding generation + backfill (owned by teammate) — blocks `query_decisions` from
  returning real results, not blocking on building the tool's plumbing.

---

## Step 1 — History as native multi-turn `contents`

Replace the flattened `history_text` block in `build_chat_prompt`/`stream_text` with role-tagged
turns (`user`/`model`) plus a `system_instruction` for the fixed persona/rules text. Project-context
block stays as context injected into the turn sequence (exact placement decided here).

**Acceptance:** existing chat behavior is unchanged from the user's perspective (same quality or
better); `stream_text` accepts structured `contents` instead of a flat string; prompt tests updated
to reflect the new shape.

## Step 2 — Tools in isolation

Implement `web_search`, `query_decisions`, `retrieve_step`, `retrieve_milestones` as plain async
functions, tested by calling them directly (no agent involved):
- `web_search`: direct external API call.
- `query_decisions`: HTTP call to new backend internal endpoint, project-scoped.
- `retrieve_step`: HTTP call to new backend internal endpoint.
- `retrieve_milestones`: HTTP call to new backend internal endpoint, project-scoped.

**Acceptance:** each returns correct typed results when called directly. `query_decisions`
correctness for *relevance* depends on the embeddings dependency above; scoping/plumbing does not.

## Step 3 — Single-turn agent, no loop (Pydantic AI)

Wire one tool (`web_search`) to the model via Pydantic AI's tool-calling. Confirm the model decides
to call it, receives the observation, and answers — no loop yet.

**Acceptance:** "find me a library for X" triggers a search and a grounded answer; a question
needing no tool gets answered directly with no spurious call.

## Step 4 — Full loop + cap

Register all three tools. Enable multi-iteration ReAct with a max-iteration cap. On cap-out, force
one final synthesis call so the user still gets a usable answer instead of a truncation.

**Acceptance:** correct tool selection across zero-tool, one-tool, and multi-tool test messages,
plus one adversarial case designed to force the cap; cap terminates cleanly with a usable partial
answer.

## Step 5 — Context injection + caching

Inject current step/project context every turn (not as a tool); keep rolling summary + recent
messages; drop the full `decisions` array now that `query_decisions` covers that need; apply
caching to the stable portion of the prompt (implicit caching via a stable prefix, per earlier
caching assessment — no explicit cache-handle bookkeeping unless implicit caching proves
insufficient).

**Acceptance:** agent answers current-step questions from injected context without calling
`retrieve_step`, and reaches for `retrieve_step` only for other steps.

## Step 6 — Streaming contract

Implement two-phase SSE: status events during tool execution, then the token stream for the final
answer. Update all three layers that share this contract: the agent's SSE output, the backend's
`real_stream()` re-parser (`main.py`), the frontend's `streamChat` parser (`api/client.ts`), and
`contracts/agent_api.yaml`.

**Acceptance:** user sees tool-activity status, then a streamed answer; latency of the final answer
is unaffected by how many tools ran.

## Step 7 — Reattach async decision detection

Confirm the existing background decision-extraction (`DECISION:` line parsing) still fires after
the response in the new agent flow, and that it parses only the final synthesized answer — not any
intermediate ReAct thought/observation text.

**Acceptance:** decisions persist after streaming completes; response latency untouched.

## Step 8 — Guardrails

Per-tool timeout (a slow web search shouldn't hang the turn); a tool failure returns a graceful
observation the model can reason about ("search unavailable") rather than crashing the loop; log
every tool invocation for debugging (Logfire, via Pydantic AI).

**Acceptance:** a killed tool call degrades gracefully; every loop is traceable after the fact.
