from uuid import uuid4

from agent_lab.architectures.definitions import ARCHITECTURES
from agent_lab.architectures.pipeline import prompt_fingerprint
from agent_lab.experiments.benchmark import BenchmarkLoader
from agent_lab.experiments.case import ExperimentCase
from agent_lab.experiments.engine import ExperimentEngine
from agent_lab.experiments.store import RunManifest, RunStore
from agent_lab.llm.gemini import GeminiProvider
from agent_lab.llm.pricing import PricingRegistry
from agent_lab.llm.ratelimit import RateLimiter, UsageTracker
from agent_lab.research.tavily import TavilyResearchTool
from agent_lab.settings import Settings


class Lab:
    """
    Wires settings into the concrete objects the API and CLI share.

    The Gemini clients are created lazily, so read-only actions
    (listing runs, verifying a run) work without an API key.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = RunStore(settings.results_directory)
        self.loader = BenchmarkLoader(
            settings.benchmark_file,
            settings.research_file,
        )
        self.pricing = PricingRegistry.from_file(settings.pricing_file)
        self.usage = UsageTracker(settings.usage_file)

        self._generator_limiter = RateLimiter(settings.generator_rpm)
        self._judge_limiter = (
            self._generator_limiter
            if settings.judge_model == settings.generator_model
            else RateLimiter(settings.judge_rpm)
        )
        self._engine: ExperimentEngine | None = None

    def engine(self) -> ExperimentEngine:
        if self._engine is None:
            settings = self.settings

            generator = GeminiProvider(
                api_key=settings.gemini_api_key or "",
                model=settings.generator_model,
                rate_limiter=self._generator_limiter,
                usage_tracker=self.usage,
            )
            judge = GeminiProvider(
                api_key=settings.gemini_api_key or "",
                model=settings.judge_model,
                rate_limiter=self._judge_limiter,
                usage_tracker=self.usage,
            )

            research_tool = (
                TavilyResearchTool(settings.tavily_api_key, max_results=5)
                if settings.tavily_enabled
                else None
            )

            self._engine = ExperimentEngine(
                store=self.store,
                generator=generator,
                judge=judge,
                pricing=self.pricing,
                research_tool=research_tool,
            )

        return self._engine

    def offline_engine(self) -> ExperimentEngine:
        return ExperimentEngine(
            store=self.store,
            generator=None,
            judge=None,
            pricing=self.pricing,
        )

    def create_run(
        self,
        *,
        run_type: str,
        cases: list[ExperimentCase],
        trials: int,
        architectures: list[str] | None = None,
        label: str = "",
    ) -> RunManifest:
        settings = self.settings
        order = [architecture.name for architecture in ARCHITECTURES]
        selected = [
            name
            for name in order
            if architectures is None or name in architectures
        ]

        if not selected:
            raise ValueError("Select at least one architecture.")

        if not cases:
            raise ValueError("Select at least one case.")

        is_benchmark = run_type == "benchmark"

        return self.store.create(
            run_id=uuid4().hex[:10],
            run_type=run_type,
            label=label,
            cases=cases,
            trials=trials,
            architectures=selected,
            generator_model=settings.generator_model,
            judge_model=settings.judge_model,
            generator_temperature=settings.generator_temperature,
            judge_temperature=settings.judge_temperature,
            max_output_tokens=settings.max_output_tokens,
            prompt_fingerprint=prompt_fingerprint(),
            benchmark_version=self.loader.version() if is_benchmark else None,
            benchmark_fingerprint=self.loader.fingerprint() if is_benchmark else None,
        )
