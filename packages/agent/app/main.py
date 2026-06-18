# packages/agent/app/main.py

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from app.schemas import (
    ClarityRequest, ClarityResponse,
    ClarityAnswersRequest,
    GoalsRequest, GoalsResponse,
    PlanRequest, PlanResponse,
    ChatRequest,
    ClarifyingQuestion, Goal, StepPlan, MilestonePlan,
    GenerateTasksRequest, GenerateTasksResponse, SubTask
)

app = FastAPI(title="Zero to One Agent API", version="0.1.0")

@app.post("/agent/clarity", response_model=ClarityResponse)
def assess_clarity(body: ClarityRequest):
    return ClarityResponse(
        clarity_score=0.65,
        needs_clarification=True,
        clarifying_questions=[
            ClarifyingQuestion(question="Who is the primary user?"),
            ClarifyingQuestion(question="What problem are you solving?"),
        ]
    )

@app.post("/agent/clarity/answers", response_model=ClarityResponse)
def reassess_clarity(body: ClarityAnswersRequest):
    answers_text = " ".join(pair.answer for pair in body.answers)  # ← dot notation
    return ClarityResponse(
        clarity_score=0.92,
        needs_clarification=False,
        clarifying_questions=[],
        enriched_idea=f"{body.idea} {answers_text}"   # ← combined
    )

@app.post("/agent/goals", response_model=GoalsResponse)
def suggest_goals(body: GoalsRequest):
    return GoalsResponse(
        goals=[
            Goal(title="Prototype", description="A clickable mockup that proves the core experience.", complete_in=7),
            Goal(title="MVP", description="Core flow only, with enough polish for early users.", complete_in=21),
            Goal(title="Production", description="A deployable version with reliability and handoff polish.", complete_in=45),
        ]
    )

@app.post("/agent/plan", response_model=PlanResponse)
def generate_plan(body: PlanRequest):
    return PlanResponse(
        steps=[
            StepPlan(
                title="Define requirements",
                description="Write detailed requirements and acceptance criteria",
                order_index=1,
                intended_start="2026-06-17",
                intended_end="2026-06-19",
                depends_on=[]
            ),
            StepPlan(
                title="Design architecture",
                description="Design system architecture and database schema",
                order_index=2,
                intended_start="2026-06-20",
                intended_end="2026-06-22",
                depends_on=[1]
            ),
            StepPlan(
                title="Build backend",
                description="Implement API endpoints and database layer",
                order_index=3,
                intended_start="2026-06-23",
                intended_end="2026-06-30",
                depends_on=[2]
            ),
            StepPlan(
                title="Build frontend",
                description="Implement UI and client-side logic",
                order_index=4,
                intended_start="2026-07-01",
                intended_end="2026-07-08",
                depends_on=[2]
            ),
            StepPlan(
                title="Testing and refinement",
                description="End-to-end testing and bug fixes",
                order_index=5,
                intended_start="2026-07-09",
                intended_end="2026-07-13",
                depends_on=[3, 4]
            ),
        ],
        milestones=[
            MilestonePlan(title="Requirements approved", after_step_index=1),
            MilestonePlan(title="Architecture review complete", after_step_index=2),
            MilestonePlan(title="Backend MVP ready", after_step_index=3),
            MilestonePlan(title="Frontend MVP ready", after_step_index=4),
            MilestonePlan(title="Launch ready", after_step_index=5),
        ]
    )
@app.post("/agent/tasks", response_model=GenerateTasksResponse)
def generate_tasks(body: GenerateTasksRequest):
    return GenerateTasksResponse(
        tasks= [
            SubTask(title="Research options", detail="Look into available tools"),
            SubTask(title="Make a decision", detail="Pick the best approach"),
            SubTask(title="Implement it", detail="Build the thing"),
        ]
    )

@app.post("/agent/chat")
def chat(body: ChatRequest):
    def event_generator():
        yield 'data: {"role": "assistant", "content": "I"}\n\n'
        yield 'data: {"role": "assistant", "content": " see"}\n\n'
        yield 'data: {"role": "assistant", "content": " your"}\n\n'
        yield 'data: {"role": "assistant", "content": " request"}\n\n'
        yield 'data: {"role": "assistant", "content": ". "}\n\n'
        yield 'data: {"role": "assistant", "content": "Let me help you."}\n\n'
    return StreamingResponse(event_generator(), media_type="text/event-stream")
