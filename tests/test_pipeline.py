import json
import re
from pathlib import Path

import pytest

from agent_lab.analysis.report import build_summary
from agent_lab.analysis.winner import choose_winner
from agent_lab.architectures.definitions import ARCHITECTURES, ROLES
from agent_lab.architectures.pipeline import PipelineArchitecture, prompt_fingerprint
from agent_lab.evaluation.deterministic import compute_metrics
from agent_lab.experiments.benchmark import BenchmarkLoader
from agent_lab.experiments.engine import ExperimentEngine, calls_per_item
from agent_lab.experiments.store import RunStore
from agent_lab.llm.base import GenerationConfig, LLM, LLMResponse
from agent_lab.llm.cache import CacheMissError
from agent_lab.settings import PROJECT_ROOT


class FakeLLM(LLM):
    """Deterministic stand-in for Gemini. Quality depends on agent count."""

    def __init__(self, model: str):
        self.model = model
        self.calls = 0

    def generate(self, prompt: str, config: GenerationConfig | None = None) -> LLMResponse:
        self.calls += 1

        if "Rank the answers" in prompt:
            labels = re.findall(r"=== Answer ([A-Z]) ===", prompt)
            text = json.dumps({"reasoning": "fake", "ranking": sorted(labels)})
        elif "impartial, strict evaluator" in prompt:
            # Answers carry their agent count, so the fake judge can score them.
            match = re.search(r"AGENTS=(\d)", prompt)
            agents = int(match.group(1)) if match else 1
            score = {1: 0.70, 2: 0.80, 3: 0.805, 4: 0.81}[agents]
            text = json.dumps(
                {
                    "key_points": [{"point": "p", "status": "covered"}],
                    "unsupported_claims": [],
                    "trap_violations": [],
                    "reasoning": "fake",
                    **{
                        name: score
                        for name in (
                            "answer_relevancy",
                            "completeness",
                            "faithfulness",
                            "citation_quality",
                            "uncertainty_handling",
                            "overall_quality",
                        )
                    },
                }
            )
        else:
            agents = int(re.search(r"of (\d) in a research team", prompt).group(1)) if "in a research team" in prompt else 1
            text = f"Answer from team AGENTS={agents} citing [S1] and [S2]. Seed={config.seed if config else None}."

        return LLMResponse(
            text=text,
            input_tokens=len(prompt) // 4,
            output_tokens=len(text) // 4,
            latency_ms=10.0,
            model=self.model,
        )


@pytest.fixture
def lab_store(tmp_path: Path):
    loader = BenchmarkLoader(
        PROJECT_ROOT / "data" / "benchmark" / "benchmark.json",
        PROJECT_ROOT / "data" / "benchmark" / "research.json",
    )
    return RunStore(tmp_path), loader.load_all()


def _create(store: RunStore, cases, trials=2):
    return store.create(
        run_id="testrun",
        run_type="benchmark",
        label="",
        cases=cases,
        trials=trials,
        architectures=[a.name for a in ARCHITECTURES],
        generator_model="fake-gen",
        judge_model="fake-judge",
        generator_temperature=0.3,
        judge_temperature=0.0,
        max_output_tokens=512,
        prompt_fingerprint=prompt_fingerprint(),
    )


def test_every_architecture_covers_every_role():
    for architecture in ARCHITECTURES:
        assert architecture.roles == ROLES


def test_source_visibility_rule(lab_store):
    _, cases = lab_store
    case = cases[0]

    for architecture in ARCHITECTURES:
        pipeline = PipelineArchitecture(architecture, FakeLLM("g"), GenerationConfig())
        answer, steps = pipeline.run(case.question, case.research)

        assert len(steps) == architecture.agent_count
        for step in steps:
            expected = bool({"research", "fact_check"} & set(step.roles))
            assert step.saw_sources == expected


