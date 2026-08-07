import httpx
from app.config import SERP_API_KEY, BACKEND_URL
from app.schemas import (
    WebSearchResultItem,
    WebSearchResult,
    FocusedStepContext,
    SubTaskContext,
)

SERP_API_URL = "https://serpapi.com/search"

async def web_search(query: str, num_results: int = 5) -> WebSearchResult:
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERP_API_KEY,
        "num": num_results,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(SERP_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

    organic = data.get("organic_results", [])[:num_results]
    return WebSearchResult(
        query=query,
        results=[
            WebSearchResultItem(
                title=item.get("title",""),
                link=item.get("link",""),
                snippet=item.get("snippet","")
            )
            for item in organic
        ]
    )


async def retrieve_step(step_id: str) -> FocusedStepContext:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BACKEND_URL}/internal/steps/{step_id}")
        response.raise_for_status()
        data = response.json()

    return FocusedStepContext(
        title=data["title"],
        description=data["description"],
        status=data["status"],
        intended_start=data["intended_start"],
        intended_end=data["intended_end"],
        tasks=[
            SubTaskContext(
                title=t["title"],
                detail=t["detail"],
                status=t["status"],
            )
            for t in data["tasks"]
        ],
    )
