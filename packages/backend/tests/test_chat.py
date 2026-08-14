"""Chat streaming: SSE framing and persistence of the assistant turn."""

import pytest


@pytest.fixture
def session_id(client, project_payload):
    project = client.post("/api/v1/projects", json=project_payload).json()
    res = client.post(
        "/api/v1/chat/sessions",
        json={"project_id": project["id"], "scope_type": "project"},
    )
    assert res.status_code == 200, res.text
    return res.json()["id"]


def test_send_message_streams_sse_and_terminates(client, session_id):
    res = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "What should I do first?"},
    )
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/event-stream")

    body = res.text
    assert body.startswith("data: ")
    # the literal terminator the frontend and the backend's own parser both rely on
    assert body.endswith("data: [DONE]\n\n")


def test_both_turns_are_persisted(client, session_id):
    client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "Hello there"},
    )

    session = client.post(
        "/api/v1/chat/sessions",
        json={
            "project_id": client.get("/api/v1/projects").json()[-1]["id"],
            "scope_type": "project",
        },
    ).json()
    assert session["id"] == session_id, "opening the same scope must reuse the session"

    roles = [m["role"] for m in session["messages"]]
    assert roles == ["user", "assistant"]
    assert session["messages"][0]["content"] == "Hello there"
    assert session["messages"][1]["content"], "the assistant turn must not be saved empty"


def test_message_to_missing_session_is_404(client):
    res = client.post("/api/v1/chat/sessions/999999/messages", json={"content": "hi"})
    assert res.status_code == 404
