from collections.abc import Callable
from uuid import uuid4

from agent_lab.evaluation.llm_judge import LLMJudge
from agent_lab.evaluation.runner import EvaluationRunner
from agent_lab.experiments.case import ExperimentCase
from agent_lab.experiments.registry import RunRegistry
from agent_lab.experiments.report import ExperimentReport
from agent_lab.experiments.runner import ExperimentRunner
from agent_lab.llm.base import LLM
from agent_lab.llm.pricing import PricingRegistry
from agent_lab.research.base import ResearchTool


ProgressCallback = Callable[[dict], None]


class ExperimentService:
    def __init__(
        self,
        generator_llm: LLM,
        judge_llm: LLM,
        research_tool: ResearchTool,
        pricing_registry: PricingRegistry | None = None,
        results_directory: str = "data/results",
    ):
        self.experiment_runner = ExperimentRunner(
            llm=generator_llm,
            research_tool=research_tool,
            pricing_registry=pricing_registry,
        )

        self.evaluation_runner = EvaluationRunner(
            LLMJudge(judge_llm)
        )

        self.results_directory = results_directory

        self.registry = RunRegistry(
            directory=f"{results_directory}/runs"
        )

    def _emit(
        self,
        callback: ProgressCallback | None,
        **event,
    ) -> None:
        if callback:
            callback(event)

    def run_case(
        self,
        case: ExperimentCase,
        run_id: str,
        progress_callback: ProgressCallback | None = None,
        case_index: int = 1,
        case_total: int = 1,
    ) -> ExperimentReport:

        def case_progress(event: dict) -> None:
            """
            Convert case-local progress into benchmark-global progress.
            """

            stage = event.get("stage")

            if stage == "research_started":
                local_progress = 5

            elif stage in {
                "research_loaded",
                "research_completed",
            }:
                local_progress = 10

            elif stage == "architecture_started":
                architecture_index = event.get(
                    "architecture_index",
                    1,
                )

                local_progress = (
                    10
                    + (
                        (architecture_index - 1)
                        * 15
                    )
                )

            elif stage == "architecture_completed":
                architecture_index = event.get(
                    "architecture_index",
                    1,
                )

                local_progress = (
                    10
                    + (
                        architecture_index
                        * 15
                    )
                )

            elif stage == "evaluation_started":
                local_progress = 80

            elif stage == "evaluation_completed":
                result_index = event.get(
                    "result_index",
                    1,
                )

                local_progress = min(
                    80 + (result_index * 5),
                    99,
                )

            elif stage == "case_completed":
                local_progress = 100

            else:
                local_progress = 0

            global_progress = int(
                (
                    (case_index - 1)
                    + (local_progress / 100)
                )
                / case_total
                * 100
            )

            self._emit(
                progress_callback,
                **event,
                case_index=case_index,
                case_total=case_total,
                case_progress=local_progress,
                progress=global_progress,
            )

        self._emit(
            progress_callback,
            stage="case_started",
            case_id=case.case_id,
            case_index=case_index,
            case_total=case_total,
            progress=int(
                ((case_index - 1) / case_total)
                * 100
            ),
        )

        experiment = self.experiment_runner.run_case(
            case=case,
            progress_callback=case_progress,
        )

        evaluation = self.evaluation_runner.evaluate_experiment(
            case=case,
            experiment=experiment,
            progress_callback=case_progress,
        )

        report = ExperimentReport(
            run_id=run_id,
            experiment=experiment,
            evaluation=evaluation,
        )

        result_file = report.save(
            directory=f"{self.results_directory}/cases"
        )

        self.registry.update_case(
            run_id=run_id,
            case_id=case.case_id,
            status="completed",
            result_file=str(result_file),
        )

        self._emit(
            progress_callback,
            stage="case_completed",
            case_id=case.case_id,
            case_index=case_index,
            case_total=case_total,
            case_progress=100,
            progress=int(
                case_index
                / case_total
                * 100
            ),
            result_file=str(result_file),
        )

        return report

    def create_benchmark_run(
        self,
        cases: list[ExperimentCase],
    ):
        run_id = uuid4().hex[:12]

        return self.registry.create(
            run_id=run_id,
            run_type="benchmark",
            case_ids=[
                case.case_id
                for case in cases
            ],
        )

    def create_custom_run(
        self,
        question: str,
        reference_answer: str,
        category: str,
        difficulty: str,
    ):
        run_id = uuid4().hex[:12]

        case = ExperimentCase(
            case_id=f"custom-{run_id}",
            question=question,
            reference_answer=reference_answer,
            category=category,
            difficulty=difficulty,
        )

        run = self.registry.create(
            run_id=run_id,
            run_type="custom",
            case_ids=[case.case_id],
        )

        return run, case

    def run_benchmark(
        self,
        cases: list[ExperimentCase],
        run_id: str,
        progress_callback: ProgressCallback | None = None,
    ):
        self.registry.update_status(
            run_id,
            "running",
        )

        total_cases = len(cases)

        for case_index, case in enumerate(
            cases,
            start=1,
        ):
            current = self.registry.load(
                run_id
            )

            if current is None:
                raise RuntimeError(
                    f"Run not found: {run_id}"
                )

            case_state = next(
                (
                    item
                    for item in current.cases
                    if item.case_id == case.case_id
                ),
                None,
            )

            if (
                case_state
                and case_state.status == "completed"
            ):
                continue

            self.registry.update_case(
                run_id=run_id,
                case_id=case.case_id,
                status="running",
            )

            try:
                self.run_case(
                    case=case,
                    run_id=run_id,
                    progress_callback=progress_callback,
                    case_index=case_index,
                    case_total=total_cases,
                )

            except Exception as exc:
                self.registry.update_case(
                    run_id=run_id,
                    case_id=case.case_id,
                    status="failed",
                    error=str(exc),
                )

                self._emit(
                    progress_callback,
                    stage="case_failed",
                    case_id=case.case_id,
                    case_index=case_index,
                    case_total=total_cases,
                    error=str(exc),
                    progress=int(
                        case_index
                        / total_cases
                        * 100
                    ),
                )

                continue

        final_run = self.registry.load(
            run_id
        )

        if final_run is None:
            raise RuntimeError(
                f"Run not found after execution: {run_id}"
            )

        if (
            final_run.completed_cases
            + final_run.failed_cases
            == final_run.total_cases
        ):
            self.registry.update_status(
                run_id,
                (
                    "completed_with_errors"
                    if final_run.failed_cases
                    else "completed"
                ),
            )

        return self.registry.load(
            run_id
        )

    def run_custom(
        self,
        case: ExperimentCase,
        run_id: str,
        progress_callback: ProgressCallback | None = None,
    ):
        self.registry.update_status(
            run_id,
            "running",
        )

        self.registry.update_case(
            run_id=run_id,
            case_id=case.case_id,
            status="running",
        )

        try:
            self.run_case(
                case=case,
                run_id=run_id,
                progress_callback=progress_callback,
                case_index=1,
                case_total=1,
            )

            self.registry.update_status(
                run_id,
                "completed",
            )

        except Exception as exc:
            self.registry.update_case(
                run_id=run_id,
                case_id=case.case_id,
                status="failed",
                error=str(exc),
            )

            self.registry.update_status(
                run_id,
                "failed",
            )

            self._emit(
                progress_callback,
                stage="case_failed",
                case_id=case.case_id,
                case_index=1,
                case_total=1,
                error=str(exc),
                progress=100,
            )

            raise

        return self.registry.load(
            run_id
        )