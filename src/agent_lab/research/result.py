from pydantic import BaseModel


class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    score: float = 0.0


class ResearchBundle(BaseModel):
    query: str
    results: list[SearchResult]