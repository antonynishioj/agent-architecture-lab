from collections.abc import Callable

from agent_lab.architectures.four_agent.architecture import FourAgentArchitecture
from agent_lab.architectures.one_agent.agent import OneAgent
from agent_lab.architectures.three_agent.architecture import ThreeAgentArchitecture
from agent_lab.architectures.two_agent.architecture import TwoAgentArchitecture
from agent_lab.experiments.case import ExperimentCase
from agent_lab.experiments.result import ArchitectureResult, ExperimentResult
from agent_lab.llm.base import LLM
from agent_lab.llm.pricing import PricingRegistry
from agent_lab.llm.tracker import TrackingLLM
from agent_lab.research.base import ResearchTool
from agent_lab.research.result import ResearchBundle


ProgressCallback = Callable[[dict], None]


class ExperimentRunner:
    def __init__(
        self,
        llm: LLM,
        research_tool: ResearchTool,
        pricing_registry: PricingRegistry | None = None,
    ):
        self.llm = llm
        self.research_tool = research_tool
        self.pricing_registry = pricing_registry

    def _create_tracking_llm(self) -> TrackingLLM:
        return TrackingLLM(
            llm=self.llm,
            pricing_registry=self.pricing_registry,
        )

    @staticmethod
    def _emit(
        callback: ProgressCallback | None,
        **event,
    ) -> None:
        if callback:
            callback(event)

    def run_one_agent(
        self,
        question: str,
        research: ResearchBundle,
    ) -> ArchitectureResult:
        llm = self._create_tracking_llm()

        architecture = OneAgent(llm=llm)

        answer = architecture.run(
            question=question,
            research=research,
        )

        return ArchitectureResult.from_run(
            question=question,
            architecture_name="1-agent",
            agent_count=1,
            answer=answer,
            metrics=llm.metrics,
            model=llm.llm.generate("").model
            
        )

    def run_two_agent(
        self,
        question: str,
        research: ResearchBundle,
    ) -> ArchitectureResult:
        llm = self._create_tracking_llm()

        architecture = TwoAgentArchitecture(llm=llm)

        answer = architecture.run(
            question=question,
            research=research,
        )

        return ArchitectureResult.from_run(
            question=question,
            architecture_name="2-agent",
            agent_count=2,
            answer=answer,
            metrics=llm.metrics,
            model=getattr(llm.llm, "model", "unknown"),
        )

    def run_three_agent(
        self,
        question: str,
        research: ResearchBundle,
    ) -> ArchitectureResult:
        llm = self._create_tracking_llm()

        architecture = ThreeAgentArchitecture(llm=llm)

        answer = architecture.run(
            question=question,
            research=research,
        )

        return ArchitectureResult.from_run(
            question=question,
            architecture_name="3-agent",
            agent_count=3,
            answer=answer,
            metrics=llm.metrics,
            model=getattr(llm.llm, "model", "unknown"),
        )

    def run_four_agent(
        self,
        question: str,
        research: ResearchBundle,
    ) -> ArchitectureResult:
        llm = self._create_tracking_llm()

        architecture = FourAgentArchitecture(llm=llm)

        answer = architecture.run(
            question=question,
            research=research,
        )

        return ArchitectureResult.from_run(
            question=question,
            architecture_name="4-agent",
            agent_count=4,
            answer=answer,
            metrics=llm.metrics,
            model=getattr(llm.llm, "model", "unknown"),
        )

    def run_all(
        self,
        question: str,
        research: ResearchBundle,
        progress_callback: ProgressCallback | None = None,
    ) -> list[ArchitectureResult]:

        runners = [
            ("1-agent", self.run_one_agent),
            ("2-agent", self.run_two_agent),
            ("3-agent", self.run_three_agent),
            ("4-agent", self.run_four_agent),
        ]

        results: list[ArchitectureResult] = []

        for index, (name, runner) in enumerate(
            runners,
            start=1,
        ):
            self._emit(
                progress_callback,
                stage="architecture_started",
                architecture=name,
                architecture_index=index,
                architecture_total=4,
            )

            result = runner(
                question=question,
                research=research,
            )

            results.append(result)

            self._emit(
                progress_callback,
                stage="architecture_completed",
                architecture=name,
                architecture_index=index,
                architecture_total=4,
                call_count=result.call_count,
                total_tokens=result.total_tokens,
                latency_ms=result.latency_ms,
                estimated_cost_usd=result.estimated_cost_usd,
            )

        return results

    def run_case(
        self,
        case: ExperimentCase,
        progress_callback: ProgressCallback | None = None,
    ) -> ExperimentResult:

        if case.research is not None:
            self._emit(
                progress_callback,
                stage="research_loaded",
                case_id=case.case_id,
            )

            research = case.research

        else:
            self._emit(
                progress_callback,
                stage="research_started",
                case_id=case.case_id,
            )

            research = self.research_tool.search(
                case.question
            )

            self._emit(
                progress_callback,
                stage="research_completed",
                case_id=case.case_id,
                source_count=len(research.results),
            )

        results = self.run_all(
            question=case.question,
            research=research,
            progress_callback=progress_callback,
        )

        return ExperimentResult(
            case_id=case.case_id,
            question=case.question,
            research=research,
            results=results,
        )