def test_benchmark_has_four_tiers_of_three():
    loader = BenchmarkLoader(
        PROJECT_ROOT / "data" / "benchmark" / "benchmark.json",
        PROJECT_ROOT / "data" / "benchmark" / "research.json",
    )
    cases = loader.load_all()
    tiers = {}
    for case in cases:
        tiers[case.difficulty] = tiers.get(case.difficulty, 0) + 1
        assert case.key_points and case.research.results
    assert tiers == {"easy": 3, "medium": 3, "hard": 3, "adversarial": 3}


def test_engine_end_to_end_and_offline_replay(lab_store, tmp_path):
    store, cases = lab_store
    cases = cases[:3]
    manifest = _create(store, cases, trials=2)

    generator, judge = FakeLLM("fake-gen"), FakeLLM("fake-judge")
    engine = ExperimentEngine(store, generator, judge)
    result = engine.run(manifest.run_id)

    assert result.status == "completed"
    per_item = calls_per_item(result.architectures)
    assert generator.calls == 6 * per_item["generator"]
    assert judge.calls == 6 * per_item["judge"]

    path = store.root / manifest.directory
    summary = json.loads((path / "summary.json").read_text())

    # 2/3/4-agent are within 0.02 of each other; 2-agent is cheapest of those.
    assert summary["winner"]["best_quality"] == "4-agent"
    assert summary["winner"]["winner"] == "2-agent"
    assert (path / "REPORT.md").exists()
    assert (path / "summary.csv").read_text().startswith("architecture,")

    # Recomputing from raw files reproduces the published summary.
    assert json.loads(json.dumps(build_summary(path))) == summary

    # Resuming a completed run makes no new API calls (cache + manifest).
    manifest = store.load(manifest.run_id)
    for item in manifest.items:
        item.status = "pending"
    store.save(manifest)
    calls_before = generator.calls
    engine.run(manifest.run_id)
    assert generator.calls == calls_before

    # Offline engine with no LLM reproduces from cache, and fails loudly on a miss.
    offline = ExperimentEngine(store, None, None)
    manifest = store.load(manifest.run_id)
    for item in manifest.items:
        item.status = "pending"
    store.save(manifest)
    offline.run(manifest.run_id, offline=True)
    assert json.loads((path / "summary.json").read_text())["architectures"] == summary["architectures"]

    (path / "llm_cache.jsonl").unlink()
    manifest = store.load(manifest.run_id)
    manifest.items[0].status = "pending"
    store.save(manifest)
    with pytest.raises(CacheMissError):
        ExperimentEngine(store, None, None).run(manifest.run_id, offline=True)
    assert store.load(manifest.run_id).status == "paused"


def test_winner_prefers_best_when_others_clearly_worse():
    scores = {
        "1-agent": {f"c{i}": 0.5 + 0.01 * (i % 3) for i in range(12)},
        "4-agent": {f"c{i}": 0.8 + 0.01 * (i % 3) for i in range(12)},
    }
    result = choose_winner(scores, {"1-agent": 1000, "4-agent": 4000}, {"1-agent": 1, "4-agent": 4})
    assert result["winner"] == "4-agent"
    assert result["comparisons"][0]["as_good_as_best"] is False


def test_winner_picks_cheapest_of_statistical_tie():
    scores = {
        "1-agent": {f"c{i}": 0.80 + (0.05 if i % 2 else -0.05) for i in range(12)},
        "4-agent": {f"c{i}": 0.81 + (-0.05 if i % 2 else 0.05) for i in range(12)},
    }
    result = choose_winner(scores, {"1-agent": 1000, "4-agent": 4000}, {"1-agent": 1, "4-agent": 4})
    assert result["best_quality"] == "4-agent"
    assert result["winner"] == "1-agent"


def test_citation_metrics():
    metrics = compute_metrics(
        "Costs are $2,160 per month [S1][S3]. Batch pricing does not apply here at all [S9]. Short.",
        source_count=4,
    )
    assert metrics.citation_count == 3
    assert metrics.invalid_citations == 1
    assert metrics.distinct_sources_cited == 2
    assert metrics.sentence_citation_coverage == 1.0
