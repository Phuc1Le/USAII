# packages/backend/app/main.py

from contextlib import asynccontextmanager
import json
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import httpx

from app.models import init_db, get_db
from app import schemas, crud, serializers, agent_client

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Zero to One API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173"],
    allow_origins=["http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_URL = os.environ.get("AGENT_URL", "http://localhost:8001")
USE_MOCK_AGENT = os.environ.get("USE_MOCK_AGENT")

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

    # 2. ask the agent for a plan
    plan = agent_client.generate_plan(
        schemas.PlanRequest(idea=body.idea, goal=body.goal)
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

    chat_request = {
        "session_id": str(session_id),
        "scope_type": session.scope_type,
        "scope_step_title": None,   # TODO: look up step title if scope = step
        "project_context": {
            "idea": project.idea,
            "goal": project.goal or "",
            "steps": [s.title for s in project.steps],
            "decisions": [d.content for d in decisions],
        },
        "history": [
            {"role": m.role, "content": m.content}
            for m in session.messages[-10:]  # last 10 messages
        ],
        "new_message": body.content,
    }

    def real_stream():
        full_response = ""
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
                    yield f"data: {json.dumps({'content': token})}\n\n"

        # save the complete assistant response after streaming finishes
        crud.save_message(db, session_id, "assistant", full_response)

        # check if the response contains a decision to save
        if "DECISION:" in full_response:
            for line in full_response.split("\n"):
                if line.startswith("DECISION:"):
                    crud.save_decision(db, project.id, line[9:].strip())

        yield "data: [DONE]\n\n"

    return StreamingResponse(real_stream(), media_type="text/event-stream")