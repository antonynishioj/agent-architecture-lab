from agent_lab.architectures.four_agent.architecture import FourAgentArchitecture
from agent_lab.architectures.one_agent.agent import OneAgent
from agent_lab.architectures.three_agent.architecture import ThreeAgentArchitecture
from agent_lab.architectures.two_agent.architecture import TwoAgentArchitecture
from agent_lab.experiments.case import ExperimentCase
from agent_lab.experiments.experiment import ExperimentResult
from agent_lab.experiments.result import ArchitectureResult
from agent_lab.llm.base import LLM
from agent_lab.llm.tracker import TrackingLLM
from agent_lab.research.base import ResearchTool
from agent_lab.research.cache import ResearchCache
from agent_lab.research.result import ResearchBundle


class ExperimentRunner:

    def __init__(
        self,
        llm: LLM,
        research_tool: ResearchTool,
        research_cache: ResearchCache | None = None,
    ):
        self.llm = llm
        self.research_tool = research_tool
        self.research_cache = research_cache or ResearchCache()

    def run_one_agent(
        self,
        question: str,
        research: ResearchBundle,
    ) -> ArchitectureResult:

        tracked_llm = TrackingLLM(self.llm)

        architecture = OneAgent(tracked_llm)

        result = architecture.run(
            question,
            research,
        )

        return ArchitectureResult.from_run(
            question=question,
            architecture_name="1-agent",
            agent_count=1,
            answer=result.text,
            metrics=tracked_llm.metrics,
            model=result.model,
        )

    def run_two_agent(
        self,
        question: str,
        research: ResearchBundle,
    ) -> ArchitectureResult:

        tracked_llm = TrackingLLM(self.llm)

        architecture = TwoAgentArchitecture(tracked_llm)

        result = architecture.run(
            question,
            research,
        )

        return ArchitectureResult.from_run(
            question=question,
            architecture_name="2-agent",
            agent_count=2,
            answer=result.text,
            metrics=tracked_llm.metrics,
            model=result.model,
        )

    def run_three_agent(
        self,
        question: str,
        research: ResearchBundle,
    ) -> ArchitectureResult:

        tracked_llm = TrackingLLM(self.llm)

        architecture = ThreeAgentArchitecture(tracked_llm)

        result = architecture.run(
            question,
            research,
        )

        return ArchitectureResult.from_run(
            question=question,
            architecture_name="3-agent",
            agent_count=3,
            answer=result.text,
            metrics=tracked_llm.metrics,
            model=result.model,
        )

    def run_four_agent(
        self,
        question: str,
        research: ResearchBundle,
    ) -> ArchitectureResult:

        tracked_llm = TrackingLLM(self.llm)

        architecture = FourAgentArchitecture(tracked_llm)

        result = architecture.run(
            question,
            research,
        )

        return ArchitectureResult.from_run(
            question=question,
            architecture_name="4-agent",
            agent_count=4,
            answer=result.text,
            metrics=tracked_llm.metrics,
            model=result.model,
        )

    def run_all(
        self,
        question: str,
        research: ResearchBundle,
    ) -> list[ArchitectureResult]:

        return [
            self.run_one_agent(question, research),
            self.run_two_agent(question, research),
            self.run_three_agent(question, research),
            self.run_four_agent(question, research),
        ]

    def run_case(self, case: ExperimentCase) -> ExperimentResult:
        if case.research is not None:
            research = case.research
        else:
            research = self.research_tool.search(case.question)
            self.research_cache.save(research, case.case_id)

        results = self.run_all(case.question, research)

        return ExperimentResult(
            case_id=case.case_id,
            question=case.question,
            research=research,
            results=results,
        )