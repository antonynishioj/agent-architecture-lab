from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    answer_relevancy: float = Field(ge=0, le=1)
    completeness: float = Field(ge=0, le=1)
    faithfulness: float = Field(ge=0, le=1)
    overall_quality: float = Field(ge=0, le=1)
    reasoning: str = ""