from agent_lab.llm.base import LLM, LLMResponse
from agent_lab.research.result import ResearchBundle


class ResearchFactChecker:
    def __init__(self, llm: LLM):
        self.llm = llm

    def run(
        self,
        question: str,
        research: ResearchBundle,
    ) -> LLMResponse:
        sources = "\n\n".join(
            f"Source {index}:\n"
            f"Title: {result.title}\n"
            f"URL: {result.url}\n"
            f"Content: {result.content}"
            for index, result in enumerate(research.results, start=1)
        )

        prompt = f"""
You are the Research and Fact-Checking Agent in a two-agent
research system.

Your responsibilities are ONLY:

1. Analyze the original question and identify the information needed.
2. Research the question using ONLY the provided research sources.
3. Extract the relevant factual information from those sources.
4. Check important claims against the provided sources.
5. Distinguish supported facts from uncertain, unsupported,
   or conflicting claims.
6. Identify important information gaps or limitations in the
   available sources.
7. Produce a structured research and fact-checking brief for
   the next agent.

Do NOT write the final user-facing answer.
Do NOT perform the critic's responsibility of evaluating the overall
reasoning or argument.
Do NOT focus on presentation or writing style.

Original question:
{question}

Provided research sources:
{sources}

Use the provided sources as the evidence for your research
and fact-checking.

Important evidence rule:

Use the provided research sources as the only evidence for factual
claims about the subject.

Do not introduce factual information from your pretrained knowledge
that is not supported by the provided research.

You may make reasonable conclusions or inferences that directly follow
from the provided evidence.

If the provided research does not contain enough information to support
a factual claim, identify that information as uncertain, unsupported,
or unavailable from the provided research.

Do not add outside facts, examples, technical concepts, statistics,
mechanisms, or terminology merely because they are generally known.

When the sources disagree or contain different levels of support,
explicitly identify the disagreement rather than silently choosing
one position.

Return a structured research and fact-checking brief.
"""

        return self.llm.generate(prompt)