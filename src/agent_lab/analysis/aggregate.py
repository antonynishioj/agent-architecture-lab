from collections import defaultdict

from agent_lab.analysis.stats import bootstrap_ci, mean, r4
from agent_lab.analysis.winner import choose_winner
from agent_lab.architectures.definitions import ARCHITECTURES_BY_NAME
from agent_lab.evaluation.result import QUALITY_DIMENSIONS, EvaluationResult
from agent_lab.experiments.result import CaseTrialResult
from agent_lab.experiments.store import RunManifest


DIFFICULTY_ORDER = ("easy", "medium", "hard", "adversarial", "custom")

# Alternative weightings used to check that the conclusion is robust.
WEIGHT_SCHEMES = {
    "equal": {dimension: 1.0 for dimension in QUALITY_DIMENSIONS},
    "trust_first": {
        "answer_relevancy": 0.5,
        "completeness": 1.0,
        "faithfulness": 2.0,
        "citation_quality": 1.0,
        "uncertainty_handling": 1.5,
        "overall_quality": 0.5,
    },
    "overall_only": {"overall_quality": 1.0},
}


def weighted_quality(evaluation: EvaluationResult, weights: dict[str, float]) -> float:
    total = sum(weights.values())

    return sum(
        getattr(evaluation, dimension) * weight
        for dimension, weight in weights.items()
    ) / total


def _case_scores(
    items: list[CaseTrialResult],
    weights: dict[str, float],
    difficulty: str | None = None,
) -> dict[str, dict[str, float]]:
    """architecture -> case_id -> mean weighted quality over trials."""

    per_trial: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for item in items:
        if difficulty and item.difficulty != difficulty:
            continue

        for outcome in item.outcomes:
            if outcome.evaluation is None:
                continue

            per_trial[outcome.architecture][item.case_id].append(
                weighted_quality(outcome.evaluation, weights)
            )

    return {
        architecture: {
            case_id: mean(values)
            for case_id, values in cases.items()
        }
        for architecture, cases in per_trial.items()
    }


def _mean_tokens(items: list[CaseTrialResult]) -> dict[str, float | None]:
    values: dict[str, list[float]] = defaultdict(list)

    for item in items:
        for outcome in item.outcomes:
            if outcome.status == "completed":
                values[outcome.architecture].append(outcome.total_tokens)

    return {name: mean(tokens) for name, tokens in values.items()}


