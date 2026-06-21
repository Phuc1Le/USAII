# packages/backend/app/agent_client.py

import os
import httpx
from app import schemas
from dotenv import load_dotenv

load_dotenv()

AGENT_URL = os.environ.get("AGENT_URL", "http://localhost:8001")
USE_MOCK_AGENT = os.environ.get("USE_MOCK_AGENT", "").lower() == "true"

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
    res.raise_for_status()
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
    res.raise_for_status()
    return schemas.ClarityResult(**res.json())


def suggest_goals(body: schemas.GoalsRequest) -> schemas.GoalsResponse:
    if USE_MOCK_AGENT:
        return schemas.GoalsResponse(goals=[
            schemas.Goal(title="Prototype", description="A clickable mockup that proves the core experience.", complete_in=7),
            schemas.Goal(title="MVP", description="Core flow only, with enough polish for early users.", complete_in=21),
            schemas.Goal(title="Production", description="A deployable version with reliability and handoff polish.", complete_in=45),
        ])
    res = httpx.post(f"{AGENT_URL}/agent/goals", json=body.model_dump(), timeout=60.0)
    res.raise_for_status()
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
    res.raise_for_status()
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
    res.raise_for_status()
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
    res.raise_for_status()
    return res.json()["summary"]
