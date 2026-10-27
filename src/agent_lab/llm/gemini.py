import re
import time

import httpx
from google import genai
from google.genai import errors, types

from .base import (
    GenerationConfig,
    LLM,
    LLMResponse,
    QuotaExhaustedError,
)
from .ratelimit import RateLimiter, UsageTracker


RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _retry_delay_seconds(error: errors.APIError) -> float | None:
    """Read the server-suggested retry delay (e.g. "34s") if present."""

    match = re.search(
        r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s",
        str(error.details),
    )

    if match:
        return float(match.group(1))

    return None


def _is_daily_quota_error(error: errors.APIError) -> bool:
    details = str(error.details)

    return error.code == 429 and "PerDay" in details


class GeminiProvider(LLM):
    """
    Gemini implementation of the common LLM interface.

    Built for the free tier: every call goes through a rate limiter,
    transient failures are retried with backoff, and a hard daily
    quota error stops the run cleanly so it can be resumed later.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        rate_limiter: RateLimiter | None = None,
        usage_tracker: UsageTracker | None = None,
        max_retries: int = 6,
    ):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.rate_limiter = rate_limiter
        self.usage_tracker = usage_tracker
        self.max_retries = max_retries

    def _build_config(
        self,
        config: GenerationConfig,
    ) -> types.GenerateContentConfig:
        options = {
            "temperature": config.temperature,
            "max_output_tokens": config.max_output_tokens,
            # No tools are used; this also silences an SDK warning.
            "automatic_function_calling": types.AutomaticFunctionCallingConfig(
                disable=True,
            ),
        }

        if config.seed is not None:
            options["seed"] = config.seed

        if config.json_schema is not None:
            options["response_mime_type"] = "application/json"
            options["response_json_schema"] = config.json_schema

        return types.GenerateContentConfig(**options)

    def generate(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
    ) -> LLMResponse:
        config = config or GenerationConfig()
        request_config = self._build_config(config)

        attempt = 0

        while True:
            if self.rate_limiter:
                self.rate_limiter.acquire()

            if self.usage_tracker:
                self.usage_tracker.record(self.model)

            start_time = time.perf_counter()

            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=request_config,
                )
            except httpx.TransportError:
                # Dropped connections and timeouts are transient on the
                # free tier ("Server disconnected without sending a response").
                if attempt >= self.max_retries:
                    raise

                attempt += 1
                time.sleep(min(60.0, 2.0 * (2 ** attempt)))
                continue
            except errors.APIError as exc:
                if _is_daily_quota_error(exc):
                    raise QuotaExhaustedError(
                        f"Daily free-tier quota exhausted for "
                        f"{self.model}. Resume the run after the "
                        f"quota resets (midnight Pacific time)."
                    ) from exc

                if (
                    exc.code not in RETRYABLE_STATUS_CODES
                    or attempt >= self.max_retries
                ):
                    raise

                attempt += 1
                delay = _retry_delay_seconds(exc) or min(
                    60.0,
                    2.0 * (2 ** attempt),
                )
                time.sleep(delay)
                continue

            latency_ms = (time.perf_counter() - start_time) * 1000

            text = response.text or ""

            if not text.strip():
                if attempt >= self.max_retries:
                    raise RuntimeError(
                        f"{self.model} returned an empty response."
                    )

                attempt += 1
                continue

            usage = response.usage_metadata

            return LLMResponse(
                text=text,
                input_tokens=(usage.prompt_token_count or 0) if usage else 0,
                output_tokens=(usage.candidates_token_count or 0) if usage else 0,
                thinking_tokens=(usage.thoughts_token_count or 0) if usage else 0,
                latency_ms=latency_ms,
                model=self.model,
                retries=attempt,
            )
