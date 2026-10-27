from pydantic import BaseModel, Field

from agent_lab.research.result import ResearchBundle


DIFFICULTIES = ("easy", "medium", "hard", "adversarial", "custom")


class ExperimentCase(BaseModel):
    case_id: str
    question: str
    reference_answer: str | None = None

    category: str = "Custom"
    difficulty: str = "custom"

    # What a complete answer must contain. The judge marks each point
    # covered / partial / missing, which makes completeness measurable.
    key_points: list[str] = Field(default_factory=list)

    # Tempting but wrong or unsupported claims planted in the case.
    # Repeating one of these is a "trap violation".
    must_not_claim: list[str] = Field(default_factory=list)

    # Why the case is hard. Shown in the UI and the docs, never to agents.
    design_notes: str = ""

    source_kind: str = "curated"

    research: ResearchBundle | None = None
