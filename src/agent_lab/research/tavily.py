import requests

from agent_lab.research.base import ResearchTool
from agent_lab.research.result import ResearchBundle, SearchResult


class TavilyResearchTool(ResearchTool):

    def __init__(
        self,
        api_key: str | None,
        max_results: int = 5,
    ):
        if not api_key:
            raise ValueError("TAVILY_API_KEY is not set.")

        self.api_key = api_key
        self.max_results = max_results
        self.url = "https://api.tavily.com/search"

    def search(self, query: str) -> ResearchBundle:

        response = requests.post(
            self.url,
            headers={
                "Content-Type": "application/json",
            },
            json={
                "api_key": self.api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": self.max_results,
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        results = [
            SearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                content=result.get("content", ""),
                score=result.get("score", 0.0),
                published=result.get("published_date"),
            )
            for result in data.get("results", [])
        ]

        return ResearchBundle(
            query=query,
            results=results,
        )