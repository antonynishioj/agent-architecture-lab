"""
The pre-registered rule that turns measurements into one winner.

1. Quality Index = equal-weighted mean of the six rubric dimensions.
2. The best architecture is the one with the highest mean Quality Index
   (averaged over trials within a case, then over cases).
3. An architecture is "as good as the best" when the paired bootstrap
   95% CI of (best - it) includes 0, or the mean gap is below
   PRACTICAL_THRESHOLD.
4. The winner is the cheapest of those (fewest mean total tokens per
   answer). Ties go to the architecture with fewer agents.

In words: the smallest team that is not measurably worse than the best.
"""

from agent_lab.analysis.stats import bootstrap_ci, mean


PRACTICAL_THRESHOLD = 0.02

RULE_TEXT = (
    "Winner = the cheapest architecture (fewest tokens per answer) whose "
    "Quality Index is not significantly lower than the best architecture's "
    "(paired bootstrap 95% CI of the difference includes 0, or the gap is "
    f"below {PRACTICAL_THRESHOLD})."
)


def paired_difference(
    best_scores: dict[str, float],
    other_scores: dict[str, float],
    seed: str,
) -> dict:
    shared = sorted(set(best_scores) & set(other_scores))
    differences = [
        best_scores[case] - other_scores[case]
        for case in shared
    ]

    low, high = bootstrap_ci(differences, seed=seed)

    return {
        "n_cases": len(shared),
        "diff_mean": mean(differences),
        "ci_low": low,
        "ci_high": high,
    }


def choose_winner(
    case_scores: dict[str, dict[str, float]],
    tokens: dict[str, float | None],
    agent_counts: dict[str, int],
    seed_prefix: str = "winner",
) -> dict:
    """
    case_scores: architecture -> case_id -> mean quality over trials
    tokens: architecture -> mean total tokens per answer
    """

    means = {
        name: mean(list(scores.values()))
        for name, scores in case_scores.items()
        if scores
    }

    if not means:
        return {
            "winner": None,
            "best_quality": None,
            "candidates": [],
            "comparisons": [],
            "rule": RULE_TEXT,
            "explanation": "No evaluated answers yet.",
        }

    best = max(
        means,
        key=lambda name: (means[name], -agent_counts.get(name, 0)),
    )

    comparisons = []
    candidates = [best]

    for name in sorted(means, key=lambda item: agent_counts.get(item, 0)):
        if name == best:
            continue

        comparison = paired_difference(
            case_scores[best],
            case_scores[name],
            seed=f"{seed_prefix}:{best}:{name}",
        )

        diff = comparison["diff_mean"]
        low = comparison["ci_low"]

        as_good = (
            diff is not None
            and (diff < PRACTICAL_THRESHOLD or (low is not None and low <= 0))
        )

        comparison.update(
            {
                "architecture": name,
                "versus": best,
                "as_good_as_best": as_good,
            }
        )

        comparisons.append(comparison)

        if as_good:
            candidates.append(name)

    winner = min(
        candidates,
        key=lambda name: (
            tokens.get(name) if tokens.get(name) is not None else float("inf"),
            agent_counts.get(name, 0),
        ),
    )

    if winner == best:
        if len(candidates) == 1:
            explanation = (
                f"{best} has the highest quality and every other "
                f"architecture is significantly worse."
            )
        else:
            explanation = (
                f"{best} has the highest quality and is also the cheapest "
                f"of the architectures that are statistically tied with it "
                f"({', '.join(sorted(candidates))})."
            )
    else:
        explanation = (
            f"{best} scored highest, but {winner} is not significantly "
            f"worse and uses fewer tokens, so the extra agents are not "
            f"worth their cost."
        )

    return {
        "winner": winner,
        "best_quality": best,
        "candidates": sorted(candidates, key=lambda n: agent_counts.get(n, 0)),
        "comparisons": comparisons,
        "rule": RULE_TEXT,
        "explanation": explanation,
    }
