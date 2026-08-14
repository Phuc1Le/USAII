import httpx
from app.config import SERP_API_KEY, BACKEND_URL
from app.schemas import (
    WebSearchResultItem,
    WebSearchResult,
    FocusedStepContext,
    SubTaskContext,
    MilestoneContext,
    DecisionSearchHit,
    DecisionSearchResult,
)

SERP_API_URL = "https://serpapi.com/search"

async def web_search(query: str, num_results: int = 5) -> WebSearchResult:
    if not SERP_API_KEY:
        raise RuntimeError(
            "SERP_API_KEY is not set — web search is unavailable. "
            "Set it in the root .env to enable this tool."
        )
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

async def retrieve_milestones(project_id: str) -> list[MilestoneContext]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BACKEND_URL}/internal/milestones", params={"project_id": project_id})
        response.raise_for_status()
        data = response.json()

    return [
        MilestoneContext(title=m["title"], achieved_at=m["achieved_at"])
        for m in data
    ]

async def query_decisions(project_id: str, query: str, limit: int = 5) -> DecisionSearchResult:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{BACKEND_URL}/internal/decisions/search",
            params={"project_id": project_id, "query": query, "limit": limit},
        )
        response.raise_for_status()
        data = response.json()

    return DecisionSearchResult(
        query=query,
        hits=[DecisionSearchHit(**h) for h in data],
    )
