from types import SimpleNamespace

import pytest
import httpx
from google.genai import errors

from agent_lab.llm.base import QuotaExhaustedError
from agent_lab.llm.gemini import GeminiProvider


def _response(text="ok"):
    return SimpleNamespace(
        text=text,
        usage_metadata=SimpleNamespace(
            prompt_token_count=10,
            candidates_token_count=5,
            thoughts_token_count=2,
        ),
    )


class FakeModels:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _provider(outcomes, monkeypatch):
    monkeypatch.setattr("agent_lab.llm.gemini.time.sleep", lambda seconds: None)
    provider = GeminiProvider(api_key="test", model="fake-model")
    provider.client = SimpleNamespace(models=FakeModels(outcomes))
    return provider


def _api_error(code, details):
    return errors.APIError(code, {"error": {"code": code, "message": "x", "status": "X", "details": details}})


def test_retries_rate_limit_then_succeeds(monkeypatch):
    rate_limited = _api_error(
        429,
        [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "3s"}],
    )
    provider = _provider([rate_limited, _api_error(503, []), _response()], monkeypatch)

    response = provider.generate("hello")

    assert response.text == "ok"
    assert response.retries == 2
    assert response.thinking_tokens == 2
    assert provider.client.models.calls == 3


def test_daily_quota_stops_immediately(monkeypatch):
    daily = _api_error(
        429,
        [{"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}],
    )
    provider = _provider([daily], monkeypatch)

    with pytest.raises(QuotaExhaustedError):
        provider.generate("hello")

    assert provider.client.models.calls == 1


def test_non_retryable_error_raises(monkeypatch):
    provider = _provider([_api_error(400, [])], monkeypatch)

    with pytest.raises(errors.APIError):
        provider.generate("hello")


def test_dropped_connection_is_retried(monkeypatch):
    dropped = httpx.RemoteProtocolError("Server disconnected without sending a response.")
    provider = _provider([dropped, _response()], monkeypatch)

    response = provider.generate("hello")

    assert response.text == "ok"
    assert response.retries == 1
