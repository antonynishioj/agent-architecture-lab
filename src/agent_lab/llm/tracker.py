from dataclasses import dataclass, field

from agent_lab.llm.base import GenerationConfig, LLM, LLMResponse
from agent_lab.llm.pricing import PricingRegistry


@dataclass
class LLMCallRecord:
    input_tokens: int
    output_tokens: int
    thinking_tokens: int
    latency_ms: float
    model: str
    retries: int = 0
    cached: bool = False
    estimated_cost_usd: float | None = None


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
    def total_thinking_tokens(self) -> int:
        return sum(call.thinking_tokens for call in self.calls)

    @property
    def total_tokens(self) -> int:
        return (
            self.total_input_tokens
            + self.total_output_tokens
            + self.total_thinking_tokens
        )

    @property
    def total_latency_ms(self) -> float:
        return sum(call.latency_ms for call in self.calls)

    @property
    def total_retries(self) -> int:
        return sum(call.retries for call in self.calls)

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
        self.model = llm.model
        self.pricing_registry = pricing_registry
        self.metrics = LLMRunMetrics()

    def generate(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
    ) -> LLMResponse:
        response = self.llm.generate(prompt, config)

        estimated_cost = None

        if self.pricing_registry is not None:
            # Thinking tokens are billed as output tokens.
            estimated_cost = self.pricing_registry.calculate_cost(
                model=response.model,
                input_tokens=response.input_tokens,
                output_tokens=(
                    response.output_tokens
                    + response.thinking_tokens
                ),
            )

        self.metrics.calls.append(
            LLMCallRecord(
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                thinking_tokens=response.thinking_tokens,
                latency_ms=response.latency_ms,
                model=response.model,
                retries=response.retries,
                cached=response.cached,
                estimated_cost_usd=estimated_cost,
            )
        )

        return response
