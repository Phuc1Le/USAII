from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.models import init_db
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    IntakeRequest, ClarityResult,
    ClarityAnswersRequest,
    GoalsRequest, GoalsResponse, Goal,
    CreateProjectRequest, Project,
    UpdateTaskRequest, Task,
    OpenSessionRequest, ChatSession,
    SendMessageRequest, Step, Milestone,
    ClarifyingQuestion
)
import os
USE_MOCK_AGENT = os.environ.get("USE_MOCK_AGENT", "true").lower() == "true"
@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Zero to One API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Person A's Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)
# ── Intake ───────────────────────────────────────────────────────

@app.post("/api/v1/projects/intake", response_model=ClarityResult)
def submit_idea(body: IntakeRequest):
    if USE_MOCK_AGENT:
        return ClarityResult(
            clarity_score=0.45,
            needs_clarification=True,
            clarifying_questions=[
                ClarifyingQuestion(question="Who is the primary user?"),
                ClarifyingQuestion(question="What is the one thing it must do?"),
            ]
        )
    # real agent call goes here later

@app.post("/api/v1/projects/intake/answers", response_model=ClarityResult)
def submit_answers(body: ClarityAnswersRequest):
    if USE_MOCK_AGENT:
        return ClarityResult(
            clarity_score=0.78,
            needs_clarification=False,
            clarifying_questions=[]
        )
    # real agent call goes here later

# ── Goals ────────────────────────────────────────────────────────

@app.post("/api/v1/projects/goals", response_model=GoalsResponse)
def get_goals(body: GoalsRequest):
    if USE_MOCK_AGENT:
        return GoalsResponse(
            goals=[
                Goal(
                    title="Finalize Requirements",
                    description="Document all requirements and acceptance criteria",
                    complete_in=3
                ),
                Goal(
                    title="MVP Development",
                    description="Build core features for minimum viable product",
                    complete_in=14
                ),
                Goal(
                    title="User Testing",
                    description="Conduct user testing and gather feedback",
                    complete_in=7
                )
            ]
        )
    # real agent call goes here later

# ── Projects ─────────────────────────────────────────────────────

@app.post("/api/v1/projects", response_model=Project, status_code=201)
def create_project(body: CreateProjectRequest):
    return Project(
        id="p_" + body.idea.replace(" ", "_").lower()[:20],
        title=body.idea,
        category=body.category,
        description=body.description,
        idea=body.idea,
        goal=body.goal,
        status="active",
        steps=[],
        milestones=[]
    )

@app.get("/api/v1/projects/{project_id}", response_model=Project)
def get_project(project_id: str):
    return Project(
        id="p1",
        title="My demo app",
        category="Technology",
        description="Building an app",
        idea="An app that helps people go from idea to launch",
        goal="MVP",
        status="active",
        steps=[
            Step(
                id="s1",
                title="Define requirements",
                description="Write down what the app must do",
                order_index=1,
                status="todo",
                intended_start="2026-06-17",
                intended_end="2026-06-19",
                depends_on=[],
                tasks=[]
            ),
            Step(
                id="s2",
                title="Build the API",
                description="Create backend endpoints",
                order_index=2,
                status="todo",
                intended_start="2026-06-20",
                intended_end="2026-06-27",
                depends_on=["s1"],
                tasks=[]
            ),
        ],
        milestones=[
            Milestone(
                id="m1",
                title="First working prototype",
                step_id="s2",
                achieved_at=None
            )
        ]
    )

# ── Steps / Tasks ────────────────────────────────────────────────

@app.get("/api/v1/steps/{step_id}/tasks", response_model=list[Task])
def get_tasks(step_id: str):
    return [
        Task(
            id="t1",
            title="Write specification document",
            detail="Create detailed spec with acceptance criteria",
            status="todo",
            order_index=1
        ),
        Task(
            id="t2",
            title="Create wireframes",
            detail="Design UI mockups for key screens",
            status="todo",
            order_index=2
        ),
        Task(
            id="t3",
            title="Get stakeholder approval",
            detail="Present to stakeholders and get sign-off",
            status="todo",
            order_index=3
        )
    ]

@app.patch("/api/v1/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, body: UpdateTaskRequest):
    return Task(
        id=task_id,
        title=body.title or "Updated task",
        detail="Task details",
        status=body.status or "todo",
        order_index=1
    )

# ── Chat ─────────────────────────────────────────────────────────

@app.post("/api/v1/chat/sessions", response_model=ChatSession)
def open_session(body: OpenSessionRequest):
    return ChatSession(
        id="sess_" + body.project_id,
        project_id=body.project_id,
        scope_type=body.scope_type,
        scope_step_id=body.scope_step_id,
        messages=[]
    )

@app.post("/api/v1/chat/sessions/{session_id}/messages")
def send_message(session_id: str, body: SendMessageRequest):
    if USE_MOCK_AGENT:
        def event_generator():
            words = ["I", " understand", " your", " request", ".", " Let", " me", " help", " you", " move", " forward", "."]
            for word in words:
                yield f"data: {word}\n\n"
            yield "data: [DONE]\n\n"   # ← signals the stream is finished
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    # real agent call goes here later

# ── Decompose (stretch) ──────────────────────────────────────────

# add when you get to the stretch features
