from agent_lab.evaluation.experiment_result import EvaluatedExperimentResult
from agent_lab.evaluation.llm_judge import LLMJudge
from agent_lab.evaluation.runner import EvaluationRunner
from agent_lab.experiments.case import ExperimentCase
from agent_lab.experiments.runner import ExperimentRunner
from agent_lab.llm.gemini import GeminiProvider
from agent_lab.research.tavily import TavilyResearchTool
from agent_lab.research.cache import ResearchCache


def main():

    research_cache = ResearchCache()

    case = ExperimentCase(
        case_id="rag-reliability-002",
        question=(
            "Does retrieval-augmented generation actually make "
            "LLM answers more reliable? Explain both the benefits "
            "and limitations, and describe the conditions under "
            "which RAG is likely to improve reliability."
        ),
        reference_answer=(
            "Retrieval-augmented generation can improve the reliability "
            "of LLM answers by grounding responses in external evidence, "
            "including current, domain-specific, or private information. "
            "It can reduce reliance on information stored in the model's "
            "parameters and can make it easier to update knowledge without "
            "retraining the model. However, RAG does not guarantee reliable "
            "answers. The retrieval system may return irrelevant, incomplete, "
            "outdated, or incorrect information, and the model may still "
            "misinterpret or misuse the retrieved evidence. Therefore, RAG "
            "is most likely to improve reliability when the retrieval system "
            "returns relevant and trustworthy sources, the retrieved evidence "
            "adequately covers the question, and the model uses that evidence "
            "accurately."
        ),
        research=research_cache.load("rag-reliability-002"),
    )

    # --------------------------------------------------
    # Generator
    # --------------------------------------------------

    generator_llm = GeminiProvider()

    research_tool = TavilyResearchTool(
        max_results=5,
    )

    experiment_runner = ExperimentRunner(
        llm=generator_llm,
        research_tool=research_tool,
    )

    experiment = experiment_runner.run_case(case)

    # --------------------------------------------------
    # Independent evaluator
    # --------------------------------------------------

    judge_llm = GeminiProvider()

    evaluator = LLMJudge(
        llm=judge_llm,
    )

    evaluation_runner = EvaluationRunner(
        evaluator=evaluator,
    )

    evaluated_experiment = evaluation_runner.evaluate_experiment(
        case=case,
        experiment=experiment,
    )

    # --------------------------------------------------
    # Print execution metrics
    # --------------------------------------------------

    print("\n=== EXPERIMENT ===")
    print(f"Case: {experiment.case_id}")
    print(f"Question: {experiment.question}")
    print(
        f"Research sources: "
        f"{len(experiment.research.results)}"
    )

    print("\n=== ARCHITECTURE RESULTS ===")

    for result in experiment.results:

        print(f"\n--- {result.architecture_name} ---")

        print(f"Calls: {result.call_count}")
        print(f"Input tokens: {result.input_tokens}")
        print(f"Output tokens: {result.output_tokens}")
        print(f"Total tokens: {result.total_tokens}")
        print(f"Latency: {result.latency_ms:.0f} ms")

    # --------------------------------------------------
    # Print independent quality evaluation
    # --------------------------------------------------

    print("\n=== QUALITY EVALUATION ===")

    for result in evaluated_experiment.results:

        evaluation = result.evaluation

        print(f"\n--- {result.architecture.architecture_name} ---")

        print(
            f"Answer relevancy: "
            f"{evaluation.answer_relevancy:.2f}"
        )

        print(
            f"Completeness: "
            f"{evaluation.completeness:.2f}"
        )

        print(
            f"Faithfulness: "
            f"{evaluation.faithfulness:.2f}"
        )

        print(
            f"Overall quality: "
            f"{evaluation.overall_quality:.2f}"
        )

        print(
            f"Reasoning: "
            f"{evaluation.reasoning}"
        )


if __name__ == "__main__":
    main()