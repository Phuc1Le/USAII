"""Lazy task generation, including the concurrency guard."""

import pytest
from sqlalchemy.exc import IntegrityError

from app import crud, schemas
from app.database import session_scope


@pytest.fixture
def step_id(client, project_payload):
    project = client.post("/api/v1/projects", json=project_payload).json()
    return project["steps"][0]["id"]


def test_tasks_are_generated_once_then_reused(client, step_id, monkeypatch):
    calls = {"n": 0}
    from app import agent_client

    real_generate_tasks = agent_client.generate_tasks

    def counting(step, project_idea):
        calls["n"] += 1
        return real_generate_tasks(step, project_idea)

    monkeypatch.setattr(agent_client, "generate_tasks", counting)

    first = client.get(f"/api/v1/steps/{step_id}/tasks").json()
    second = client.get(f"/api/v1/steps/{step_id}/tasks").json()

    assert calls["n"] == 1, "the agent must only be called when a step has no tasks yet"
    assert [t["id"] for t in first] == [t["id"] for t in second]


def test_duplicate_task_order_is_rejected(client, step_id):
    """Regression: two concurrent readers both inserted a full set of tasks.

    The check-then-write in GET /steps/{id}/tasks cannot prevent that on its own,
    so uq_tasks_step_order makes the losing insert fail at the database level.
    """
    client.get(f"/api/v1/steps/{step_id}/tasks")  # first set lands

    subtasks = [schemas.SubTask(title="Duplicate", detail="same order_index as an existing task")]
    with session_scope() as db:
        with pytest.raises(IntegrityError):
            crud.create_tasks_for_step(db, step_id, subtasks)


def test_tasks_for_missing_step_is_404(client):
    assert client.get("/api/v1/steps/999999/tasks").status_code == 404


def test_task_status_can_be_updated(client, step_id):
    task = client.get(f"/api/v1/steps/{step_id}/tasks").json()[0]
    res = client.patch(f"/api/v1/tasks/{task['id']}", json={"status": "done"})
    assert res.status_code == 200
    assert res.json()["status"] == "done"
