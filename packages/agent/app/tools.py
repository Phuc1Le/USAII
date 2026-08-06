import httpx
from app.config import SERP_API_KEY
from app.schemas import WebSearchResultItem, WebSearchResult

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