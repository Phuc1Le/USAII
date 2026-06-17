# packages/backend/app/serializers.py

from app import models, schemas


def serialize_task(t: models.Task) -> schemas.Task:
    return schemas.Task(
        id=str(t.id),
        title=t.title,
        detail=t.detail or "",
        status=t.status,
        order_index=t.order_index,
    )


def serialize_step(s: models.Step) -> schemas.Step:
    return schemas.Step(
        id=str(s.id),
        title=s.title,
        description=s.description or "",
        order_index=s.order_index,
        status=s.status,
        intended_start=s.intended_start,
        intended_end=s.intended_end,
        depends_on=[str(d.depends_on_step_id) for d in s.dependencies],
        tasks=[serialize_task(t) for t in s.tasks],
    )


def serialize_milestone(m: models.Milestone) -> schemas.Milestone:
    return schemas.Milestone(
        id=str(m.id),
        title=m.title,
        step_id=str(m.step_id) if m.step_id else None,
        achieved_at=m.achieved_at.isoformat() if m.achieved_at else None,
    )


def serialize_project(p: models.Project) -> schemas.Project:
    return schemas.Project(
        id=str(p.id),
        title=p.title,
        category=p.category,
        description=p.description,
        idea=p.idea,
        goal=p.goal or "",
        status=p.status,
        steps=[serialize_step(s) for s in p.steps],
        milestones=[serialize_milestone(m) for m in p.milestones],
    )


def serialize_session(
    s: models.ChatSession,
) -> schemas.ChatSession:
    return schemas.ChatSession(
        id=str(s.id),
        project_id=str(s.project_id),
        scope_type=s.scope_type,
        scope_step_id=str(s.scope_step_id) if s.scope_step_id else None,
        messages=[
            schemas.ChatMessage(role=m.role, content=m.content)
            for m in s.messages
        ],
    )