import json
from pathlib import Path

from pydantic import BaseModel

from agent_lab.experiments.case import ExperimentCase
from agent_lab.research.result import ResearchBundle


class BenchmarkDataset(BaseModel):
    version: str
    cases: list[ExperimentCase]


class ResearchDataset(BaseModel):
    version: str
    cases: dict[str, ResearchBundle]


class BenchmarkLoader:
    def __init__(
        self,
        benchmark_file: str = "data/benchmark/benchmark.json",
        research_file: str = "data/benchmark/research.json",
    ):
        self.benchmark_file = Path(benchmark_file)
        self.research_file = Path(research_file)

    def load_benchmark(self) -> BenchmarkDataset:
        if not self.benchmark_file.exists():
            raise FileNotFoundError(
                f"Benchmark file not found: {self.benchmark_file}"
            )

        data = json.loads(
            self.benchmark_file.read_text(encoding="utf-8")
        )

        return BenchmarkDataset.model_validate(data)

    def load_research(self) -> ResearchDataset:
        if not self.research_file.exists():
            raise FileNotFoundError(
                f"Research file not found: {self.research_file}"
            )

        data = json.loads(
            self.research_file.read_text(encoding="utf-8")
        )

        return ResearchDataset.model_validate(data)

    def load_all(self) -> list[ExperimentCase]:
        benchmark = self.load_benchmark()
        research = self.load_research()

        cases = []

        for case in benchmark.cases:
            research_bundle = research.cases.get(case.case_id)

            if research_bundle is None:
                raise ValueError(
                    f"No research found for benchmark case: "
                    f"{case.case_id}"
                )

            cases.append(
                case.model_copy(
                    update={
                        "research": research_bundle
                    }
                )
            )

        return cases

    def load_case(self, case_id: str) -> ExperimentCase:
        cases = self.load_all()

        for case in cases:
            if case.case_id == case_id:
                return case

        raise KeyError(
            f"Benchmark case not found: {case_id}"
        )