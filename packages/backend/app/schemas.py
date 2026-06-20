# packages/backend/app/schemas.py

from pydantic import BaseModel
from typing import Literal

# ── Tasks ────────────────────────────────────────────────────────

class Task(BaseModel):
    id: str
    title: str
    detail: str
    status: Literal["todo", "done"]
    order_index: int

# ── Steps ────────────────────────────────────────────────────────

class Step(BaseModel):
    id: str
    title: str
    description: str
    order_index: int
    status: Literal["todo", "in_progress", "blocked", "deferred", "done"]
    intended_start: str | None    # "YYYY-MM-DD"
    intended_end: str | None      # "YYYY-MM-DD"
    depends_on: list[str]         # list of step ids
    tasks: list[Task]             # empty until step is opened

# ── Milestones ───────────────────────────────────────────────────

class Milestone(BaseModel):
    id: str
    title: str
    step_id: str | None
    achieved_at: str | None       # ISO datetime string

# ── Projects ─────────────────────────────────────────────────────

class Project(BaseModel):
    id: str
    title: str
    category: str
    description: str
    idea: str
    goal: str
    status: Literal["active", "completed"]
    steps: list[Step]
    milestones: list[Milestone]

# ── Intake ───────────────────────────────────────────────────────

class IntakeRequest(BaseModel):
    category: str
    description: str
    idea: str

class ClarifyingQuestion(BaseModel):
    question: str

class ClarityResult(BaseModel):
    clarity_score: float
    needs_clarification: bool
    clarifying_questions: list[ClarifyingQuestion]
    enriched_idea: str | None = None   

class QAPair(BaseModel):
    question: str
    answer: str

class ClarityAnswersRequest(BaseModel):
    idea: str
    answers: list[QAPair]  # ← matches agent's QAPair  

# ── Goals ────────────────────────────────────────────────────────

class GoalsRequest(BaseModel):
    category: str
    description: str
    idea: str

class Goal(BaseModel):
    title: str
    description: str
    complete_in: int

class GoalsResponse(BaseModel):
    goals: list[Goal]

# ── Create project ───────────────────────────────────────────────

class CreateProjectRequest(BaseModel):
    category: str
    description: str
    idea: str
    goal: str
    complete_in: int  # days — passed through to PlanRequest

# ── Projects (update) ────────────────────────────────────────────

class UpdateProjectRequest(BaseModel):
    status: Literal["active", "completed"] | None = None

# ── Steps (update) ───────────────────────────────────────────────

class UpdateStepRequest(BaseModel):
    status: Literal["todo", "in_progress", "blocked", "deferred", "done"] | None = None

# ── Milestones (update) ──────────────────────────────────────────

class UpdateMilestoneRequest(BaseModel):
    achieved: bool | None = None

# ── Tasks (update) ───────────────────────────────────────────────

class UpdateTaskRequest(BaseModel):
    status: Literal["todo", "done"] | None = None
    title: str | None = None

# ── Chat ─────────────────────────────────────────────────────────

class OpenSessionRequest(BaseModel):
    project_id: str
    scope_type: Literal["step", "project"]
    scope_step_id: str | None = None

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatSession(BaseModel):
    id: str
    project_id: str
    scope_type: Literal["step", "project"]
    scope_step_id: str | None
    messages: list[ChatMessage]

class SendMessageRequest(BaseModel):
    content: str

# ── Agent response shapes (backend needs to parse these) ─────────

class StepPlan(BaseModel):
    title: str
    description: str
    order_index: int
    intended_start: str
    intended_end: str
    depends_on: list[int]

class MilestonePlan(BaseModel):
    title: str
    after_step_index: int

class PlanResponse(BaseModel):
    steps: list[StepPlan]
    milestones: list[MilestonePlan]

class PlanRequest(BaseModel):
    category: str | None = None
    description: str | None = None
    idea: str
    goal: str
    complete_in: int

class SubTask(BaseModel):
    title: str
    detail: str

class GenerateTasksResponse(BaseModel):
    tasks: list[SubTask]