from dataclasses import dataclass, field

from agent_lab.llm.base import LLM, LLMResponse
from agent_lab.llm.pricing import PricingRegistry


@dataclass
class LLMCallRecord:
    input_tokens: int
    output_tokens: int
    latency_ms: float
    model: str
    estimated_cost_usd: float | None = None


@dataclass
class LLMRunMetrics:
    calls: list[LLMCallRecord] = field(default_factory=list)

    @property
    def total_input_tokens(self) -> int:
        return sum(
            call.input_tokens
            for call in self.calls
        )

    @property
    def total_output_tokens(self) -> int:
        return sum(
            call.output_tokens
            for call in self.calls
        )

    @property
    def total_tokens(self) -> int:
        return (
            self.total_input_tokens
            + self.total_output_tokens
        )

    @property
    def total_latency_ms(self) -> float:
        return sum(
            call.latency_ms
            for call in self.calls
        )

    @property
    def call_count(self) -> int:
        return len(self.calls)

    @property
    def estimated_cost_usd(self) -> float | None:
        costs = [
            call.estimated_cost_usd
            for call in self.calls
            if call.estimated_cost_usd is not None
        ]

        if not costs:
            return None

        return sum(costs)


class TrackingLLM(LLM):
    """
    Wraps any LLM provider and records execution metrics.

    The provider itself does not need to know anything about
    experiments, architecture, pricing, or evaluation.
    """

    def __init__(
        self,
        llm: LLM,
        pricing_registry: PricingRegistry | None = None,
    ):
        self.llm = llm
        self.pricing_registry = pricing_registry
        self.metrics = LLMRunMetrics()

    def generate(self, prompt: str) -> LLMResponse:
        response = self.llm.generate(prompt)

        estimated_cost = None

        if self.pricing_registry is not None:
            estimated_cost = self.pricing_registry.calculate_cost(
                model=response.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
            )

        self.metrics.calls.append(
            LLMCallRecord(
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                latency_ms=response.latency_ms,
                model=response.model,
                estimated_cost_usd=estimated_cost,
            )
        )

        return response