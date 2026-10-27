"""
Qualitative checks behind the blog's findings, recomputed from raw files.

These were noticed while reading answers after the official run, so they
are exploratory (not pre-registered). Each check is a plain rule that
anyone can rerun with `uv run agent-lab findings <run>`.
"""

import re
from collections import Counter
from pathlib import Path

from agent_lab.experiments.store import RunStore


# A final answer that contains a heading for an internal hand-off section
# ("### Critique", "**Fact-check report**", ...) leaked the pipeline's notes.
LEAKED_SECTION = re.compile(
    r"(?im)^\s*(#+\s*|\*\*)\s*(critique|fact[- ]check(ing)?( report)?|research brief|critic'?s? (notes|recommendations))\b"
)


def leaked_internal_notes(path: Path) -> dict:
    leaks: Counter = Counter()
    totals: Counter = Counter()

    for item in RunStore.load_items(path):
        for outcome in item.outcomes:
            totals[outcome.architecture] += 1

            if LEAKED_SECTION.search(outcome.answer):
                leaks[outcome.architecture] += 1

    return {name: {"leaked": leaks[name], "answers": totals[name]} for name in sorted(totals)}


def fact_survival(path: Path, case_id: str, patterns: list[str]) -> dict:
    """
    For one case: in how many trials did a fact survive the first agent's
    output, and the final answer? Shows where information is dropped.
    """

    regex = re.compile("|".join(patterns), re.IGNORECASE)
    result: dict = {}

    for item in RunStore.load_items(path):
        if item.case_id != case_id:
            continue

        for outcome in item.outcomes:
            entry = result.setdefault(
                outcome.architecture,
                {"trials": 0, "first_agent": 0, "final_answer": 0},
            )
            entry["trials"] += 1

            if outcome.steps and regex.search(outcome.steps[0].output):
                entry["first_agent"] += 1

            if regex.search(outcome.answer):
                entry["final_answer"] += 1

    return dict(sorted(result.items()))


def key_point_coverage(path: Path, case_id: str, point_prefix: str) -> dict:
    """How often each architecture covered one key point of one case."""

    result: dict = {}

    for item in RunStore.load_items(path):
        if item.case_id != case_id:
            continue

        for outcome in item.outcomes:
            if outcome.evaluation is None:
                continue

            for verdict in outcome.evaluation.key_points:
                if verdict.point.lower().startswith(point_prefix.lower()):
                    counts = result.setdefault(outcome.architecture, Counter())
                    counts[verdict.status] += 1

    return {name: dict(counts) for name, counts in sorted(result.items())}


def all_findings(path: Path) -> dict:
    return {
        "leaked_internal_notes": leaked_internal_notes(path),
        "helios_7b_contrast": fact_survival(
            path,
            "distractor-study-009",
            [r"\b7\s?B\b", r"7 billion"],
        ),
        "false_premise_rumour_source": key_point_coverage(
            path,
            "false-premise-011",
            "The 'dropped GC' claim",
        ),
    }
