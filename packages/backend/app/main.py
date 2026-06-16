from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.models import init_db
from fastapi.responses import StreamingResponse
from app.schemas import (
    IntakeRequest, ClarityResult,
    ClarityAnswersRequest,
    GoalsRequest, GoalsResponse,
    CreateProjectRequest, Project,
    UpdateTaskRequest, Task,
    OpenSessionRequest, ChatSession,
    SendMessageRequest,
)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Zero to One API", version="0.1.0", lifespan=lifespan)

# ── Intake ───────────────────────────────────────────────────────

@app.post("/api/v1/projects/intake", response_model=ClarityResult)
def submit_idea(body: IntakeRequest):
    pass

@app.post("/api/v1/projects/intake/answers", response_model=ClarityResult)
def submit_answers(body: ClarityAnswersRequest):
    pass

# ── Goals ────────────────────────────────────────────────────────

@app.post("/api/v1/projects/goals", response_model=GoalsResponse)
def get_goals(body: GoalsRequest):
    pass

# ── Projects ─────────────────────────────────────────────────────

@app.post("/api/v1/projects", response_model=Project, status_code=201)
def create_project(body: CreateProjectRequest):
    pass

@app.get("/api/v1/projects/{project_id}", response_model=Project)
def get_project(project_id: str):
    pass

# ── Steps / Tasks ────────────────────────────────────────────────

@app.get("/api/v1/steps/{step_id}/tasks", response_model=list[Task])
def get_tasks(step_id: str):
    pass

@app.patch("/api/v1/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, body: UpdateTaskRequest):
    pass

# ── Chat ─────────────────────────────────────────────────────────

@app.post("/api/v1/chat/sessions", response_model=ChatSession)
def open_session(body: OpenSessionRequest):
    pass

@app.post("/api/v1/chat/sessions/{session_id}/messages")
def send_message(session_id: str, body: SendMessageRequest):
    pass   # returns SSE stream — no response_model

# ── Decompose (stretch) ──────────────────────────────────────────

# add when you get to the stretch features
