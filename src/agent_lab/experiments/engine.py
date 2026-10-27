from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from agent_lab.architectures.definitions import ARCHITECTURES_BY_NAME
from agent_lab.architectures.pipeline import AgentStep, PipelineArchitecture
from agent_lab.evaluation.deterministic import compute_metrics
from agent_lab.evaluation.llm_judge import LLMJudge
from agent_lab.evaluation.ranking_judge import RankingJudge
from agent_lab.experiments.case import ExperimentCase
from agent_lab.experiments.result import ArchitectureOutcome, CaseTrialResult
from agent_lab.experiments.store import RunItem, RunManifest, RunStore, utc_now
from agent_lab.llm.base import GenerationConfig, LLM, QuotaExhaustedError
from agent_lab.llm.cache import CachedLLM, CacheMissError, ResponseCache
from agent_lab.llm.pricing import PricingRegistry
from agent_lab.llm.tracker import TrackingLLM
from agent_lab.research.base import ResearchTool


ProgressCallback = Callable[[dict], None]

JUDGE_SEED = 42


def calls_per_item(architectures: list[str]) -> dict[str, int]:
    """How many LLM calls one (case, trial) unit costs, per model role."""

    generator = sum(
        ARCHITECTURES_BY_NAME[name].agent_count
        for name in architectures
    )

    judge = len(architectures) + (1 if len(architectures) > 1 else 0)

    return {"generator": generator, "judge": judge}


def generator_seed(trial: int) -> int:
    return 1000 + trial


def _parallel(function: Callable, items: list) -> list:
    """Map in threads, preserving order; the first exception propagates."""

    if len(items) <= 1:
        return [function(item) for item in items]

    with ThreadPoolExecutor(max_workers=len(items)) as pool:
        return list(pool.map(function, items))


