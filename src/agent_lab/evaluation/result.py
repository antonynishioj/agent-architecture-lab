from pydantic import BaseModel, Field


QUALITY_DIMENSIONS = (
    "answer_relevancy",
    "completeness",
    "faithfulness",
    "citation_quality",
    "uncertainty_handling",
    "overall_quality",
)


class KeyPointVerdict(BaseModel):
    point: str
    status: str  # covered | partial | missing


class EvaluationResult(BaseModel):
    answer_relevancy: float = Field(ge=0, le=1)
    completeness: float = Field(ge=0, le=1)
    faithfulness: float = Field(ge=0, le=1)
    citation_quality: float = Field(ge=0, le=1)
    uncertainty_handling: float = Field(ge=0, le=1)
    overall_quality: float = Field(ge=0, le=1)

    # Completeness as the judge scored it, before it is replaced by
    # the key-point coverage calculation.
    judge_completeness: float | None = None

    key_points: list[KeyPointVerdict] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    trap_violations: list[str] = Field(default_factory=list)
    reasoning: str = ""

    @property
    def quality_index(self) -> float:
        return sum(
            getattr(self, dimension)
            for dimension in QUALITY_DIMENSIONS
        ) / len(QUALITY_DIMENSIONS)


class DeterministicMetrics(BaseModel):
    word_count: int
    citation_count: int
    distinct_sources_cited: int
    invalid_citations: int
    citation_validity: float
    sentence_citation_coverage: float


class RankingResult(BaseModel):
    """Blind comparative ranking of all answers for one case and trial."""

    order: list[str]  # architecture names, best first
    labels: dict[str, str]  # label shown to judge -> architecture name
    reasoning: str = ""
