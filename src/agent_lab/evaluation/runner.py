from agent_lab.evaluation.base import Evaluator
from agent_lab.evaluation.evaluated_result import (
    EvaluatedArchitectureResult,
)
from agent_lab.evaluation.experiment_result import (
    EvaluatedExperimentResult,
)
from agent_lab.experiments.case import ExperimentCase
from agent_lab.experiments.experiment import ExperimentResult
from agent_lab.experiments.result import ArchitectureResult
from agent_lab.research.result import ResearchBundle


class EvaluationRunner:

    def __init__(self, evaluator: Evaluator):
        self.evaluator = evaluator

    def evaluate(
        self,
        case: ExperimentCase,
        result: ArchitectureResult,
        research: ResearchBundle,
    ) -> EvaluatedArchitectureResult:

        evaluation = self.evaluator.evaluate(
            case=case,
            result=result,
            research=research,
        )

        return EvaluatedArchitectureResult(
            architecture=result,
            evaluation=evaluation,
        )

    def evaluate_experiment(
        self,
        case: ExperimentCase,
        experiment: ExperimentResult,
    ) -> EvaluatedExperimentResult:

        evaluated_results = [
            self.evaluate(
                case=case,
                result=result,
                research=experiment.research,
            )
            for result in experiment.results
        ]

        return EvaluatedExperimentResult(
            case_id=experiment.case_id,
            question=experiment.question,
            results=evaluated_results,
        )