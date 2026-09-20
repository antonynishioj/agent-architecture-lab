from pydantic import BaseModel

from agent_lab.llm.tracker import LLMRunMetrics


class ArchitectureResult(BaseModel):
    question: str
    architecture_name: str
    agent_count: int

    answer: str

    model: str

    call_count: int

    input_tokens: int
    output_tokens: int
    total_tokens: int

    latency_ms: float

    estimated_cost_usd: float | None = None

    @classmethod
    def from_run(
        cls,
        question: str,
        architecture_name: str,
        agent_count: int,
        answer: str,
        metrics: LLMRunMetrics,
        model: str,
    ) -> "ArchitectureResult":
        return cls(
            question=question,
            architecture_name=architecture_name,
            agent_count=agent_count,
            answer=answer,
            model=model,
            call_count=metrics.call_count,
            input_tokens=metrics.total_input_tokens,
            output_tokens=metrics.total_output_tokens,
            total_tokens=metrics.total_tokens,
            latency_ms=metrics.total_latency_ms,
            estimated_cost_usd=metrics.estimated_cost_usd,
        )