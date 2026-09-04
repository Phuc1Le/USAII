# packages/backend/app/agent_client.py

import hashlib
import json

from fastapi import HTTPException
import httpx
from app import schemas
from app.config import AGENT_URL, USE_MOCK_AGENT


def _agent_error_detail(res: httpx.Response) -> str:
    """Pull the agent's own explanation out of its error response.

    The agent raises HTTPException too, so its body is already `{"detail": "..."}`.
    Passing that whole body through as our detail double-encodes it — FastAPI
    serializes it again into `{"detail": "{\\"detail\\":\\"...\\"}"}` — and the
    frontend's apiError() unwraps `detail` exactly once, so the user ends up
    reading an escaped JSON blob instead of the actual reason.
    """
    try:
        payload = res.json()
    except ValueError:
        payload = None

    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
        if detail is not None:
            # FastAPI validation errors put a list of dicts here; no single readable
            # sentence to extract, so keep it as text rather than dropping it
            return json.dumps(detail, ensure_ascii=False)

    return res.text.strip() or f"Agent returned HTTP {res.status_code}"


def _raise_for_agent_error(res: httpx.Response) -> None:
    """Forward the agent's failure with its own explanation attached.

    httpx's raise_for_status() carries only the status code, so FastAPI turns it
    into an opaque 500 and the agent's reason (bad Gemini key, exhausted quota,
    schema mismatch) is lost before anyone can read it.
    """
    if res.is_error:
        raise HTTPException(status_code=res.status_code, detail=_agent_error_detail(res))


def assess_clarity(body: schemas.IntakeRequest) -> schemas.ClarityResult:
    if USE_MOCK_AGENT:
        return schemas.ClarityResult(
            clarity_score=0.45,
            needs_clarification=True,
            clarifying_questions=[
                schemas.ClarifyingQuestion(question="Who is the primary user?"),
                schemas.ClarifyingQuestion(question="What is the one thing it must do?"),
            ]
        )
    res = httpx.post(f"{AGENT_URL}/agent/clarity", json=body.model_dump(), timeout=60.0)
    _raise_for_agent_error(res)
    return schemas.ClarityResult(**res.json())


def reassess_clarity(body: schemas.ClarityAnswersRequest) -> schemas.ClarityResult:
    if USE_MOCK_AGENT:
        answers_text = " ".join(pair.answer for pair in body.answers)
        return schemas.ClarityResult(
            clarity_score=0.85,
            needs_clarification=False,
            clarifying_questions=[],
            enriched_idea=f"{body.idea} {answers_text}"   # ← combined
        )
    res = httpx.post(f"{AGENT_URL}/agent/clarity/answers", json=body.model_dump(), timeout=60.0)
    _raise_for_agent_error(res)
    return schemas.ClarityResult(**res.json())


def suggest_goals(body: schemas.GoalsRequest) -> schemas.GoalsResponse:
    if USE_MOCK_AGENT:
        return schemas.GoalsResponse(goals=[
            schemas.Goal(title="Prototype", description="A clickable mockup that proves the core experience.", complete_in=7),
            schemas.Goal(title="MVP", description="Core flow only, with enough polish for early users.", complete_in=21),
            schemas.Goal(title="Production", description="A deployable version with reliability and handoff polish.", complete_in=45),
        ])
    res = httpx.post(f"{AGENT_URL}/agent/goals", json=body.model_dump(), timeout=60.0)
    _raise_for_agent_error(res)
    return schemas.GoalsResponse(**res.json())


def generate_plan(body: schemas.PlanRequest) -> schemas.PlanResponse:
    if USE_MOCK_AGENT:
        return schemas.PlanResponse(
            steps=[
                schemas.StepPlan(
                    title="Define requirements",
                    description="Write down what the app must do",
                    order_index=1,
                    intended_start="2026-06-17",
                    intended_end="2026-06-19",
                    depends_on=[]
                ),
                schemas.StepPlan(
                    title="Build the API",
                    description="Create backend endpoints",
                    order_index=2,
                    intended_start="2026-06-20",
                    intended_end="2026-06-27",
                    depends_on=[1]
                ),
                schemas.StepPlan(
                    title="Build the frontend",
                    description="Create the UI",
                    order_index=3,
                    intended_start="2026-06-28",
                    intended_end="2026-07-03",
                    depends_on=[2]
                ),
            ],
            milestones=[
                schemas.MilestonePlan(
                    title="First working prototype",
                    after_step_index=2
                )
            ]
        )
    res = httpx.post(f"{AGENT_URL}/agent/plan", json=body.model_dump(), timeout=60.0)
    _raise_for_agent_error(res)
    return schemas.PlanResponse(**res.json())

def generate_tasks(step: schemas.StepPlan, project_idea: str) -> list[schemas.SubTask]:
    if USE_MOCK_AGENT:
        return [
            schemas.SubTask(title="Research options", detail="Look into available tools"),
            schemas.SubTask(title="Make a decision", detail="Pick the best approach"),
            schemas.SubTask(title="Implement it", detail="Build the thing"),
        ]
    res = httpx.post(f"{AGENT_URL}/agent/tasks", json={
        "step_title": step.title,
        "step_description": step.description,
        "project_idea": project_idea,
    }, timeout=60.0)
    _raise_for_agent_error(res)
    return [schemas.SubTask(**t) for t in res.json()["tasks"]]


def summarize_chat(
    messages: list[dict],
    existing_summary: str | None = None,
) -> str:
    if USE_MOCK_AGENT:
        return "The user is working on their project plan. They have clarified requirements and are progressing through implementation steps."
    res = httpx.post(f"{AGENT_URL}/agent/chat/summary", json={
        "messages": messages,
        "existing_summary": existing_summary,
    }, timeout=60.0)
    _raise_for_agent_error(res)
    return res.json()["summary"]


EMBEDDING_DIM = 3072

def embed_text(text: str) -> list[float]:
    if USE_MOCK_AGENT:
        # deterministic pseudo-vector so dev works without Gemini; not a real semantic
        # embedding. Stable hash (not Python's per-process hash()) so the same text maps
        # to the same vector across processes/restarts.
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [
            ((digest[i % len(digest)] * 31 + i) % 1000) / 500.0 - 1.0
            for i in range(EMBEDDING_DIM)
        ]
    res = httpx.post(f"{AGENT_URL}/agent/embed", json={"text": text}, timeout=60.0)
    _raise_for_agent_error(res)
    return res.json()["embedding"]
