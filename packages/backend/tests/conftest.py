"""Shared test setup.

The env vars below MUST be set before anything imports `app.config`, because
config.py reads os.environ at import time and every other module imports its
settings from there as plain module-level constants. python-dotenv's
load_dotenv() does not override variables that are already set, so these win
over both .env files.
"""

import os
import tempfile
from pathlib import Path

_TEST_DB = Path(tempfile.gettempdir()) / "zero_to_one_test.db"
if _TEST_DB.exists():
    _TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"
os.environ["USE_MOCK_AGENT"] = "true"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


DEFAULT_CLIENT_KEY = "test-default-user"


@pytest.fixture(scope="session")
def client():
    """A client that is always someone.

    Every project route needs X-User-Id, and tests that are not about ownership
    should not have to care — so the header is set once here, exactly like the
    frontend sets it once in api/client.ts.
    """
    # entering the context manager runs the lifespan, so init_db() applies every
    # Alembic migration to the fresh test database — the migrations are under test too
    with TestClient(app, headers={"X-User-Id": DEFAULT_CLIENT_KEY}) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def anon_client():
    """A client that sends no identity — for testing what happens without one."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def project_payload():
    return {
        "category": "health",
        "description": "Theo doi duong huyet cho nguoi tieu duong",
        "idea": "An app that reminds people to take their medication",
        "goal": "MVP",
        "complete_in": 30,
        "clarifying_answers": [],
    }
