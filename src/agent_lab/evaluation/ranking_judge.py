import random
import string

from agent_lab.evaluation.json_utils import parse_json_object
from agent_lab.evaluation.result import RankingResult
from agent_lab.experiments.case import ExperimentCase
from agent_lab.llm.base import GenerationConfig, LLM
from agent_lab.research.result import ResearchBundle


RANKING_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "ranking": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["reasoning", "ranking"],
}


class RankingJudge:
    """
    Ranks all answers for a case side by side.

    Answers are shuffled with a seed derived from the case and trial,
    so the judge cannot learn a position or label for an architecture,
    and the shuffle is reproducible.
    """

    def __init__(self, llm: LLM, config: GenerationConfig):
        self.llm = llm
        self.config = config.model_copy(
            update={"json_schema": RANKING_SCHEMA}
        )

    @staticmethod
    def assign_labels(
        architecture_names: list[str],
        case_id: str,
        trial: int,
    ) -> dict[str, str]:
        shuffled = list(architecture_names)
        random.Random(f"{case_id}:{trial}").shuffle(shuffled)

        return {
            string.ascii_uppercase[index]: name
            for index, name in enumerate(shuffled)
        }

    def rank(
        self,
        case: ExperimentCase,
        trial: int,
        answers: dict[str, str],
        research: ResearchBundle,
    ) -> RankingResult:
        labels = self.assign_labels(
            sorted(answers),
            case.case_id,
            trial,
        )

        candidates = "\n\n".join(
            f"=== Answer {label} ===\n{answers[name]}"
            for label, name in labels.items()
        )

        letters = ", ".join(labels)

        prompt = f"""You are an impartial expert comparing {len(labels)} answers to the same research question.

Rank the answers from best to worst. The sources are the ONLY evidence that
counts. Prefer answers that are correct and faithful to the sources, complete,
honest about uncertainty, conflicts, and false premises, and well cited.
Do not reward length or style for its own sake. Ignore the order in which
answers are presented.

Question:
{case.question}

Sources:
{research.format_sources()}

{candidates}

Return JSON with:
- "reasoning": a brief comparison of the decisive differences,
- "ranking": all labels ({letters}) ordered best to worst, each exactly once."""

        response = self.llm.generate(prompt, self.config)
        data = parse_json_object(response.text)

        ranking = [
            str(label).strip().upper().removeprefix("ANSWER ").strip()
            for label in data.get("ranking", [])
        ]

        if sorted(ranking) != sorted(labels):
            raise ValueError(
                f"Ranking judge returned an invalid ranking: {ranking}"
            )

        return RankingResult(
            order=[labels[label] for label in ranking],
            labels=labels,
            reasoning=str(data.get("reasoning", "")),
        )
