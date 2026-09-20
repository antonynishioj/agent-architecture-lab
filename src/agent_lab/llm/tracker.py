from dataclasses import dataclass, field

from agent_lab.llm.base import LLM, LLMResponse


@dataclass
class LLMCallRecord:
    input_tokens: int
    output_tokens: int
    latency_ms: float
    model: str


@dataclass
class LLMRunMetrics:
    calls: list[LLMCallRecord] = field(default_factory=list)

    @property
    def total_input_tokens(self) -> int:
        return sum(call.input_tokens for call in self.calls)

    @property
    def total_output_tokens(self) -> int:
        return sum(call.output_tokens for call in self.calls)

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def total_latency_ms(self) -> float:
        return sum(call.latency_ms for call in self.calls)

    @property
    def call_count(self) -> int:
        return len(self.calls)


class TrackingLLM(LLM):
    """Wraps an LLM and records every call made during an architecture run."""

    def __init__(self, llm: LLM):
        self.llm = llm
        self.metrics = LLMRunMetrics()

    def generate(self, prompt: str) -> LLMResponse:
        response = self.llm.generate(prompt)

        self.metrics.calls.append(
            LLMCallRecord(
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                latency_ms=response.latency_ms,
                model=response.model,
            )
        )

        return response