import hashlib
import json
from pathlib import Path
from threading import Lock

from agent_lab.llm.base import GenerationConfig, LLM, LLMResponse


class CacheMissError(RuntimeError):
    """Raised in offline (replay) mode when a prompt is not cached."""


def cache_key(
    model: str,
    prompt: str,
    config: GenerationConfig,
) -> str:
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "config": config.model_dump(),
        },
        sort_keys=True,
    )

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ResponseCache:
    """
    Append-only JSONL log of every prompt and response in a run.

    It serves two purposes:
    1. Resuming a run never pays twice for the same call.
    2. Anyone can replay the run offline and verify the results.
    """

    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()
        self._entries: dict[str, dict] = {}

        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                self._entries[entry["key"]] = entry

    def get(self, key: str) -> dict | None:
        with self._lock:
            return self._entries.get(key)

    def put(self, entry: dict) -> None:
        with self._lock:
            self._entries[entry["key"]] = entry

            self.path.parent.mkdir(parents=True, exist_ok=True)

            with self.path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(entry, ensure_ascii=False) + "\n")


class CachedLLM(LLM):
    """
    Serves responses from the run cache when possible.

    With llm=None it works fully offline and raises CacheMissError
    for unknown prompts. That is how `agent-lab replay` verifies a
    published run without an API key.
    """

    def __init__(
        self,
        llm: LLM | None,
        cache: ResponseCache,
        model: str | None = None,
    ):
        self.llm = llm
        self.cache = cache
        self.model = model or (llm.model if llm else "unknown")

    def generate(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
    ) -> LLMResponse:
        config = config or GenerationConfig()
        key = cache_key(self.model, prompt, config)

        entry = self.cache.get(key)

        if entry is not None:
            response = LLMResponse.model_validate(entry["response"])
            return response.model_copy(update={"cached": True})

        if self.llm is None:
            raise CacheMissError(
                f"Prompt not found in cache for model {self.model}."
            )

        response = self.llm.generate(prompt, config)

        self.cache.put(
            {
                "key": key,
                "model": self.model,
                "config": config.model_dump(),
                "prompt": prompt,
                "response": response.model_dump(),
            }
        )

        return response
