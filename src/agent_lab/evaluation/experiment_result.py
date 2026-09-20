from pydantic import BaseModel

from agent_lab.evaluation.evaluated_result import EvaluatedArchitectureResult


class EvaluatedExperimentResult(BaseModel):
    case_id: str
    question: str
    results: list[EvaluatedArchitectureResult]