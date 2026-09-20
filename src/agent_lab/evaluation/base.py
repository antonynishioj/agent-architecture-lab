from abc import ABC, abstractmethod

from agent_lab.evaluation.result import EvaluationResult
from agent_lab.experiments.case import ExperimentCase
from agent_lab.experiments.result import ArchitectureResult
from agent_lab.research.result import ResearchBundle


class Evaluator(ABC):
    @abstractmethod
    def evaluate(
        self,
        case: ExperimentCase,
        result: ArchitectureResult,
        research: ResearchBundle,
    ) -> EvaluationResult:
        pass