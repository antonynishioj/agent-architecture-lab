import os

import requests
from dotenv import load_dotenv

from agent_lab.research.base import ResearchTool
from agent_lab.research.result import ResearchBundle, SearchResult


load_dotenv()


class TavilyResearchTool(ResearchTool):

    def __init__(
        self,
        max_results: int = 5,
    ):
        api_key = os.getenv("TAVILY_API_KEY")

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
            )
            for result in data.get("results", [])
        ]

        return ResearchBundle(
            query=query,
            results=results,
        )