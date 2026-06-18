# packages/agent/app/schemas.py

from pydantic import BaseModel
from typing import Literal

# ── /agent/clarity ───────────────────────────────────────────────

class ClarityRequest(BaseModel):
    category: str
    description: str
    idea: str

class ClarifyingQuestion(BaseModel):
    question: str

class ClarityResponse(BaseModel):
    clarity_score: float
    needs_clarification: bool
    clarifying_questions: list[ClarifyingQuestion]
    enriched_idea: str | None = None   # ← add this

# ── /agent/clarity/answers ───────────────────────────────────────

class QAPair(BaseModel):
    question: str
    answer: str

class ClarityAnswersRequest(BaseModel):
    idea: str
    answers: list[QAPair]

# response is ClarityResponse again (re-scored)

# ── /agent/goals ─────────────────────────────────────────────────

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

# ── /agent/plan ──────────────────────────────────────────────────

class PlanRequest(BaseModel):
    category: str | None = None
    description: str | None = None
    idea: str
    goal: str

class StepPlan(BaseModel):
    title: str
    description: str
    order_index: int
    intended_start: str           # "YYYY-MM-DD"
    intended_end: str             # "YYYY-MM-DD"
    depends_on: list[int]         # order_index values

class MilestonePlan(BaseModel):
    title: str
    after_step_index: int

class PlanResponse(BaseModel):
    steps: list[StepPlan]
    milestones: list[MilestonePlan]

# ── /agent/chat ──────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ProjectContext(BaseModel):
    idea: str          # "An app that helps people go from idea to launch"
    goal: str          # "MVP"
    steps: list[str]   # ["Define requirements", "Build API", "Build frontend", ...]
                       # titles only — keeps the prompt short
    decisions: list[str]  # ["Chose FastAPI over Flask", "Using SQLite for demo", ...]
                          # the decisions table from the DB, as plain text

class ChatRequest(BaseModel):
    session_id: str
    scope_type: Literal["step", "project"]
    scope_step_title: str | None
    project_context: ProjectContext
    history: list[ChatMessage]
    new_message: str

# chat response is SSE stream — no response model needed
class SubTask(BaseModel):
    title: str
    detail: str

class GenerateTasksRequest(BaseModel):
    step_title: str
    step_description: str
    project_idea: str

class GenerateTasksResponse(BaseModel):
    tasks: list[SubTask]