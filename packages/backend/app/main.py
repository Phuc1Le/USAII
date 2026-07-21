# packages/backend/app/main.py

from contextlib import asynccontextmanager
import json
import os
import re
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import httpx

from app.models import init_db, get_db
from app import schemas, crud, serializers, agent_client
from dotenv import load_dotenv

try:
    REPO_ROOT = Path(__file__).resolve().parents[3]
    load_dotenv(REPO_ROOT / ".env")
except IndexError:
    pass
load_dotenv()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Zero to One API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

AGENT_URL = os.environ.get("AGENT_URL", "http://localhost:8001")
USE_MOCK_AGENT = os.environ.get("USE_MOCK_AGENT", "").lower() == "true"
CHAT_SUMMARY_TRIGGER = int(os.environ.get("CHAT_SUMMARY_TRIGGER", "6"))
CHAT_SUMMARY_KEEP = int(os.environ.get("CHAT_SUMMARY_KEEP", "3"))
CHAT_SUMMARY_RE_EVERY = int(os.environ.get("CHAT_SUMMARY_RE_EVERY", "2"))

# ── Intake ────────────────────────────────────────────────────────

@app.post("/api/v1/projects/intake", response_model=schemas.ClarityResult)
def submit_idea(body: schemas.IntakeRequest):
    return agent_client.assess_clarity(body)


@app.post("/api/v1/projects/intake/answers", response_model=schemas.ClarityResult)
def submit_answers(body: schemas.ClarityAnswersRequest):
    return agent_client.reassess_clarity(body)


# ── Goals ─────────────────────────────────────────────────────────

@app.post("/api/v1/projects/goals", response_model=schemas.GoalsResponse)
def get_goals(body: schemas.GoalsRequest):
    return agent_client.suggest_goals(body)


# ── Projects ──────────────────────────────────────────────────────

@app.get("/api/v1/projects", response_model=list[schemas.Project])
def list_projects(db: Session = Depends(get_db)):
    return [serializers.serialize_project(p) for p in crud.get_all_projects(db)]


@app.post("/api/v1/projects", response_model=schemas.Project, status_code=201)
def create_project(body: schemas.CreateProjectRequest, db: Session = Depends(get_db)):
    # 1. save the project row
    db_project = crud.create_project(db, body)

    # save any answered clarifying questions as decisions now that the project has an id
    for qa in body.clarifying_answers:
        if qa.answer.strip():
            crud.save_decision(db, db_project.id, f"Q: {qa.question}\nA: {qa.answer.strip()}")

    # 2. ask the agent for a plan
    plan = agent_client.generate_plan(
        schemas.PlanRequest(idea=body.idea, goal=body.goal, complete_in=body.complete_in)
    )

    # 3. save steps + milestones
    db_steps = crud.create_steps_from_plan(db, db_project.id, plan.steps)
    crud.create_milestones_from_plan(db, db_project.id, plan.milestones, db_steps)

    # 4. reload and return
    db.refresh(db_project)
    return serializers.serialize_project(db_project)


@app.patch("/api/v1/projects/{project_id}", response_model=schemas.Project)
def update_project(project_id: int, body: schemas.UpdateProjectRequest, db: Session = Depends(get_db)):
    project = crud.update_project(db, project_id, body)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return serializers.serialize_project(project)


