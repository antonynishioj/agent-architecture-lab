from agent_lab.evaluation.json_utils import parse_json_object
from agent_lab.evaluation.result import EvaluationResult, KeyPointVerdict
from agent_lab.experiments.case import ExperimentCase
from agent_lab.llm.base import GenerationConfig, LLM
from agent_lab.research.result import ResearchBundle


SCORE = {"type": "number", "minimum": 0, "maximum": 1}

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "key_points": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "point": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["covered", "partial", "missing"],
                    },
                },
                "required": ["point", "status"],
            },
        },
        "unsupported_claims": {
            "type": "array",
            "items": {"type": "string"},
        },
        "trap_violations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "reasoning": {"type": "string"},
        "answer_relevancy": SCORE,
        "completeness": SCORE,
        "faithfulness": SCORE,
        "citation_quality": SCORE,
        "uncertainty_handling": SCORE,
        "overall_quality": SCORE,
    },
    "required": [
        "key_points",
        "unsupported_claims",
        "trap_violations",
        "reasoning",
        "answer_relevancy",
        "completeness",
        "faithfulness",
        "citation_quality",
        "uncertainty_handling",
        "overall_quality",
    ],
}

KEY_POINT_WEIGHTS = {"covered": 1.0, "partial": 0.5, "missing": 0.0}


def _bullets(items: list[str], empty: str) -> str:
    if not items:
        return empty

    return "\n".join(f"- {item}" for item in items)


class LLMJudge:
    """
    Scores one answer on an absolute rubric.

    The judge never sees which architecture produced the answer.
    """

    def __init__(self, llm: LLM, config: GenerationConfig):
        self.llm = llm
        self.config = config.model_copy(
            update={"json_schema": JUDGE_SCHEMA}
        )

    def build_prompt(
        self,
        case: ExperimentCase,
        answer: str,
        research: ResearchBundle,
    ) -> str:
        reference = case.reference_answer or (
            "(No reference answer was provided. Judge against the "
            "question and the sources.)"
        )

        key_points = _bullets(
            case.key_points,
            "(No key points were provided. Identify the 3-6 points a "
            "complete answer must contain, based on the question and "
            "the sources, and evaluate those.)",
        )

        traps = _bullets(
            case.must_not_claim,
            "(None specified. Still report any claim that the sources "
            "contradict or do not support.)",
        )

        return f"""You are an impartial, strict evaluator of an AI-generated research answer.

Evaluate the candidate answer against the question, the reference answer,
the key points, and the sources. The sources are the ONLY evidence that
counts. A claim that is true in the real world but absent from the sources
is UNSUPPORTED for this evaluation.

Question:
{case.question}

Reference answer:
{reference}

Key points a complete answer must contain:
{key_points}

Trap claims (claims the answer must NOT make, because the sources contradict
them or do not support them):
{traps}

Sources (cited by the candidate as [S1], [S2], ...):
{research.format_sources()}

Candidate answer:
<<<
{answer}
>>>

Procedure:
1. key_points: for each key point, mark "covered", "partial", or "missing".
2. unsupported_claims: list every factual claim in the candidate that the
   sources do not support or that contradicts them (short paraphrases).
3. trap_violations: list every trap claim the candidate makes or implies.
4. reasoning: a short, concrete explanation of strengths and weaknesses.
5. Then score each dimension from 0.0 to 1.0. Use the full continuous range
   (for example 0.63 or 0.87). Do not round to 0.5 or 1.0 for convenience.

Dimensions:
- answer_relevancy: does it directly answer what was asked, without padding?
- completeness: how much of the required information is present?
- faithfulness: are the claims supported by the sources? Deduct for each
  unsupported claim, contradiction, exaggeration, or use of outside knowledge.
- citation_quality: are claims cited, and does each cited source actually
  support the claim it is attached to? No citations means a score near 0.
- uncertainty_handling: does it surface conflicts, outdated information,
  missing evidence, and false premises honestly, without being needlessly
  vague when the evidence is clear? Any trap violation caps this at 0.4.
- overall_quality: overall usefulness and trustworthiness to a careful reader.

Calibration:
- 0.96-1.00 means no meaningful flaw. This is rare.
- 0.81-0.95 means excellent with minor issues.
- 0.61-0.80 means good but with noticeable problems.
- 0.41-0.60 means important problems.
- Below 0.40 means seriously flawed.
- When unsure between two scores, choose the lower one.
- Do not reward length, confidence, or polish for their own sake.

Return only the JSON object."""

    def evaluate(
        self,
        case: ExperimentCase,
        answer: str,
        research: ResearchBundle,
    ) -> EvaluationResult:
        response = self.llm.generate(
            self.build_prompt(case, answer, research),
            self.config,
        )

        data = parse_json_object(response.text)

        for field in (
            "answer_relevancy",
            "completeness",
            "faithfulness",
            "citation_quality",
            "uncertainty_handling",
            "overall_quality",
        ):
            data[field] = min(1.0, max(0.0, float(data.get(field, 0))))

        verdicts = [
            KeyPointVerdict(
                point=str(item.get("point", "")),
                status=str(item.get("status", "missing")).lower(),
            )
            for item in data.get("key_points", [])
            if isinstance(item, dict)
        ]

        data["judge_completeness"] = data["completeness"]

        # With explicit key points, completeness is calculated from the
        # checklist instead of trusting a holistic number.
        if case.key_points and verdicts:
            data["completeness"] = sum(
                KEY_POINT_WEIGHTS.get(verdict.status, 0.0)
                for verdict in verdicts
            ) / len(verdicts)

        data["key_points"] = verdicts

        return EvaluationResult.model_validate(data)
