from pydantic import BaseModel, Field


class BenchmarkRunRequest(BaseModel):
    case_ids: list[str] | None = None
    trials: int = Field(default=3, ge=1, le=5)
    architectures: list[str] | None = None
    label: str = Field(default="", max_length=100)


class SourceInput(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    url: str = Field(default="", max_length=1000)
    content: str = Field(min_length=10, max_length=20000)
    published: str | None = None


class CustomExperimentRequest(BaseModel):
    question: str = Field(min_length=10, max_length=5000)
    reference_answer: str | None = Field(default=None, max_length=10000)
    key_points: list[str] = Field(default_factory=list)
    must_not_claim: list[str] = Field(default_factory=list)
    category: str = Field(default="Custom", max_length=100)
    difficulty: str = Field(default="custom", max_length=50)

    # "web" searches with Tavily once; "manual" uses the pasted sources.
    sources_mode: str = Field(default="web", pattern="^(web|manual)$")
    sources: list[SourceInput] = Field(default_factory=list)

    trials: int = Field(default=1, ge=1, le=5)
    architectures: list[str] | None = None
    label: str = Field(default="", max_length=100)


class ExperimentStartResponse(BaseModel):
    run_id: str
    status: str
    message: str
