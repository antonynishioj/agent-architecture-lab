from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_lab.api.results import ResultStore
from agent_lab.api.routes import APIContext, create_router
from agent_lab.experiments.benchmark import BenchmarkLoader
from agent_lab.experiments.service import ExperimentService
from agent_lab.llm.gemini import GeminiProvider
from agent_lab.llm.pricing import PricingRegistry
from agent_lab.research.tavily import TavilyResearchTool


def create_app() -> FastAPI:
    generator_llm = GeminiProvider()
    judge_llm = GeminiProvider()

    research_tool = TavilyResearchTool(
        max_results=5
    )

    pricing_registry = PricingRegistry()

    # Pricing is intentionally not configured for the
    # development Gemini model.
    #
    # The final benchmark will use Anthropic pricing.
    pricing_registry.register(
        model=generator_llm.model,
        pricing=__import__(
            "agent_lab.llm.pricing",
            fromlist=["ModelPricing"],
        ).ModelPricing(),
    )

    service = ExperimentService(
        generator_llm=generator_llm,
        judge_llm=judge_llm,
        research_tool=research_tool,
        pricing_registry=pricing_registry,
        results_directory="data/results",
    )

    benchmark_loader = BenchmarkLoader(
        benchmark_file="data/benchmark/benchmark.json",
        research_file="data/benchmark/research.json",
    )

    result_store = ResultStore(
        directory="data/results/cases"
    )

    context = APIContext(
        service=service,
        benchmark_loader=benchmark_loader,
        result_store=result_store,
    )

    app = FastAPI(
        title="AI Agent Architecture Lab",
        description=(
            "Experimental framework for measuring "
            "different AI agent architectures."
        ),
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(
        create_router(context)
    )

    return app


app = create_app() 