class ExperimentEngine:
    """
    Executes a run stored in a RunStore.

    For every (case, trial) unit:
    1. each selected architecture answers the question,
    2. the judge scores every answer independently (blind),
    3. the ranking judge orders all answers side by side (blind),
    4. the unit is saved, so an interrupted run resumes where it stopped.
    """

    def __init__(
        self,
        store: RunStore,
        generator: LLM | None,
        judge: LLM | None,
        pricing: PricingRegistry | None = None,
        research_tool: ResearchTool | None = None,
    ):
        self.store = store
        self.generator = generator
        self.judge = judge
        self.pricing = pricing
        self.research_tool = research_tool

    @staticmethod
    def _emit(callback: ProgressCallback | None, **event) -> None:
        if callback:
            callback(event)

    def prepare_research(
        self,
        manifest: RunManifest,
        progress: ProgressCallback | None = None,
    ) -> None:
        """Custom cases without pasted sources are searched once, then frozen."""

        path = self.store.root / manifest.directory
        cases = self.store.load_cases(path)

        changed = False

        for case in cases:
            if case.research is not None and case.research.results:
                continue

            if self.research_tool is None:
                raise RuntimeError(
                    "This case has no sources and web search is not "
                    "configured. Paste sources or set TAVILY_API_KEY."
                )

            self._emit(
                progress,
                stage="research_started",
                message="Searching the web for evidence...",
                case_id=case.case_id,
            )

            case.research = self.research_tool.search(case.question)
            case.source_kind = "web"
            changed = True

            if not case.research.results:
                raise RuntimeError("Web search returned no sources.")

            self._emit(
                progress,
                stage="research_completed",
                message=(
                    f"Found {len(case.research.results)} sources. They "
                    f"are frozen and shared by every architecture."
                ),
                case_id=case.case_id,
            )

        if changed:
            self.store.save_cases(path, cases)

    def run(
        self,
        run_id: str,
        progress: ProgressCallback | None = None,
        offline: bool = False,
    ) -> RunManifest:
        from agent_lab.analysis.report import write_reports

        manifest = self.store.load(run_id)

        if manifest is None:
            raise FileNotFoundError(f"Run not found: {run_id}")

        path = self.store.root / manifest.directory

        if not offline:
            # A run must use one generator and one judge throughout, or
            # its results would silently mix two models.
            for role, provider, expected in (
                ("generator", self.generator, manifest.generator_model),
                ("judge", self.judge, manifest.judge_model),
            ):
                if provider is not None and provider.model != expected:
                    raise RuntimeError(
                        f"This run was started with {role} model "
                        f"'{expected}', but the server is configured for "
                        f"'{provider.model}'. Restore the original model in "
                        f".env to resume it, or start a new run."
                    )

            self.prepare_research(manifest, progress)

        cases = {
            case.case_id: case
            for case in self.store.load_cases(path)
        }

        cache = ResponseCache(path / "llm_cache.jsonl")

        generator = CachedLLM(
            None if offline else self.generator,
            cache,
            model=manifest.generator_model,
        )
        judge = CachedLLM(
            None if offline else self.judge,
            cache,
            model=manifest.judge_model,
        )

        manifest.status = "running"
        manifest.error = None
        manifest.started_at = manifest.started_at or utc_now()
        self.store.save(manifest)

        per_item = calls_per_item(manifest.architectures)
        calls_each = per_item["generator"] + per_item["judge"]
        total_calls = max(1, len(manifest.items) * calls_each)

        state = {"done": manifest.completed_items * calls_each}
        tick_lock = Lock()

        def tick(message: str, **extra) -> None:
            with tick_lock:
                state["done"] += 1
                done = state["done"]

            self._emit(
                progress,
                stage="call_completed",
                message=message,
                progress=min(99, int(done / total_calls * 100)),
                **extra,
            )

        pending = [
            item
            for item in manifest.items
            if item.status != "completed"
        ]

        for position, item in enumerate(pending, start=1):
            case = cases[item.case_id]

            self._emit(
                progress,
                stage="item_started",
                message=(
                    f"Case {item.case_id}, trial {item.trial} "
                    f"({position}/{len(pending)} remaining units)"
                ),
                case_id=item.case_id,
                trial=item.trial,
                progress=min(99, int(state["done"] / total_calls * 100)),
            )

            try:
                result = self._run_item(
                    manifest=manifest,
                    item=item,
                    case=case,
                    generator=generator,
                    judge=judge,
                    tick=tick,
                    progress=progress,
                )
            except (QuotaExhaustedError, CacheMissError) as exc:
                manifest.status = "paused"
                manifest.error = str(exc)
                self.store.save(manifest)
                write_reports(path)
                raise
            except Exception as exc:
                item.status = "failed"
                item.error = f"{type(exc).__name__}: {exc}"
                self.store.save(manifest)
                state["done"] = (
                    manifest.completed_items + manifest.failed_items
                ) * calls_each
                continue

            item.file = self.store.save_item(path, result)
            item.status = "completed"
            item.error = None
            self.store.save(manifest)

            state["done"] = (
                manifest.completed_items + manifest.failed_items
            ) * calls_each

            write_reports(path)

        manifest.status = (
            "completed_with_errors"
            if manifest.failed_items
            else "completed"
        )
        manifest.completed_at = utc_now()
        self.store.save(manifest)

        write_reports(path)

        self._emit(
            progress,
            stage="run_completed",
            message="Run completed.",
            progress=100,
        )

        return manifest

    def _run_item(
        self,
        *,
        manifest: RunManifest,
        item: RunItem,
        case: ExperimentCase,
        generator: LLM,
        judge: LLM,
        tick: Callable[..., None],
        progress: ProgressCallback | None,
    ) -> CaseTrialResult:
        research = case.research

        if research is None:
            raise RuntimeError(f"Case {case.case_id} has no research.")

        generation_config = GenerationConfig(
            temperature=manifest.generator_temperature,
            max_output_tokens=manifest.max_output_tokens,
            seed=generator_seed(item.trial),
        )

        judge_config = GenerationConfig(
            temperature=manifest.judge_temperature,
            max_output_tokens=manifest.max_output_tokens,
            seed=JUDGE_SEED,
        )

        def run_architecture(name: str) -> ArchitectureOutcome:
            definition = ARCHITECTURES_BY_NAME[name]
            tracking = TrackingLLM(generator, self.pricing)

            self._emit(
                progress,
                stage="architecture_started",
                message=f"{name}: running {definition.agent_count} agent(s)",
                case_id=case.case_id,
                trial=item.trial,
                architecture=name,
            )

            def on_step(step: AgentStep, name=name, definition=definition) -> None:
                roles = " + ".join(step.roles)

                tick(
                    f"{name}: agent {step.agent_index + 1}/"
                    f"{definition.agent_count} ({roles}) finished "
                    f"in {step.latency_ms / 1000:.1f}s",
                    case_id=case.case_id,
                    trial=item.trial,
                    architecture=name,
                )

            try:
                answer, steps = PipelineArchitecture(
                    definition,
                    tracking,
                    generation_config,
                ).run(case.question, research, on_step=on_step)

                status, error = "completed", None
            except (QuotaExhaustedError, CacheMissError):
                raise
            except Exception as exc:
                answer, steps = "", []
                status, error = "failed", f"{type(exc).__name__}: {exc}"

            metrics = tracking.metrics

            return ArchitectureOutcome(
                architecture=name,
                agent_count=definition.agent_count,
                status=status,
                error=error,
                answer=answer,
                steps=steps,
                model=manifest.generator_model,
                call_count=metrics.call_count,
                input_tokens=metrics.total_input_tokens,
                output_tokens=metrics.total_output_tokens,
                thinking_tokens=metrics.total_thinking_tokens,
                total_tokens=metrics.total_tokens,
                latency_ms=metrics.total_latency_ms,
                retries=metrics.total_retries,
                estimated_cost_usd=metrics.estimated_cost_usd,
            )

        # Architectures run concurrently: each pipeline is still strictly
        # sequential inside, and the shared rate limiter caps requests
        # per minute. On the free tier, calls take 20-40 s each, so this
        # makes a full run roughly 3x faster.
        outcomes = _parallel(run_architecture, manifest.architectures)

        rubric_judge = LLMJudge(judge, judge_config)

        def judge_outcome(outcome: ArchitectureOutcome) -> None:
            if outcome.status != "completed":
                return

            outcome.deterministic = compute_metrics(
                outcome.answer,
                source_count=len(research.results),
            )

            try:
                outcome.evaluation = rubric_judge.evaluate(
                    case,
                    outcome.answer,
                    research,
                )
            except (QuotaExhaustedError, CacheMissError):
                raise
            except Exception as exc:
                outcome.judge_error = f"{type(exc).__name__}: {exc}"

            tick(
                f"Judge scored {outcome.architecture}",
                case_id=case.case_id,
                trial=item.trial,
                architecture=outcome.architecture,
            )

        _parallel(judge_outcome, outcomes)

        result = CaseTrialResult(
            run_id=manifest.run_id,
            case_id=case.case_id,
            trial=item.trial,
            difficulty=case.difficulty,
            category=case.category,
            question=case.question,
            outcomes=outcomes,
            completed_at=utc_now(),
        )

        answers = {
            outcome.architecture: outcome.answer
            for outcome in outcomes
            if outcome.status == "completed"
        }

        if len(manifest.architectures) > 1 and len(answers) > 1:
            try:
                result.ranking = RankingJudge(judge, judge_config).rank(
                    case,
                    item.trial,
                    answers,
                    research,
                )
            except (QuotaExhaustedError, CacheMissError):
                raise
            except Exception as exc:
                result.ranking_error = f"{type(exc).__name__}: {exc}"

            tick(
                "Blind ranking completed",
                case_id=case.case_id,
                trial=item.trial,
            )

        # A unit only counts when every architecture answered and every
        # answer was judged. Otherwise fail it, so resuming retries it
        # (finished calls come from the cache) instead of letting gaps
        # into the statistics.
        problems = [
            f"{outcome.architecture}: {outcome.error or outcome.judge_error}"
            for outcome in outcomes
            if outcome.status != "completed" or outcome.judge_error
        ]

        if result.ranking_error:
            problems.append(f"ranking: {result.ranking_error}")

        if problems:
            raise RuntimeError("; ".join(problems))

        return result
