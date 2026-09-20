from collections.abc import Callable

from agent_lab.evaluation.base import Evaluator
from agent_lab.evaluation.evaluated_result import (
    EvaluatedArchitectureResult,
)
from agent_lab.evaluation.experiment_result import (
    EvaluatedExperimentResult,
)
from agent_lab.experiments.case import ExperimentCase
from agent_lab.experiments.result import ExperimentResult


ProgressCallback = Callable[[dict], None]


class EvaluationRunner:
    def __init__(
        self,
        evaluator: Evaluator,
    ):
        self.evaluator = evaluator

    def evaluate_experiment(
        self,
        case: ExperimentCase,
        experiment: ExperimentResult,
        progress_callback: ProgressCallback | None = None,
    ) -> EvaluatedExperimentResult:

        evaluated_results = []

        total = len(
            experiment.results
        )

        for index, result in enumerate(
            experiment.results,
            start=1,
        ):

            if progress_callback:
                progress_callback(
                    {
                        "stage": "evaluation_started",
                        "architecture": (
                            result.architecture_name
                        ),
                        "result_index": index,
                        "result_total": total,
                    }
                )

            evaluation = self.evaluator.evaluate(
                case=case,
                result=result,
                research=experiment.research,
            )

            evaluated_results.append(
                EvaluatedArchitectureResult(
                    architecture=result,
                    evaluation=evaluation,
                )
            )

            if progress_callback:
                progress_callback(
                    {
                        "stage": "evaluation_completed",
                        "architecture": (
                            result.architecture_name
                        ),
                        "result_index": index,
                        "result_total": total,
                    }
                )

        return EvaluatedExperimentResult(
            case_id=experiment.case_id,
            question=experiment.question,
            results=evaluated_results,
        )