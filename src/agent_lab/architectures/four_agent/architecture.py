from agent_lab.llm.base import LLM, LLMResponse
from agent_lab.research.result import ResearchBundle

from agent_lab.architectures.four_agent.researcher import (
    FourAgentResearcher,
)
from agent_lab.architectures.four_agent.fact_checker import (
    FourAgentFactChecker,
)
from agent_lab.architectures.four_agent.critic import (
    FourAgentCritic,
)
from agent_lab.architectures.four_agent.writer import (
    FourAgentWriter,
)


class FourAgentArchitecture:

    def __init__(self, llm: LLM):
        self.researcher = FourAgentResearcher(llm)
        self.fact_checker = FourAgentFactChecker(llm)
        self.critic = FourAgentCritic(llm)
        self.writer = FourAgentWriter(llm)

    def run(
        self,
        question: str,
        research: ResearchBundle,
    ) -> LLMResponse:

        research_result = self.researcher.run(
            question,
            research,
        )

        fact_check_result = self.fact_checker.run(
            question,
            research_result.text,
        )

        critique_result = self.critic.run(
            question,
            fact_check_result.text,
        )

        final_result = self.writer.run(
            question,
            fact_check_result.text,
            critique_result.text,
        )

        return final_result