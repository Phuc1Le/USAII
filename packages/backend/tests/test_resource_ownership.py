"""Routes addressed by a raw id must not serve another user's data.

Every one of these is reachable by guessing a small integer, so "you would have
to know the id" is not a defence.
"""

import pytest


ALICE = {"X-User-Id": "owner-alice"}
BOB = {"X-User-Id": "intruder-bob"}


@pytest.fixture
def alice(client, project_payload):
    """A project of Alice's with a step, a task, a milestone and a chat session."""
    project = client.post("/api/v1/projects", json=project_payload, headers=ALICE).json()
    step = project["steps"][0]
    task = client.get(f"/api/v1/steps/{step['id']}/tasks", headers=ALICE).json()[0]
    session = client.post(
        "/api/v1/chat/sessions",
        json={"project_id": project["id"], "scope_type": "project"},
        headers=ALICE,
    ).json()
    return {
        "project": project,
        "step": step,
        "task": task,
        "milestone": project["milestones"][0],
        "session": session,
    }


def test_bob_cannot_read_alices_tasks(client, alice):
    """Regression: the route returned existing tasks before it ever loaded the step.

    Checking ownership after that early return would have left already-generated
    tasks readable by anyone who guessed the step id.
    """
    res = client.get(f"/api/v1/steps/{alice['step']['id']}/tasks", headers=BOB)
    assert res.status_code == 404


def test_bob_cannot_update_alices_step(client, alice):
    res = client.patch(
        f"/api/v1/steps/{alice['step']['id']}", json={"status": "done"}, headers=BOB
    )
    assert res.status_code == 404


def test_bob_cannot_update_alices_task(client, alice):
    res = client.patch(
        f"/api/v1/tasks/{alice['task']['id']}", json={"status": "done"}, headers=BOB
    )
    assert res.status_code == 404

    # and the task really is untouched
    tasks = client.get(f"/api/v1/steps/{alice['step']['id']}/tasks", headers=ALICE).json()
    changed = next(t for t in tasks if t["id"] == alice["task"]["id"])
    assert changed["status"] == "todo"


def test_bob_cannot_update_alices_milestone(client, alice):
    res = client.patch(
        f"/api/v1/milestones/{alice['milestone']['id']}", json={"achieved": True}, headers=BOB
    )
    assert res.status_code == 404


def test_bob_cannot_open_a_session_on_alices_project(client, alice):
    res = client.post(
        "/api/v1/chat/sessions",
        json={"project_id": alice["project"]["id"], "scope_type": "project"},
        headers=BOB,
    )
    assert res.status_code == 404


def test_bob_cannot_post_into_alices_session(client, alice):
    res = client.post(
        f"/api/v1/chat/sessions/{alice['session']['id']}/messages",
        json={"content": "let me in"},
        headers=BOB,
    )
    assert res.status_code == 404


def test_alice_can_still_do_all_of_it(client, alice):
    """The guard must not lock the owner out — the boring half of every check."""
    assert client.get(f"/api/v1/steps/{alice['step']['id']}/tasks", headers=ALICE).status_code == 200
    assert client.patch(
        f"/api/v1/steps/{alice['step']['id']}", json={"status": "in_progress"}, headers=ALICE
    ).status_code == 200
    assert client.patch(
        f"/api/v1/tasks/{alice['task']['id']}", json={"status": "done"}, headers=ALICE
    ).status_code == 200
    assert client.patch(
        f"/api/v1/milestones/{alice['milestone']['id']}", json={"achieved": True}, headers=ALICE
    ).status_code == 200
    assert client.post(
        f"/api/v1/chat/sessions/{alice['session']['id']}/messages",
        json={"content": "what next?"},
        headers=ALICE,
    ).status_code == 200
