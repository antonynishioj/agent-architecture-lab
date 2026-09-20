import json

from agent_lab.evaluation.result import EvaluationResult
from agent_lab.experiments.case import ExperimentCase
from agent_lab.experiments.result import ArchitectureResult
from agent_lab.llm.base import LLM
from agent_lab.research.result import ResearchBundle


class LLMJudge:
    def __init__(self, llm: LLM):
        self.llm = llm

    def evaluate(
        self,
        case: ExperimentCase,
        result: ArchitectureResult,
        research: ResearchBundle,
    ) -> EvaluationResult:

        sources = "\n\n".join(
            f"Source {index}:\n"
            f"Title: {source.title}\n"
            f"URL: {source.url}\n"
            f"Content: {source.content}"
            for index, source in enumerate(research.results, start=1)
        )

        prompt = f"""
You are an impartial evaluator of an AI-generated research answer.

Evaluate the candidate answer using:

1. The original question.
2. The reference answer.
3. The frozen research sources.

Do not compare the candidate answer with answers from other systems.

Original question:
{case.question}

Reference answer:
{case.reference_answer}

Frozen research sources:
{sources}

Candidate answer:
{result.answer}

Evaluate these dimensions independently:

1. Answer Relevancy

Did the candidate directly address the original question?

2. Completeness

Did the candidate cover the important information required
to answer the question?

3. Faithfulness

Are the factual claims in the candidate answer supported by
the provided research sources?

A candidate should receive a lower faithfulness score if it:

- makes claims unsupported by the sources,
- contradicts the sources,
- exaggerates what the sources establish,
- introduces outside factual information,
- or invents information.

4. Overall Quality

Consider:

- factual correctness,
- answer relevancy,
- completeness,
- faithfulness to the evidence,
- clarity,
- coherence,
- usefulness,
- reasoning quality,
- and appropriate handling of uncertainty.

Scoring:

For every evaluation dimension, assign a continuous score
from 0.0 to 1.0.

Do NOT restrict scores to 0.0, 0.5, or 1.0.

Scores such as 0.63, 0.71, 0.84, 0.91, and 0.97 are valid.

Use the full range of the scale when appropriate.

Do not automatically round scores to convenient values.

Answer Relevancy:

- 0.00–0.20: Does not meaningfully address the question.
- 0.21–0.40: Addresses only a small part of the question.
- 0.41–0.60: Partially addresses the question but misses important aspects.
- 0.61–0.80: Directly addresses the question but has some omissions or irrelevant content.
- 0.81–0.95: Highly relevant with only minor issues.
- 0.96–1.00: Exceptionally precise and directly addresses the question with no meaningful relevance problems.

Completeness:

- 0.00–0.20: Almost all important information is missing.
- 0.21–0.40: Covers only a small portion of the required information.
- 0.41–0.60: Covers the main idea but misses several important points.
- 0.61–0.80: Covers most important points but has noticeable omissions.
- 0.81–0.95: Covers nearly all important information with only minor omissions.
- 0.96–1.00: Exceptionally complete with no meaningful omissions.

Faithfulness:

- 0.00–0.20: Contains major unsupported or contradictory claims.
- 0.21–0.40: Contains several significant unsupported or contradictory claims.
- 0.41–0.60: Some claims are supported, but important claims are unsupported or uncertain.
- 0.61–0.80: Mostly supported, with some unsupported or weakly supported claims.
- 0.81–0.95: Almost entirely supported by the provided evidence.
- 0.96–1.00: Claims are exceptionally well supported and do not exceed what the evidence establishes.

Overall Quality:

Consider factual correctness, clarity, coherence, usefulness,
relevance, completeness, evidence support, and reasoning quality.

Use a continuous score from 0.0 to 1.0.

A score of 1.0 is rare.

Use 1.00 only when the candidate fully satisfies the evaluation
dimension without any meaningful deficiency.

A score between 0.90 and 0.99 should be used when the answer
is excellent but contains a minor imperfection.

Do not give a high score merely because the answer is generally
correct or well-written.

Consider:

- important omissions,
- unsupported claims,
- contradictions,
- weak reasoning,
- unnecessary information,
- lack of precision,
- failure to acknowledge uncertainty,
- and claims that go beyond what the sources establish.

Score calibration:

When deciding between two possible scores, choose the lower
score unless the evidence clearly supports the higher score.

Do not inflate scores simply because the answer sounds confident,
professional, detailed, or well-written.

Evidence boundary:

Evaluate faithfulness against the frozen research sources.

A candidate should not receive full faithfulness merely because
an unsupported claim is generally true according to your own
knowledge.

If a factual claim is not supported by the provided research,
treat it as unsupported for this evaluation, even if the claim
may be true in the real world.

Reasonable conclusions that directly follow from the provided
evidence may be accepted as supported.

Do not use outside knowledge to validate unsupported claims.

For example, if the candidate introduces a technical concept
that is not present in the research sources, do not consider
that claim supported merely because the concept is generally
known to be true.

Important evaluation rule:

Evaluate each candidate independently.

Do not rank candidates against each other.

Do not compare the candidate answer with answers from other
architectures.

Do not use the architecture name to influence your evaluation.

The candidate should receive the same evaluation standard
regardless of which architecture produced it.

Reasoning requirement:

Before assigning the scores, identify the specific strengths
and weaknesses of the candidate answer.

The reasoning must explain why the assigned scores are appropriate.

Mention concrete evidence such as:

- important information that was included,
- important information that was omitted,
- claims that are supported by the sources,
- claims that are unsupported,
- claims that contradict the sources,
- reasoning weaknesses,
- ambiguity,
- unnecessary content,
- or unsupported external knowledge.

Do not make generic statements such as:
"The answer is good and well-written"
without explaining what specifically makes it good.

Do not compare the candidate with any other architecture.

Return ONLY a JSON object.

Do not use Markdown.
Do not include ```json.
Do not include any explanation outside the JSON.

Required JSON structure:

{{
    "answer_relevancy": 0.0,
    "completeness": 0.0,
    "faithfulness": 0.0,
    "overall_quality": 0.0,
    "reasoning": "Brief evidence-based explanation of the strengths and weaknesses that justify the scores."
}}
"""

        response = self.llm.generate(prompt)

        raw_text = response.text.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            if raw_text.startswith("json"):
                raw_text = raw_text[4:].strip()

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            start = raw_text.find("{")
            end = raw_text.rfind("}")

            if start == -1 or end == -1:
                raise ValueError(
                    f"Judge did not return valid JSON:\n{raw_text}"
                )

            data = json.loads(raw_text[start : end + 1])

        return EvaluationResult.model_validate(data)