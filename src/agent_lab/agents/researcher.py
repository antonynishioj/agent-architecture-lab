from agent_lab.llm.base import LLM, LLMResponse


class ResearchAgent:
    """Agent responsible for researching a question."""

    def __init__(self, llm: LLM):
        self.llm = llm

    def run(self, question: str) -> LLMResponse:
        prompt = f"""
You are a research agent.

Research the following question and provide a factual,
well-structured research response.

Question:
{question}
"""

        return self.llm.generate(prompt)