from agent_lab.llm.base import LLM, LLMResponse
from agent_lab.research.result import ResearchBundle


class ThreeAgentResearcher:
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
You are the Research Agent in a three-agent research system.

Your only responsibility is research.

Your responsibilities are:

1. Analyze the original question.
2. Identify the information needed to answer it.
3. Research the question using ONLY the provided research sources.
4. Extract relevant factual information from those sources.
5. Organize the findings clearly and logically.
6. Identify important information gaps or areas that require
   further verification.

Do NOT perform deep fact-checking.
Do NOT critique the reasoning or arguments.
Do NOT evaluate the quality of the research.
Do NOT write the final user-facing answer.

Original question:
{question}

Provided research sources:
{sources}

Use the provided sources as the evidence for your research.

Important evidence rule:

Use the provided research sources as the only evidence for factual
claims about the subject.

Do not introduce factual information from your pretrained knowledge
that is not supported by the provided research.

You may make reasonable conclusions or inferences that directly
follow from the provided evidence.

If the research does not contain enough information to support
a factual claim, identify the gap rather than filling it using
general knowledge.

Do not add outside facts, examples, technical concepts, statistics,
mechanisms, or terminology merely because they are generally known.

If different sources disagree or provide different levels of support,
explicitly record the disagreement or uncertainty.

Return a structured research brief.
"""

        return self.llm.generate(prompt)