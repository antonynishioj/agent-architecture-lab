from agent_lab.llm.base import LLM, LLMResponse


class OneAgent:
    """
    Independent 1-agent architecture.

    This agent performs research, fact checking,
    criticism, and final writing itself.
    """

    def __init__(self, llm: LLM):
        self.llm = llm

    def run(self, question: str) -> LLMResponse:
        prompt = f"""
You are the only agent responsible for answering a research question.

You must perform all of the following internally:

1. Research the question.
2. Identify relevant factual information.
3. Check the factual reliability of the information.
4. Critically examine the reasoning and identify weaknesses.
5. Produce a clear final answer.

You must perform all responsibilities yourself.
Do not delegate any responsibility to another agent.

Question:
{question}

Return only the final answer.
"""

        return self.llm.generate(prompt)