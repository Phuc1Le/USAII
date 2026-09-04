"""Project creation: the multi-step flow that calls the agent and then writes."""

import pytest
from fastapi import HTTPException

from app import agent_client, schemas


def test_create_project_returns_plan(client, project_payload):
    res = client.post("/api/v1/projects", json=project_payload)
    assert res.status_code == 201, res.text

    project = res.json()
    assert project["idea"] == project_payload["idea"]
    # the mock agent returns 3 steps and 1 milestone
    assert len(project["steps"]) == 3
    assert len(project["milestones"]) == 1
    # dependencies from the plan are wired to real step ids, not order_index values
    assert [s["order_index"] for s in project["steps"]] == [1, 2, 3]


def test_create_project_forwards_category_and_description(client, project_payload, monkeypatch):
    """Regression: the category never reached the agent, so every plan was generic.

    build_plan_prompt() picks its category-specific guidance from these fields;
    with them missing it silently fell back to the generic branch.
    """
    captured = {}
    real_generate_plan = agent_client.generate_plan

    def spy(body: schemas.PlanRequest):
        captured["body"] = body
        return real_generate_plan(body)

    monkeypatch.setattr(agent_client, "generate_plan", spy)

    res = client.post("/api/v1/projects", json=project_payload)
    assert res.status_code == 201, res.text

    sent = captured["body"]
    assert sent.category == project_payload["category"]
    assert sent.description == project_payload["description"]
    assert sent.complete_in == project_payload["complete_in"]


def test_failed_plan_leaves_no_project_behind(client, project_payload, monkeypatch):
    """Regression: a 502 from the agent used to leave an orphaned, step-less project.

    The project row was committed before the agent call, so a failure stranded it
    in the database and in GET /projects.
    """
    before = len(client.get("/api/v1/projects").json())

    def boom(body):
        raise HTTPException(status_code=502, detail="Gemini JSON call failed")

    monkeypatch.setattr(agent_client, "generate_plan", boom)

    res = client.post("/api/v1/projects", json=project_payload)
    assert res.status_code == 502

    after = client.get("/api/v1/projects").json()
    assert len(after) == before
    assert all(p["idea"] != project_payload["idea"] or p["steps"] for p in after)


def test_clarifying_answers_are_saved_as_decisions(client, project_payload):
    payload = {
        **project_payload,
        "clarifying_answers": [
            {"question": "Who is the primary user?", "answer": "Type 2 diabetes patients over 50"},
            {"question": "What must it do?", "answer": ""},  # blank ones are skipped
        ],
    }
    project = client.post("/api/v1/projects", json=payload).json()

    decisions = client.get(f"/api/v1/projects/{project['id']}/decisions").json()
    assert len(decisions) == 1
    assert "Type 2 diabetes patients over 50" in decisions[0]["content"]


def test_get_missing_project_is_404(client):
    assert client.get("/api/v1/projects/999999").status_code == 404
