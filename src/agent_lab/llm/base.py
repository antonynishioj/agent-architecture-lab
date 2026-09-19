from abc import ABC, abstractmethod

from pydantic import BaseModel


class LLMResponse(BaseModel):
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    model: str = "unknown"


class LLM(ABC):
    """Interface that every LLM provider must implement."""

    @abstractmethod
    def generate(self, prompt: str) -> LLMResponse:
        """Generate a response from the LLM."""
        pass