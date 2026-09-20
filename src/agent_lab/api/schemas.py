from pydantic import BaseModel, Field


class CustomExperimentRequest(BaseModel):
    question: str = Field(
        min_length=10,
        max_length=5000,
    )

    reference_answer: str = Field(
        min_length=10,
        max_length=10000,
    )

    category: str = Field(
        default="Custom",
        max_length=100,
    )

    difficulty: str = Field(
        default="custom",
        max_length=50,
    )


class ExperimentStartResponse(BaseModel):
    run_id: str
    status: str
    message: str


class ExperimentStatusResponse(BaseModel):
    run_id: str
    status: str
    progress: int
    message: str
    case_id: str | None = None
    current_case: str | None = None
    current_architecture: str | None = None
    error: str | None = None


class BenchmarkListItem(BaseModel):
    case_id: str
    category: str
    difficulty: str
    question: str


class BenchmarkListResponse(BaseModel):
    count: int
    cases: list[BenchmarkListItem]