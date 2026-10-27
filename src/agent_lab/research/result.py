from pydantic import BaseModel


class SearchResult(BaseModel):
    title: str
    url: str = ""
    content: str
    score: float = 0.0
    published: str | None = None


class ResearchBundle(BaseModel):
    query: str
    results: list[SearchResult]

    def format_sources(self) -> str:
        """Render the sources with stable IDs ([S1], [S2], ...) for prompts."""

        if not self.results:
            return "(No sources were found.)"

        blocks = []

        for index, result in enumerate(self.results, start=1):
            lines = [f"[S{index}] {result.title}"]

            if result.url:
                lines.append(f"URL: {result.url}")

            if result.published:
                lines.append(f"Published: {result.published}")

            lines.append(f"Content: {result.content}")

            blocks.append("\n".join(lines))

        return "\n\n".join(blocks)
