from pydantic import BaseModel, Field

from agent_lab.architectures.pipeline import AgentStep
from agent_lab.evaluation.result import (
    DeterministicMetrics,
    EvaluationResult,
    RankingResult,
)


class ArchitectureOutcome(BaseModel):
    """Everything one architecture produced for one case and trial."""

    architecture: str
    agent_count: int
    status: str = "completed"  # completed | failed
    error: str | None = None

    answer: str = ""
    steps: list[AgentStep] = Field(default_factory=list)

    model: str = ""
    call_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    retries: int = 0
    estimated_cost_usd: float | None = None

    evaluation: EvaluationResult | None = None
    judge_error: str | None = None
    deterministic: DeterministicMetrics | None = None


class CaseTrialResult(BaseModel):
    """One (case, trial) unit of the experiment: all architectures + judging."""

    run_id: str
    case_id: str
    trial: int
    difficulty: str
    category: str
    question: str

    outcomes: list[ArchitectureOutcome]

    ranking: RankingResult | None = None
    ranking_error: str | None = None

    completed_at: str
