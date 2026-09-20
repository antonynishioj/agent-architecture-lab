from agent_lab.experiments.benchmark import BenchmarkLoader
from agent_lab.experiments.service import ExperimentService
from agent_lab.llm.gemini import GeminiProvider
from agent_lab.research.tavily import TavilyResearchTool


def main() -> None:

    generator_llm = GeminiProvider()
    judge_llm = GeminiProvider()

    research_tool = TavilyResearchTool(
        max_results=5
    )

    service = ExperimentService(
        generator_llm=generator_llm,
        judge_llm=judge_llm,
        research_tool=research_tool,
        results_directory="data/results",
    )

    loader = BenchmarkLoader(
        benchmark_file="data/benchmark/benchmark.json",
        research_file="data/benchmark/research.json",
    )

    cases = loader.load_all()

    print(
        f"Loaded {len(cases)} benchmark cases."
    )

    reports = service.run_benchmark(cases)

    print(
        f"\nCompleted {len(reports)} benchmark cases."
    )

    for report in reports:
        print(
            f"{report.experiment.case_id} "
            f"→ {report.run_id}"
        )


if __name__ == "__main__":
    main()