from agent_lab.llm.base import LLM, LLMResponse
from agent_lab.research.result import ResearchBundle

from agent_lab.architectures.three_agent.researcher import (
    ThreeAgentResearcher,
)
from agent_lab.architectures.three_agent.fact_checker_critic import (
    ThreeAgentFactCheckerCritic,
)
from agent_lab.architectures.three_agent.writer import (
    ThreeAgentWriter,
)


class ThreeAgentArchitecture:

    def __init__(self, llm: LLM):
        self.researcher = ThreeAgentResearcher(llm)
        self.fact_checker_critic = ThreeAgentFactCheckerCritic(llm)
        self.writer = ThreeAgentWriter(llm)

    def run(
        self,
        question: str,
        research: ResearchBundle,
    ) -> LLMResponse:

        research_result = self.researcher.run(
            question,
            research,
        )

        reviewed_result = self.fact_checker_critic.run(
            question,
            research_result.text,
        )

        final_result = self.writer.run(
            question,
            reviewed_result.text,
        )

        return final_result