"""The /internal/* routes are agent-only and must not be open to the internet."""

import pytest

from app import main


@pytest.fixture
def step_id(client, project_payload):
    project = client.post("/api/v1/projects", json=project_payload).json()
    return project["steps"][0]["id"]


def test_internal_routes_are_open_when_no_token_is_configured(client, step_id):
    """Local dev keeps working without extra setup — startup logs a warning instead."""
    assert main.INTERNAL_API_TOKEN == ""
    assert client.get(f"/internal/steps/{step_id}").status_code == 200


def test_internal_routes_reject_a_missing_token(client, step_id, monkeypatch):
    monkeypatch.setattr(main, "INTERNAL_API_TOKEN", "s3cret")
    res = client.get(f"/internal/steps/{step_id}")
    assert res.status_code == 403


def test_internal_routes_reject_a_wrong_token(client, step_id, monkeypatch):
    monkeypatch.setattr(main, "INTERNAL_API_TOKEN", "s3cret")
    res = client.get(f"/internal/steps/{step_id}", headers={"X-Internal-Token": "guess"})
    assert res.status_code == 403


def test_internal_routes_accept_the_right_token(client, step_id, monkeypatch):
    monkeypatch.setattr(main, "INTERNAL_API_TOKEN", "s3cret")
    res = client.get(f"/internal/steps/{step_id}", headers={"X-Internal-Token": "s3cret"})
    assert res.status_code == 200


def test_public_routes_are_unaffected_by_the_token(client, monkeypatch):
    monkeypatch.setattr(main, "INTERNAL_API_TOKEN", "s3cret")
    assert client.get("/api/v1/projects").status_code == 200
