import csv
import io
import json
from pathlib import Path

from agent_lab.analysis.aggregate import summarize
from agent_lab.experiments.store import RunStore


CSV_COLUMNS = (
    "architecture",
    "agent_count",
    "quality_index",
    "quality_ci_low",
    "quality_ci_high",
    "answer_relevancy",
    "completeness",
    "faithfulness",
    "citation_quality",
    "uncertainty_handling",
    "overall_quality",
    "win_rate",
    "mean_rank",
    "trap_violation_rate",
    "unsupported_claims_per_answer",
    "citation_validity",
    "calls_per_answer",
    "total_tokens",
    "latency_s",
    "estimated_cost_usd",
    "quality_per_1k_tokens",
    "units_completed",
    "units_failed",
)


def build_summary(path: Path) -> dict:
    manifest = RunStore.load_from_dir(path)

    if manifest is None:
        raise FileNotFoundError(f"No manifest.json in {path}")

    return summarize(manifest, RunStore.load_items(path))


def summary_csv(summary: dict) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
    writer.writeheader()

    for row in summary["architectures"]:
        flat = {**row, **row["dimensions"]}
        writer.writerow({column: flat.get(column) for column in CSV_COLUMNS})

    return buffer.getvalue()


def _fmt(value, digits: int = 3) -> str:
    if value is None:
        return "–"

    if isinstance(value, float):
        return f"{value:.{digits}f}"

    return str(value)


def report_markdown(summary: dict) -> str:
    config = summary["config"]
    winner = summary["winner"]

    lines = [
        f"# Run `{summary['run_id']}`",
        "",
        f"Status: **{summary['status']}** · "
        f"{config['units_completed']}/{config['units_planned']} case-trials · "
        f"generator `{config['generator_model']}` · judge `{config['judge_model']}` · "
        f"git `{config['git_commit']}` · prompts `{config['prompt_fingerprint']}`",
        "",
        "## Winner",
        "",
    ]

    if winner["winner"]:
        lines += [
            f"**{winner['winner']}**. {winner['explanation']}",
            "",
            f"> {winner['rule']}",
            "",
        ]
    else:
        lines += ["No winner yet.", ""]

    lines += [
        "## Leaderboard",
        "",
        "| Architecture | Quality Index (95% CI) | Faithfulness | Completeness | Uncertainty | Win rate | Tokens / answer | Latency (s) | Cost (USD) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for row in summary["architectures"]:
        dims = row["dimensions"]

        lines.append(
            f"| {row['architecture']} "
            f"| {_fmt(row['quality_index'])} ({_fmt(row['quality_ci_low'])}–{_fmt(row['quality_ci_high'])}) "
            f"| {_fmt(dims['faithfulness'])} "
            f"| {_fmt(dims['completeness'])} "
            f"| {_fmt(dims['uncertainty_handling'])} "
            f"| {_fmt(row['win_rate'], 2)} "
            f"| {_fmt(row['total_tokens'], 0)} "
            f"| {_fmt(row['latency_s'], 1)} "
            f"| {_fmt(row['estimated_cost_usd'], 5)} |"
        )

    if winner["comparisons"]:
        lines += [
            "",
            "## Is each architecture as good as the best?",
            "",
            f"Paired bootstrap over cases, against **{winner['best_quality']}**.",
            "",
            "| Architecture | Gap (best − it) | 95% CI | As good as best? |",
            "|---|---|---|---|",
        ]

        for comparison in winner["comparisons"]:
            lines.append(
                f"| {comparison['architecture']} "
                f"| {_fmt(comparison['diff_mean'])} "
                f"| {_fmt(comparison['ci_low'])} to {_fmt(comparison['ci_high'])} "
                f"| {'yes' if comparison['as_good_as_best'] else 'no'} |"
            )

    if summary["by_difficulty"]:
        names = summary["config"]["architectures"]

        lines += [
            "",
            "## Quality by difficulty",
            "",
            "| Difficulty | " + " | ".join(names) + " | Best | Winner |",
            "|---|" + "---|" * (len(names) + 2),
        ]

        for difficulty, tier in summary["by_difficulty"].items():
            lines.append(
                f"| {difficulty} ({tier['cases']}) | "
                + " | ".join(_fmt(tier["quality_index"].get(name)) for name in names)
                + f" | {tier['best_quality']} | {tier['winner']} |"
            )

    lines += [
        "",
        "## Robustness to the scoring weights",
        "",
        "| Scheme | Best quality | Winner |",
        "|---|---|---|",
    ]

    for scheme, result in summary["sensitivity"].items():
        lines.append(
            f"| {scheme} | {result['best_quality']} | {result['winner'] or '–'} |"
        )

    lines += [
        "",
        "## Verify this run",
        "",
        "```bash",
        "uv run agent-lab report <this directory>   # recompute summary.json from the raw case files",
        "uv run agent-lab replay <this directory>   # re-run every call from llm_cache.jsonl, no API key needed",
        "```",
        "",
    ]

    return "\n".join(lines)


def write_reports(path: Path) -> dict:
    summary = build_summary(path)

    (path / "summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    (path / "summary.csv").write_text(
        summary_csv(summary),
        encoding="utf-8",
        newline="",
    )
    (path / "REPORT.md").write_text(
        report_markdown(summary),
        encoding="utf-8",
    )

    return summary
