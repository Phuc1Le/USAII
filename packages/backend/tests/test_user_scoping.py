"""One person's projects must not appear in another person's account.

Identity here is just the X-User-Id header, so these tests are about data
separation, not about resisting an attacker who sends someone else's key.
"""

import pytest


ALICE = {"X-User-Id": "alice-client-key"}
BOB = {"X-User-Id": "bob-client-key"}


@pytest.fixture
def alice_project(client, project_payload):
    res = client.post("/api/v1/projects", json=project_payload, headers=ALICE)
    assert res.status_code == 201, res.text
    return res.json()


def test_projects_are_listed_per_user(client, project_payload, alice_project):
    client.post("/api/v1/projects", json=project_payload, headers=BOB)

    alice_ids = {p["id"] for p in client.get("/api/v1/projects", headers=ALICE).json()}
    bob_ids = {p["id"] for p in client.get("/api/v1/projects", headers=BOB).json()}

    assert alice_project["id"] in alice_ids
    assert alice_project["id"] not in bob_ids
    assert not (alice_ids & bob_ids), "no project may appear in both accounts"


def test_another_users_project_is_indistinguishable_from_a_missing_one(client, alice_project):
    """404, not 403: a different status would confirm the project exists."""
    res = client.get(f"/api/v1/projects/{alice_project['id']}", headers=BOB)
    assert res.status_code == 404

    missing = client.get("/api/v1/projects/999999", headers=BOB)
    assert missing.status_code == res.status_code


def test_another_users_project_cannot_be_updated(client, alice_project):
    res = client.patch(
        f"/api/v1/projects/{alice_project['id']}",
        json={"status": "completed"},
        headers=BOB,
    )
    assert res.status_code == 404

    # and it is genuinely untouched
    still_active = client.get(f"/api/v1/projects/{alice_project['id']}", headers=ALICE).json()
    assert still_active["status"] == "active"


def test_another_users_decisions_are_not_readable(client, project_payload):
    payload = {
        **project_payload,
        "clarifying_answers": [{"question": "Who for?", "answer": "a secret answer"}],
    }
    project = client.post("/api/v1/projects", json=payload, headers=ALICE).json()

    assert client.get(f"/api/v1/projects/{project['id']}/decisions", headers=ALICE).status_code == 200
    assert client.get(f"/api/v1/projects/{project['id']}/decisions", headers=BOB).status_code == 404


def test_project_numbering_restarts_per_user(client, project_payload):
    fresh = {"X-User-Id": "brand-new-person"}
    project = client.post("/api/v1/projects", json=project_payload, headers=fresh).json()
    assert project["title"] == "Project 1", "a new user's first project must not be numbered after other people's"


def test_missing_header_is_rejected(anon_client):
    res = anon_client.get("/api/v1/projects")
    assert res.status_code == 400
    assert "X-User-Id" in res.json()["detail"]


def test_the_same_key_always_maps_to_the_same_user(client, project_payload, alice_project):
    """The user row is created on first sight and reused after that."""
    second = client.post("/api/v1/projects", json=project_payload, headers=ALICE).json()
    ids = {p["id"] for p in client.get("/api/v1/projects", headers=ALICE).json()}
    assert {alice_project["id"], second["id"]} <= ids
