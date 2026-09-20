from pydantic import BaseModel

from agent_lab.evaluation.result import EvaluationResult
from agent_lab.experiments.result import ArchitectureResult


class EvaluatedArchitectureResult(BaseModel):
    architecture: ArchitectureResult
    evaluation: EvaluationResult