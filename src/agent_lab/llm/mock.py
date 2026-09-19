from .base import LLM, LLMResponse


class MockLLM(LLM):
    """Fake LLM used during development and testing."""

    def generate(self, prompt: str) -> LLMResponse:
        response = f"Mock response to: {prompt}"

        return LLMResponse(
            text=response,
            input_tokens=len(prompt.split()),
            output_tokens=len(response.split()),
            model="mock",
        )