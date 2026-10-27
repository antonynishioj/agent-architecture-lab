import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


def _int(name: str, default: int) -> int:
    value = os.getenv(name)

    if not value:
        return default

    return int(value)


def _float(name: str, default: float) -> float:
    value = os.getenv(name)

    if not value:
        return default

    return float(value)


@dataclass(frozen=True)
class Settings:
    """
    All runtime configuration in one place.

    Every value can be overridden from the .env file. Defaults are
    chosen so the full benchmark fits inside the Gemini free tier.
    """

    gemini_api_key: str | None
    generator_model: str
    judge_model: str

    generator_rpm: int
    judge_rpm: int
    generator_rpd: int
    judge_rpd: int

    generator_temperature: float
    judge_temperature: float
    max_output_tokens: int

    tavily_api_key: str | None

    benchmark_file: Path
    research_file: Path
    pricing_file: Path
    results_directory: Path
    usage_file: Path

    @property
    def tavily_enabled(self) -> bool:
        return bool(self.tavily_api_key)


def load_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        generator_model=os.getenv(
            "GEMINI_MODEL",
            "gemini-3.1-flash-lite",
        ),
        judge_model=os.getenv(
            "GEMINI_JUDGE_MODEL",
            "gemini-3.5-flash-lite",
        ),
        generator_rpm=_int("GEMINI_RPM", 10),
        judge_rpm=_int("GEMINI_JUDGE_RPM", 10),
        generator_rpd=_int("GEMINI_RPD", 500),
        judge_rpd=_int("GEMINI_JUDGE_RPD", 500),
        generator_temperature=_float("GENERATOR_TEMPERATURE", 0.3),
        judge_temperature=_float("JUDGE_TEMPERATURE", 0.0),
        max_output_tokens=_int("MAX_OUTPUT_TOKENS", 4096),
        tavily_api_key=os.getenv("TAVILY_API_KEY") or None,
        benchmark_file=PROJECT_ROOT / "data" / "benchmark" / "benchmark.json",
        research_file=PROJECT_ROOT / "data" / "benchmark" / "research.json",
        pricing_file=PROJECT_ROOT / "data" / "pricing.json",
        results_directory=PROJECT_ROOT / "results" / "runs",
        usage_file=PROJECT_ROOT / "data" / "usage.json",
    )