@app.get("/api/v1/projects/{project_id}", response_model=schemas.Project)
def get_project(project_id: int, db: Session = Depends(get_db)):
    db_project = crud.get_project(db, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return serializers.serialize_project(db_project)


@app.get("/api/v1/projects/{project_id}/decisions", response_model=list[schemas.Decision])
def list_decisions(project_id: int, db: Session = Depends(get_db)):
    return [serializers.serialize_decision(d) for d in crud.get_decisions(db, project_id)]


# ── Steps / Tasks ─────────────────────────────────────────────────

@app.patch("/api/v1/steps/{step_id}", response_model=schemas.Step)
def update_step(step_id: int, body: schemas.UpdateStepRequest, db: Session = Depends(get_db)):
    from app.models import Step as StepModel
    step = crud.update_step(db, step_id, body)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    return serializers.serialize_step(step)


@app.patch("/api/v1/milestones/{milestone_id}", response_model=schemas.Milestone)
def update_milestone(milestone_id: int, body: schemas.UpdateMilestoneRequest, db: Session = Depends(get_db)):
    milestone = crud.update_milestone(db, milestone_id, body)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return serializers.serialize_milestone(milestone)


@app.get("/api/v1/steps/{step_id}/tasks", response_model=list[schemas.Task])
def get_tasks(step_id: int, db: Session = Depends(get_db)):
    # lazy generation: if no tasks exist yet, ask the agent to generate them
    existing = crud.get_tasks_for_step(db, step_id)
    if existing:
        return [serializers.serialize_task(t) for t in existing]

    # get the step so we can pass context to the agent
    step = db.query(__import__("app.models", fromlist=["Step"]).Step).filter_by(id=step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    step_plan = schemas.StepPlan(
        title=step.title,
        description=step.description or "",
        order_index=step.order_index,
        intended_start=step.intended_start or "",
        intended_end=step.intended_end or "",
        depends_on=[],
    )
    subtasks = agent_client.generate_tasks(step_plan, step.project.idea)
    db_tasks = crud.create_tasks_for_step(db, step_id, subtasks)
    return [serializers.serialize_task(t) for t in db_tasks]


@app.patch("/api/v1/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, body: schemas.UpdateTaskRequest, db: Session = Depends(get_db)):
    task = crud.update_task(db, task_id, body)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return serializers.serialize_task(task)


# ── Chat ──────────────────────────────────────────────────────────

@app.post("/api/v1/chat/sessions", response_model=schemas.ChatSession)
def open_session(body: schemas.OpenSessionRequest, db: Session = Depends(get_db)):
    session = crud.get_or_create_session(db, body)
    return serializers.serialize_session(session)


@app.post("/api/v1/chat/sessions/{session_id}/messages")
def send_message(
    session_id: int,
    body: schemas.SendMessageRequest,
    db: Session = Depends(get_db)
):
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # save user message
    crud.save_message(db, session_id, "user", body.content)

    # rolling summarization check
    _maybe_summarize(db, session_id)

    # reload session to pick up any fresh summary
    session = crud.get_session(db, session_id)

    if USE_MOCK_AGENT:
        def mock_stream():
            words = ["I", " understand", " your", " request", ".",
                     " Let", " me", " help", " you", " move", " forward", "."]
            full_response = ""
            for word in words:
                full_response += word
                yield f"data: {json.dumps({'content': word})}\n\n"
            crud.save_message(db, session_id, "assistant", full_response)
            yield "data: [DONE]\n\n"
        return StreamingResponse(mock_stream(), media_type="text/event-stream")

    # real agent call — assemble context then stream
    project = session.project
    decisions = crud.get_decisions(db, project.id)

    def step_context(s) -> dict:
        return {
            "title": s.title,
            "description": s.description or "",
            "status": s.status,
            "intended_start": s.intended_start,
            "intended_end": s.intended_end,
        }

    focused_step_model = None
    if session.scope_type == "step" and session.scope_step_id:
        focused_step_model = next(
            (s for s in project.steps if s.id == session.scope_step_id), None
        )

    focused_step = None
    if focused_step_model:
        focused_step = {
            **step_context(focused_step_model),
            "tasks": [
                {"title": t.title, "detail": t.detail or "", "status": t.status}
                for t in focused_step_model.tasks
            ],
        }

    prior_steps = []
    if focused_step_model:
        sessions_by_step = {
            s.scope_step_id: s for s in crud.get_step_chat_sessions(db, project.id)
        }
        for s in sorted(project.steps, key=lambda x: x.order_index):
            if s.order_index >= focused_step_model.order_index:
                continue
            prior_session = sessions_by_step.get(s.id)
            if not prior_session:
                continue
            if prior_session.summary:
                content = prior_session.summary
            elif prior_session.messages:
                # short conversation, never hit the summarization trigger yet
                content = " ".join(m.content for m in prior_session.messages)[:800]
            else:
                continue
            prior_steps.append({"title": s.title, "summary": content})

    chat_request = {
        "session_id": str(session_id),
        "scope_type": session.scope_type,
        "focused_step": focused_step,
        "project_context": {
            "idea": project.idea,
            "goal": project.goal or "",
            "steps": [step_context(s) for s in project.steps],
            "decisions": [d.content for d in decisions],
        },
        "prior_steps": prior_steps,
        "history": [
            {"role": m.role, "content": m.content}
            for m in session.messages[-10:]  # last 10 messages
        ],
        "new_message": body.content,
    }

    if session.summary:
        chat_request["summary"] = session.summary

    # tolerant to markdown emphasis, bullets, and casing around the "DECISION:" marker
    decision_re = re.compile(r"^[\s*_>-]*decision\s*:\s*", re.IGNORECASE)

    def is_decision_line(text: str) -> bool:
        return bool(decision_re.match(text.strip()))

    def real_stream():
        full_response = ""      # raw model output, including any DECISION lines
        visible_response = ""   # what the user actually sees / what gets persisted as the message
        line_buffer = ""
        with httpx.stream("POST", f"{AGENT_URL}/agent/chat", json=chat_request) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line.startswith("data: "):
                    payload = line[6:]
                    if payload == "[DONE]":
                        break
                    try:
                        token = json.loads(payload).get("content", "")
                    except json.JSONDecodeError:
                        token = payload
                    if not token:
                        continue
                    full_response += token
                    line_buffer += token
                    # only forward complete lines, so a trailing DECISION line can be withheld
                    while "\n" in line_buffer:
                        nl_index = line_buffer.index("\n")
                        complete_line = line_buffer[:nl_index + 1]
                        line_buffer = line_buffer[nl_index + 1:]
                        if not is_decision_line(complete_line):
                            visible_response += complete_line
                            yield f"data: {json.dumps({'content': complete_line})}\n\n"

            if line_buffer and not is_decision_line(line_buffer):
                visible_response += line_buffer
                yield f"data: {json.dumps({'content': line_buffer})}\n\n"

        # persist only what the user saw — DECISION lines are structured data, not chat prose
        crud.save_message(db, session_id, "assistant", visible_response.strip())

        # extract and save any decisions from the raw response
        decision_saved = False
        for line in full_response.split("\n"):
            stripped = line.strip()
            if is_decision_line(stripped):
                content = decision_re.sub("", stripped).strip()
                if content:
                    crud.save_decision(db, project.id, content)
                    decision_saved = True

        if decision_saved:
            yield f"data: {json.dumps({'decision': True})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(real_stream(), media_type="text/event-stream")


def _maybe_summarize(db: Session, session_id: int) -> None:
    session = crud.get_session(db, session_id)
    if not session:
        return

    msg_count = len(session.messages)

    if msg_count < CHAT_SUMMARY_TRIGGER:
        return

    # decide if re-summarization is due
    need_summary = False
    if session.summary is None:
        need_summary = True
    elif (
        session.summary_message_count is not None
        and msg_count - session.summary_message_count >= CHAT_SUMMARY_KEEP + CHAT_SUMMARY_RE_EVERY
    ):
        need_summary = True

    if not need_summary:
        return

    # messages to summarize: all except the last KEEP
    to_summarize_count = msg_count - CHAT_SUMMARY_KEEP

    # if we already have a summary, only send the new old messages
    start_idx = session.summary_message_count or 0
    old_messages = session.messages[start_idx:to_summarize_count]

    # always include the first message — it carries the project context and initial task setup
    if start_idx > 0 and len(session.messages) > 0:
        old_messages.insert(0, session.messages[0])

    try:
        new_summary = agent_client.summarize_chat(
            messages=[{"role": m.role, "content": m.content} for m in old_messages],
            existing_summary=session.summary,
        )
        crud.update_session_summary(db, session_id, new_summary, to_summarize_count)
    except Exception:
        # summarization failure is non-fatal — proceed without it
        pass