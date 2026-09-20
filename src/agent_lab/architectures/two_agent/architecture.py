from agent_lab.llm.base import LLM, LLMResponse
from agent_lab.research.result import ResearchBundle

from agent_lab.architectures.two_agent.research_fact_checker import (
    ResearchFactChecker,
)
from agent_lab.architectures.two_agent.critic_writer import (
    CriticWriter,
)


class TwoAgentArchitecture:

    def __init__(self, llm: LLM):
        self.research_fact_checker = ResearchFactChecker(llm)
        self.critic_writer = CriticWriter(llm)

    def run(
        self,
        question: str,
        research: ResearchBundle,
    ) -> LLMResponse:

        research_result = self.research_fact_checker.run(
            question,
            research,
        )

        final_result = self.critic_writer.run(
            question,
            research_result.text,
        )

        return final_result