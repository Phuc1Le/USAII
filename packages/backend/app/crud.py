# packages/backend/app/crud.py

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app import models
from app import schemas


# ── Projects ─────────────────────────────────────────────────────

def create_project(db: Session, body: schemas.CreateProjectRequest) -> models.Project:
    count = db.query(models.Project).count()
    project = models.Project(
        title=f"Project {count + 1}",
        category=body.category,
        description=body.description,
        idea=body.idea,
        goal=body.goal,
        status="active",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: int) -> models.Project | None:
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def get_all_projects(db: Session) -> list[models.Project]:
    return db.query(models.Project).order_by(models.Project.id).all()


def update_project(db: Session, project_id: int, body: schemas.UpdateProjectRequest) -> models.Project | None:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        return None
    if body.status is not None:
        project.status = body.status
    db.commit()
    db.refresh(project)
    return project


# ── Steps ─────────────────────────────────────────────────────────

def create_steps_from_plan(
    db: Session,
    project_id: int,
    steps: list[schemas.StepPlan],   # comes from the agent
) -> list[models.Step]:

    # first pass: create all step rows (no dependencies yet)
    db_steps = []
    for s in steps:
        db_step = models.Step(
            project_id=project_id,
            title=s.title,
            description=s.description,
            order_index=s.order_index,
            intended_start=s.intended_start,
            intended_end=s.intended_end,
            status="todo",
        )
        db.add(db_step)
        db_steps.append(db_step)

    db.commit()
    for s in db_steps:
        db.refresh(s)

    # second pass: wire up dependencies now that all steps have real ids
    # agent uses order_index to refer to steps; we need real db ids
    order_to_id = {s.order_index: db_steps[i].id for i, s in enumerate(steps)}

    for i, s in enumerate(steps):
        for dep_order in s.depends_on:
            dep_id = order_to_id.get(dep_order)
            if dep_id:
                db.add(models.StepDependency(
                    step_id=db_steps[i].id,
                    depends_on_step_id=dep_id,
                ))

    db.commit()
    return db_steps


# ── Milestones ────────────────────────────────────────────────────

def create_milestones_from_plan(
    db: Session,
    project_id: int,
    milestones: list[schemas.MilestonePlan],
    db_steps: list[models.Step],      # the steps we just created
) -> list[models.Milestone]:

    # agent uses after_step_index to refer to steps
    order_to_db_step = {s.order_index: db_steps[i] for i, s in enumerate(db_steps)}

    db_milestones = []
    for m in milestones:
        db_step = order_to_db_step.get(m.after_step_index)
        db_milestone = models.Milestone(
            project_id=project_id,
            title=m.title,
            step_id=db_step.id if db_step else None,
        )
        db.add(db_milestone)
        db_milestones.append(db_milestone)

    db.commit()
    return db_milestones


def update_milestone(
    db: Session,
    milestone_id: int,
    body: schemas.UpdateMilestoneRequest,
) -> models.Milestone | None:
    milestone = db.query(models.Milestone).filter(models.Milestone.id == milestone_id).first()
    if not milestone:
        return None
    if body.achieved is not None:
        milestone.achieved_at = datetime.now(timezone.utc) if body.achieved else None
    db.commit()
    db.refresh(milestone)
    return milestone


# ── Tasks ─────────────────────────────────────────────────────────

def create_tasks_for_step(
    db: Session,
    step_id: int,
    tasks: list[schemas.SubTask],    # comes from the agent
) -> list[models.Task]:

    db_tasks = []
    for i, t in enumerate(tasks):
        db_task = models.Task(
            step_id=step_id,
            title=t.title,
            detail=t.detail,
            status="todo",
            order_index=i,
        )
        db.add(db_task)
        db_tasks.append(db_task)

    db.commit()
    return db_tasks


def update_step(db: Session, step_id: int, body: schemas.UpdateStepRequest) -> models.Step | None:
    step = db.query(models.Step).filter(models.Step.id == step_id).first()
    if not step:
        return None
    if body.status is not None:
        step.status = body.status
    db.commit()
    db.refresh(step)
    return step


def get_tasks_for_step(db: Session, step_id: int) -> list[models.Task]:
    return (
        db.query(models.Task)
        .filter(models.Task.step_id == step_id)
        .order_by(models.Task.order_index)
        .all()
    )


def update_task(
    db: Session,
    task_id: int,
    body: schemas.UpdateTaskRequest,
) -> models.Task | None:

    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return None
    if body.status is not None:
        task.status = body.status
    if body.title is not None:
        task.title = body.title
    db.commit()
    db.refresh(task)
    return task


# ── Chat ──────────────────────────────────────────────────────────

def get_or_create_session(
    db: Session,
    body: schemas.OpenSessionRequest,
) -> models.ChatSession:

    # if a session already exists for this project+scope, return it
    query = db.query(models.ChatSession).filter(
        models.ChatSession.project_id == body.project_id,
        models.ChatSession.scope_type == body.scope_type,
        models.ChatSession.scope_step_id == body.scope_step_id,
    )
    existing = query.first()
    if existing:
        return existing

    session = models.ChatSession(
        project_id=body.project_id,
        scope_type=body.scope_type,
        scope_step_id=body.scope_step_id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: int) -> models.ChatSession | None:
    return db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id
    ).first()


def save_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
) -> models.ChatMessage:

    msg = models.ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def save_decision(db: Session, project_id: int, content: str) -> models.Decision:
    decision = models.Decision(project_id=project_id, content=content)
    db.add(decision)
    db.commit()
    return decision


def get_decisions(db: Session, project_id: int) -> list[models.Decision]:
    return db.query(models.Decision).filter(
        models.Decision.project_id == project_id
    ).all()