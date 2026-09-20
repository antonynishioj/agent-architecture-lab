from agent_lab.llm.base import LLM, LLMResponse
from agent_lab.research.result import ResearchBundle


class OneAgent:
    def __init__(self, llm: LLM):
        self.llm = llm

    def run(self, question: str, research: ResearchBundle) -> LLMResponse:
        sources = "\n\n".join(
            f"Source {index}:\n"
            f"Title: {result.title}\n"
            f"URL: {result.url}\n"
            f"Content: {result.content}"
            for index, result in enumerate(research.results, start=1)
        )

        prompt = f"""
You are the only agent responsible for answering a research question.

You must perform all of the following yourself:

1. Research using the provided sources.
2. Identify relevant factual information.
3. Fact-check the information against the provided sources.
4. Critically examine the reasoning and identify weaknesses.
5. Produce a clear final answer.

You must perform all responsibilities yourself.
Do not delegate any responsibility to another agent.

Original question:
{question}

Provided research sources:
{sources}

Use the provided sources as your research evidence.

Important evidence rule:

Use the provided research sources as the only evidence for factual
claims about the subject.

Do not introduce factual information from your pretrained knowledge
that is not supported by the provided research.

You may make reasonable conclusions or inferences that directly follow
from the provided evidence.

If the provided research does not contain enough information to support
a factual claim, do not fill the gap using general knowledge.

Instead, explicitly identify the information as uncertain, unsupported,
or unavailable from the provided research.

Do not introduce additional facts, examples, technical concepts,
statistics, mechanisms, or terminology unless they are supported by
the provided research or are a reasonable conclusion directly derived
from it.

Return only the final answer.
"""

        return self.llm.generate(prompt)