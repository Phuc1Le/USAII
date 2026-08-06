# test_tools_unit.py
import json
import httpx
import pytest

from app.tools import web_search

FIXTURE = json.load(open("fixtures/serpapi_response.json"))

@pytest.mark.asyncio
async def test_web_search_parses_serpapi_response(monkeypatch):
    def handler(request):
        return httpx.Response(200, json=FIXTURE)

    transport = httpx.MockTransport(handler)

    original_init = httpx.AsyncClient.__init__
    def patched_init(self, *args, **kwargs):
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    result = await web_search("fastapi background tasks")
    assert result.query == "fastapi background tasks"
    assert len(result.results) > 0
    assert result.results[0].title
    assert result.results[0].link.startswith("http")
