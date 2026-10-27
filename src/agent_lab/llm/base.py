from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict


class GenerationConfig(BaseModel):
    """
    Sampling settings for one LLM call.

    The seed is part of the config so that repeated trials are
    distinct samples while re-runs of the same trial hit the cache.
    """

    model_config = ConfigDict(frozen=True)

    temperature: float = 0.3
    max_output_tokens: int = 4096
    seed: int | None = None
    json_schema: dict | None = None


class LLMResponse(BaseModel):
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    latency_ms: float = 0.0
    model: str = "unknown"
    retries: int = 0
    cached: bool = False


class LLM(ABC):
    """Interface that every LLM provider must implement."""

    model: str

    @abstractmethod
    def generate(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass


class QuotaExhaustedError(RuntimeError):
    """Raised when the provider reports that the daily quota is used up."""
