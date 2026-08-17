"""Registration, login, and the rule that decides which credential is accepted."""

import pytest

from app import models
from app.database import session_scope


CREDS = {"email": "alice@example.com", "password": "correct horse battery"}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def registered(anon_client):
    # session-scoped: an email can only be registered once, and the test database
    # lives for the whole session
    res = anon_client.post("/api/v1/auth/register", json=CREDS)
    assert res.status_code == 201, res.text
    return res.json()


def test_register_returns_a_usable_token(anon_client, registered):
    me = anon_client.get("/api/v1/auth/me", headers=_auth(registered["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == CREDS["email"]


def test_register_claims_the_anonymous_account_and_its_projects(anon_client, project_payload):
    """Signing up must not lose what was made before signing up."""
    key = {"X-User-Id": "browser-that-will-register"}
    project = anon_client.post("/api/v1/projects", json=project_payload, headers=key).json()

    res = anon_client.post(
        "/api/v1/auth/register",
        json={"email": "claimer@example.com", "password": "a-long-enough-pass"},
        headers=key,
    )
    assert res.status_code == 201, res.text

    token = _auth(res.json()["access_token"])
    ids = {p["id"] for p in anon_client.get("/api/v1/projects", headers=token).json()}
    assert project["id"] in ids


def test_the_header_stops_working_once_an_account_has_a_password(anon_client, project_payload):
    """The point of the whole design: registering closes the anonymous door."""
    key = {"X-User-Id": "browser-that-registers-then-retries"}
    anon_client.post("/api/v1/projects", json=project_payload, headers=key)
    anon_client.post(
        "/api/v1/auth/register",
        json={"email": "closed@example.com", "password": "a-long-enough-pass"},
        headers=key,
    )

    # same key that worked a moment ago
    res = anon_client.get("/api/v1/projects", headers=key)
    assert res.status_code == 401
    assert "password" in res.json()["detail"].lower()


def test_registering_cannot_hijack_an_account_that_already_has_a_password(anon_client):
    key = {"X-User-Id": "victim-key"}
    anon_client.post(
        "/api/v1/auth/register",
        json={"email": "victim@example.com", "password": "victims-own-password"},
        headers=key,
    )

    # an attacker who learned the client_key tries to register over it
    res = anon_client.post(
        "/api/v1/auth/register",
        json={"email": "attacker@example.com", "password": "attackers-password"},
        headers=key,
    )
    assert res.status_code == 201  # they get an account...

    # ...but a brand new one, and the victim's password still works
    login = anon_client.post(
        "/api/v1/auth/login",
        json={"email": "victim@example.com", "password": "victims-own-password"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["id"] != res.json()["user"]["id"]


def test_login_works_and_wrong_password_does_not(anon_client, registered):
    ok = anon_client.post("/api/v1/auth/login", json=CREDS)
    assert ok.status_code == 200

    bad = anon_client.post(
        "/api/v1/auth/login", json={**CREDS, "password": "not-the-password"}
    )
    assert bad.status_code == 401


def test_unknown_email_and_wrong_password_are_indistinguishable(anon_client, registered):
    """Different messages would reveal which emails have accounts here."""
    wrong_password = anon_client.post("/api/v1/auth/login", json={**CREDS, "password": "nope-not-it"})
    no_such_user = anon_client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "nope-not-it"}
    )
    assert wrong_password.status_code == no_such_user.status_code == 401
    assert wrong_password.json()["detail"] == no_such_user.json()["detail"]


def test_email_is_case_insensitive(anon_client, registered):
    res = anon_client.post(
        "/api/v1/auth/login", json={"email": "ALICE@Example.COM", "password": CREDS["password"]}
    )
    assert res.status_code == 200


def test_duplicate_email_is_rejected(anon_client, registered):
    res = anon_client.post("/api/v1/auth/register", json=CREDS)
    assert res.status_code == 409


def test_password_is_never_stored_in_the_clear(anon_client, registered):
    with session_scope() as db:
        user = db.query(models.User).filter(models.User.email == CREDS["email"]).one()
        assert user.password_hash
        assert CREDS["password"] not in user.password_hash
        assert user.password_hash.startswith("$2")  # bcrypt's own marker


def test_short_passwords_are_rejected(anon_client):
    res = anon_client.post(
        "/api/v1/auth/register", json={"email": "short@example.com", "password": "abc"}
    )
    assert res.status_code == 422


def test_garbage_and_missing_tokens_are_rejected(anon_client):
    assert anon_client.get("/api/v1/auth/me", headers=_auth("not-a-real-token")).status_code == 401
    assert anon_client.get("/api/v1/auth/me", headers={"Authorization": "Basic abc"}).status_code == 401
    assert anon_client.get("/api/v1/auth/me").status_code == 401


def test_two_accounts_still_cannot_see_each_other(anon_client, project_payload):
    """Everything user scoping guaranteed must survive the switch to tokens."""
    a = anon_client.post(
        "/api/v1/auth/register", json={"email": "a@example.com", "password": "a-long-enough-pass"}
    ).json()
    b = anon_client.post(
        "/api/v1/auth/register", json={"email": "b@example.com", "password": "b-long-enough-pass"}
    ).json()

    project = anon_client.post(
        "/api/v1/projects", json=project_payload, headers=_auth(a["access_token"])
    ).json()

    seen_by_b = anon_client.get("/api/v1/projects", headers=_auth(b["access_token"])).json()
    assert project["id"] not in {p["id"] for p in seen_by_b}
    assert anon_client.get(
        f"/api/v1/projects/{project['id']}", headers=_auth(b["access_token"])
    ).status_code == 404