def summarize(
    manifest: RunManifest,
    items: list[CaseTrialResult],
) -> dict:
    architectures = manifest.architectures
    agent_counts = {
        name: ARCHITECTURES_BY_NAME[name].agent_count
        for name in architectures
    }

    case_scores = _case_scores(items, WEIGHT_SCHEMES["equal"])
    tokens = _mean_tokens(items)

    winner = choose_winner(case_scores, tokens, agent_counts)

    rows = []

    for name in architectures:
        outcomes = [
            outcome
            for item in items
            for outcome in item.outcomes
            if outcome.architecture == name
        ]
        completed = [o for o in outcomes if o.status == "completed"]
        evaluated = [o for o in completed if o.evaluation is not None]
        deterministic = [o.deterministic for o in completed if o.deterministic]

        scores = list(case_scores.get(name, {}).values())
        ci_low, ci_high = bootstrap_ci(scores, seed=f"quality:{name}")

        rankings = [
            item.ranking.order
            for item in items
            if item.ranking is not None and name in item.ranking.order
        ]

        quality = mean(scores)
        mean_total_tokens = tokens.get(name)

        rows.append(
            {
                "architecture": name,
                "agent_count": agent_counts[name],
                "units_completed": len(completed),
                "units_failed": len(outcomes) - len(completed),
                "cases_scored": len(scores),
                "quality_index": r4(quality),
                "quality_ci_low": r4(ci_low),
                "quality_ci_high": r4(ci_high),
                "dimensions": {
                    dimension: r4(
                        mean([getattr(o.evaluation, dimension) for o in evaluated])
                    )
                    for dimension in QUALITY_DIMENSIONS
                },
                "trap_violation_rate": r4(
                    mean([1.0 if o.evaluation.trap_violations else 0.0 for o in evaluated])
                ),
                "unsupported_claims_per_answer": r4(
                    mean([len(o.evaluation.unsupported_claims) for o in evaluated])
                ),
                "citation_validity": r4(
                    mean([d.citation_validity for d in deterministic])
                ),
                "sentence_citation_coverage": r4(
                    mean([d.sentence_citation_coverage for d in deterministic])
                ),
                "word_count": r4(mean([d.word_count for d in deterministic])),
                "win_rate": r4(
                    mean([1.0 if order[0] == name else 0.0 for order in rankings])
                ),
                "mean_rank": r4(
                    mean([order.index(name) + 1 for order in rankings])
                ),
                "calls_per_answer": r4(mean([o.call_count for o in completed])),
                "input_tokens": r4(mean([o.input_tokens for o in completed])),
                "output_tokens": r4(mean([o.output_tokens for o in completed])),
                "thinking_tokens": r4(mean([o.thinking_tokens for o in completed])),
                "total_tokens": r4(mean_total_tokens),
                "latency_s": r4(mean([o.latency_ms / 1000 for o in completed])),
                "estimated_cost_usd": (
                    round(mean(costs), 6)
                    if (costs := [o.estimated_cost_usd for o in completed if o.estimated_cost_usd is not None])
                    else None
                ),
                "retries": sum(o.retries for o in completed),
                "quality_per_1k_tokens": r4(
                    quality / (mean_total_tokens / 1000)
                    if quality is not None and mean_total_tokens
                    else None
                ),
            }
        )

    by_difficulty = {}

    for difficulty in DIFFICULTY_ORDER:
        tier_scores = _case_scores(items, WEIGHT_SCHEMES["equal"], difficulty)

        if not tier_scores:
            continue

        tier_items = [item for item in items if item.difficulty == difficulty]
        tier_winner = choose_winner(
            tier_scores,
            _mean_tokens(tier_items),
            agent_counts,
            seed_prefix=f"tier:{difficulty}",
        )

        by_difficulty[difficulty] = {
            "cases": len({item.case_id for item in tier_items}),
            "quality_index": {
                name: r4(mean(list(scores.values())))
                for name, scores in tier_scores.items()
            },
            "best_quality": tier_winner["best_quality"],
            "winner": tier_winner["winner"],
        }

    sensitivity = {}

    for scheme, weights in WEIGHT_SCHEMES.items():
        result = choose_winner(
            _case_scores(items, weights),
            tokens,
            agent_counts,
            seed_prefix=f"scheme:{scheme}",
        )

        sensitivity[scheme] = {
            "best_quality": result["best_quality"],
            "winner": result["winner"],
        }

    ranked = [row for row in rows if row["mean_rank"] is not None]

    if ranked:
        sensitivity["blind_ranking"] = {
            "best_quality": min(ranked, key=lambda row: row["mean_rank"])["architecture"],
            "winner": None,
        }

    per_case = []

    for case_id in manifest.case_ids:
        case_items = [item for item in items if item.case_id == case_id]

        if not case_items:
            continue

        per_case.append(
            {
                "case_id": case_id,
                "difficulty": case_items[0].difficulty,
                "trials": len(case_items),
                "quality_index": {
                    name: r4(case_scores.get(name, {}).get(case_id))
                    for name in architectures
                },
            }
        )

    for comparison in winner["comparisons"]:
        for key in ("diff_mean", "ci_low", "ci_high"):
            comparison[key] = r4(comparison[key])

    return {
        "run_id": manifest.run_id,
        "status": manifest.status,
        "config": {
            "generator_model": manifest.generator_model,
            "judge_model": manifest.judge_model,
            "trials": manifest.trials,
            "architectures": architectures,
            "cases_planned": len(manifest.case_ids),
            "units_planned": len(manifest.items),
            "units_completed": len(items),
            "benchmark_version": manifest.benchmark_version,
            "benchmark_fingerprint": manifest.benchmark_fingerprint,
            "prompt_fingerprint": manifest.prompt_fingerprint,
            "git_commit": manifest.git_commit,
        },
        "winner": winner,
        "architectures": rows,
        "by_difficulty": by_difficulty,
        "sensitivity": sensitivity,
        "per_case": per_case,
    }
