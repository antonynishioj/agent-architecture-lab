import os
import time

from dotenv import load_dotenv
from google import genai

from .base import LLM, LLMResponse


load_dotenv()


class GeminiProvider(LLM):
    """Gemini implementation of the common LLM interface."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, prompt: str) -> LLMResponse:
        start_time = time.perf_counter()

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        usage = response.usage_metadata

        input_tokens = usage.prompt_token_count or 0
        output_tokens = usage.candidates_token_count or 0

        return LLMResponse(
            text=response.text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            model=self.model,
        )