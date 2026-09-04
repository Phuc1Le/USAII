"""An agent failure must reach the user as a sentence, not as encoded JSON."""

import json

import httpx
import pytest
from fastapi import HTTPException

from app.agent_client import _agent_error_detail, _raise_for_agent_error


def _response(status_code: int, json_body=None, text: str | None = None) -> httpx.Response:
    request = httpx.Request("POST", "http://agent:8001/agent/plan")
    if json_body is not None:
        return httpx.Response(status_code, json=json_body, request=request)
    return httpx.Response(status_code, text=text or "", request=request)


def test_agent_detail_is_unwrapped_not_re_encoded():
    """Regression: the agent's whole JSON body was passed through as our detail.

    FastAPI then serialized it a second time, and the frontend's apiError() — which
    unwraps `detail` exactly once — showed the user the escaped blob instead.
    """
    reason = "Gemini JSON call failed: 429 RESOURCE_EXHAUSTED"
    res = _response(502, json_body={"detail": reason})

    assert _agent_error_detail(res) == reason
    # what the frontend would read after FastAPI serializes our HTTPException
    with pytest.raises(HTTPException) as excinfo:
        _raise_for_agent_error(res)
    shown_to_user = json.loads(json.dumps({"detail": excinfo.value.detail}))["detail"]
    assert shown_to_user == reason
    assert "{" not in shown_to_user, "the user must never see raw JSON"


def test_status_code_is_preserved():
    """The frontend special-cases 429 to explain a quota problem in plain language."""
    res = _response(429, json_body={"detail": "RESOURCE_EXHAUSTED"})
    with pytest.raises(HTTPException) as excinfo:
        _raise_for_agent_error(res)
    assert excinfo.value.status_code == 429


def test_non_json_body_falls_back_to_text():
    res = _response(502, text="Bad Gateway")
    assert _agent_error_detail(res) == "Bad Gateway"


def test_validation_error_list_is_kept_readable():
    errors = [{"loc": ["body", "idea"], "msg": "Field required"}]
    res = _response(422, json_body={"detail": errors})
    assert "Field required" in _agent_error_detail(res)


def test_empty_body_still_says_something():
    res = _response(500, text="")
    assert _agent_error_detail(res) == "Agent returned HTTP 500"


def test_success_response_raises_nothing():
    assert _raise_for_agent_error(_response(200, json_body={"ok": True})) is None
