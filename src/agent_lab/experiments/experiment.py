from pydantic import BaseModel

from agent_lab.experiments.result import ArchitectureResult
from agent_lab.research.result import ResearchBundle


class ExperimentResult(BaseModel):
    case_id: str
    question: str
    research: ResearchBundle
    results: list[ArchitectureResult]