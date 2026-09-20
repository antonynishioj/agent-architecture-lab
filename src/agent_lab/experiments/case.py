from pydantic import BaseModel
from agent_lab.research.result import ResearchBundle


class ExperimentCase(BaseModel):
    case_id: str
    question: str
    reference_answer: str
    research: ResearchBundle | None = None