from agent_lab.llm.base import LLM, LLMResponse


class OneAgent:
    """
    Baseline architecture where a single agent handles
    research, fact-checking, criticism, and writing.
    """

    def __init__(self, llm: LLM):
        self.llm = llm

    def run(self, question: str) -> LLMResponse:
        prompt = f"""
You are a research assistant.

For the following question, perform all of these responsibilities:

1. Research the topic.
2. Check the factual accuracy of the information.
3. Critically review the reasoning and identify possible weaknesses.
4. Write a clear and concise final answer.

Question:
{question}

Return only the final answer.
"""

        return self.llm.generate(prompt)