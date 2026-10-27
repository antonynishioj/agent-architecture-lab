"""
Figures for the blog post (PNG, light theme, print-friendly).

Colours are the reference palette's light-surface steps. Every mark is
also direct-labelled, so identity never depends on colour alone.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

from agent_lab.architectures.definitions import ARCHITECTURES  # noqa: E402
from agent_lab.architectures.roles import ROLE_SPECS  # noqa: E402


COLORS = {
    "1-agent": "#2a78d6",
    "2-agent": "#eb6834",
    "3-agent": "#1baf7a",
    "4-agent": "#eda100",
}

INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#8a8984"
GRID = "#e5e4e0"
SURFACE = "#fcfcfb"
PANEL = "#f3f2ee"

TIERS = ("easy", "medium", "hard", "adversarial")

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.edgecolor": GRID,
        "axes.labelcolor": INK_2,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "axes.titleweight": "bold",
        "axes.titlesize": 12,
        "axes.titlecolor": INK,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
    }
)


def _save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def _box(ax, x, y, w, h, text, face=PANEL, edge=GRID, color=INK, size=9, weight="normal"):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.01,rounding_size=0.08",
            facecolor=face,
            edgecolor=edge,
            linewidth=1.2,
        )
    )
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=color, weight=weight, wrap=True)


def _arrow(ax, start, end, color=INK_2, style="-|>", dashed=False):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle=style,
            mutation_scale=12,
            color=color,
            linewidth=1.3,
            linestyle=(0, (3, 3)) if dashed else "-",
        )
    )


# ---------------------------------------------------------------------------
# Diagrams


def architectures_diagram(path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.6)
    ax.axis("off")

    row_height = 1.25
    left = 1.9
    width_total = 7.7

    for row, architecture in enumerate(ARCHITECTURES):
        y = 4.45 - row * row_height
        color = COLORS[architecture.name]

        ax.add_patch(FancyBboxPatch((0.1, y + 0.18), 0.22, 0.22, boxstyle="round,pad=0,rounding_size=0.04", color=color))
        ax.text(0.45, y + 0.29, architecture.name, va="center", fontsize=11, weight="bold", color=INK)
        ax.text(0.45, y - 0.02, f"{architecture.agent_count} call{'s' if architecture.agent_count > 1 else ''}", va="center", fontsize=8.5, color=MUTED)

        count = architecture.agent_count
        gap = 0.35
        box_width = (width_total - gap * (count - 1)) / count

        for index, agent in enumerate(architecture.agents):
            x = left + index * (box_width + gap)
            roles = "\n".join(ROLE_SPECS[role].title for role in agent.responsibilities)
            sees = {"research", "fact_check"} & set(agent.responsibilities)

            _box(ax, x, y - 0.2, box_width, 0.85, roles, face="#ffffff", edge=color, size=8.5)
            ax.text(x + 0.08, y + 0.55, f"Agent {index + 1}", fontsize=7, color=MUTED, va="center")

            if sees:
                ax.text(x + box_width - 0.08, y + 0.55, "sees sources", fontsize=7, color=color, va="center", ha="right")

            if index < count - 1:
                _arrow(ax, (x + box_width + 0.03, y + 0.22), (x + box_width + gap - 0.03, y + 0.22))

    ax.text(
        5,
        -0.15,
        "Same four roles, same role instructions, same evidence. Only the grouping into agents changes.\n"
        "Each agent receives the notes of every earlier agent; only research and fact-checking agents see the raw sources.",
        ha="center",
        va="top",
        fontsize=8.5,
        color=INK_2,
    )

    return _save(fig, path)


def experiment_flow_diagram(path: Path, generator_model: str, judge_model: str) -> Path:
    fig, ax = plt.subplots(figsize=(10, 4.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.4)
    ax.axis("off")

    _box(ax, 0.1, 1.6, 1.7, 1.2, "Benchmark case\nquestion +\nfrozen sources\n+ key points", size=8.5)

    for index, architecture in enumerate(ARCHITECTURES):
        y = 3.5 - index * 0.95
        _box(ax, 2.4, y, 1.5, 0.7, architecture.name, face="#ffffff", edge=COLORS[architecture.name], size=9, weight="bold")
        _arrow(ax, (1.8, 2.2), (2.4, y + 0.35))
        _arrow(ax, (3.9, y + 0.35), (4.5, 2.2))

    ax.text(3.15, 4.3, "in parallel, 3 trials each", ha="center", fontsize=8, color=MUTED)

    _box(ax, 4.5, 2.65, 1.9, 0.9, "Rubric judge (blind)\n6 dimensions,\nkey-point checklist", size=8)
    _box(ax, 4.5, 1.55, 1.9, 0.9, "Ranking judge (blind)\n4 answers shuffled\nA–D, ranked", size=8)
    _box(ax, 4.5, 0.45, 1.9, 0.9, "Deterministic checks\ncitations, tokens,\nlatency, cost", size=8)

    _box(ax, 7.0, 1.55, 1.3, 0.9, "Statistics\nbootstrap CIs\nper case & tier", size=8)
    _box(ax, 8.7, 1.55, 1.2, 0.9, "Winner\nrule", face=INK, edge=INK, color="#ffffff", size=9, weight="bold")

    for y in (3.1, 2.0, 0.9):
        _arrow(ax, (6.4, y), (7.0, 2.0))
    _arrow(ax, (8.3, 2.0), (8.7, 2.0))

    ax.text(5, 0.05, f"Generator: {generator_model} · Judge: {judge_model} (a different, newer model)", ha="center", fontsize=8.5, color=INK_2)

    return _save(fig, path)


def winner_rule_diagram(path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 2.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2.6)
    ax.axis("off")

    steps = [
        ("1  Score", "Quality Index =\nmean of 6 rubric\ndimensions"),
        ("2  Best", "highest mean\nacross cases\n(trials averaged)"),
        ("3  Tie test", "paired bootstrap:\nnot significantly worse\nor gap < 0.02"),
        ("4  Cheapest", "fewest tokens\namong the tied\n= WINNER"),
    ]

    for index, (title, body) in enumerate(steps):
        x = 0.15 + index * 2.5
        last = index == len(steps) - 1
        _box(ax, x, 0.35, 2.1, 1.75, "", face=INK if last else PANEL, edge=INK if last else GRID)
        ax.text(x + 1.05, 1.75, title, ha="center", fontsize=10.5, weight="bold", color="#ffffff" if last else INK)
        ax.text(x + 1.05, 1.0, body, ha="center", va="center", fontsize=8.5, color="#ffffff" if last else INK_2)

        if not last:
            _arrow(ax, (x + 2.12, 1.22), (x + 2.48, 1.22))

    return _save(fig, path)


def difficulty_ladder(path: Path, cases: list) -> Path:
    descriptions = {
        "easy": "All sources agree.\nOne clear answer.",
        "medium": "Combine 5 sources,\ncover every trade-off.",
        "hard": "Conflicts, outdated\nprices, distractors,\nmulti-step maths.",
        "adversarial": "Missing evidence,\nfalse premises,\nplanted wrong claims.",
    }

    fig, ax = plt.subplots(figsize=(10, 3.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.4)
    ax.axis("off")

    shades = ["#cde2fb", "#9ec5f4", "#5598e7", "#256abf"]

    for index, tier in enumerate(TIERS):
        x = 0.2 + index * 2.45
        height = 1.3 + index * 0.5
        dark = index >= 2
        _box(ax, x, 0.3, 2.25, height, "", face=shades[index], edge=shades[index])
        ax.text(x + 0.12, 0.3 + height - 0.22, tier.upper(), fontsize=10, weight="bold", color="#ffffff" if dark else INK)
        ax.text(x + 0.12, 0.3 + height - 0.42, descriptions[tier], fontsize=8, va="top", color="#ffffff" if dark else INK_2)

        count = sum(1 for case in cases if case.difficulty == tier)
        ax.text(x + 2.13, 0.42, f"{count} cases", fontsize=8, ha="right", color="#ffffff" if dark else INK_2)

    return _save(fig, path)


# ---------------------------------------------------------------------------
# Result charts


def _style(ax, grid_axis="x"):
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis=grid_axis, color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def quality_interval_chart(summary: dict, path: Path) -> Path:
    rows = [row for row in summary["architectures"] if row["quality_index"] is not None]

    fig, ax = plt.subplots(figsize=(8, 3.2))
    _style(ax)

    for index, row in enumerate(reversed(rows)):
        color = COLORS[row["architecture"]]
        ax.plot([row["quality_ci_low"], row["quality_ci_high"]], [index, index], color=color, linewidth=2, solid_capstyle="round")
        ax.scatter([row["quality_index"]], [index], s=70, color=color, edgecolor=SURFACE, linewidth=2, zorder=3)
        ax.text(row["quality_ci_high"] + 0.003, index, f"{row['quality_index']:.3f}", va="center", fontsize=9, color=INK_2)

    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([row["architecture"] for row in reversed(rows)])
    ax.set_xlabel("Quality Index (mean across cases, 95% bootstrap CI)")
    ax.set_title("Answer quality by architecture", loc="left")

    return _save(fig, path)


def tradeoff_chart(summary: dict, path: Path) -> Path:
    rows = [row for row in summary["architectures"] if row["quality_index"] is not None]

    fig, ax = plt.subplots(figsize=(8, 4))
    _style(ax, grid_axis="y")

    for row in rows:
        color = COLORS[row["architecture"]]
        ax.scatter([row["total_tokens"]], [row["quality_index"]], s=90, color=color, edgecolor=SURFACE, linewidth=2, zorder=3)
        ax.annotate(row["architecture"], (row["total_tokens"], row["quality_index"]), xytext=(8, 4), textcoords="offset points", fontsize=9, color=INK)

    ax.set_xlim(left=0, right=max(row["total_tokens"] for row in rows) * 1.18)
    ax.set_xlabel("Tokens per answer (lower is cheaper)")
    ax.set_ylabel("Quality Index")
    ax.set_title("Quality vs cost: up and to the left is better", loc="left")

    return _save(fig, path)


def tier_chart(summary: dict, path: Path) -> Path:
    tiers = [tier for tier in TIERS if tier in summary["by_difficulty"]]

    fig, ax = plt.subplots(figsize=(8, 4))
    _style(ax, grid_axis="y")

    for name in summary["config"]["architectures"]:
        values = [summary["by_difficulty"][tier]["quality_index"].get(name) for tier in tiers]
        ax.plot(tiers, values, color=COLORS[name], linewidth=2, marker="o", markersize=7, markeredgecolor=SURFACE, markeredgewidth=2, label=name)
        if values and values[-1] is not None:
            ax.annotate(name, (len(tiers) - 1, values[-1]), xytext=(8, 0), textcoords="offset points", va="center", fontsize=8.5, color=INK_2)

    ax.set_ylabel("Quality Index")
    ax.set_title("Quality by difficulty tier", loc="left")
    ax.legend(frameon=False, ncol=4, loc="lower left", bbox_to_anchor=(0, -0.28), fontsize=8.5)
    ax.set_xlim(-0.2, len(tiers) - 0.4)

    return _save(fig, path)


def cost_charts(summary: dict, path: Path) -> Path:
    rows = summary["architectures"]
    names = [row["architecture"] for row in rows]
    colors = [COLORS[name] for name in names]

    fig, axes = plt.subplots(1, 2, figsize=(10, 3))

    for ax, key, title, fmt in (
        (axes[0], "total_tokens", "Tokens per answer", lambda v: f"{v:,.0f}"),
        (axes[1], "latency_s", "Latency per answer (s)", lambda v: f"{v:.1f}s"),
    ):
        _style(ax)
        values = [row[key] or 0 for row in rows]
        ax.barh(names[::-1], values[::-1], color=colors[::-1], height=0.55)
        for index, value in enumerate(values[::-1]):
            ax.text(value + max(values) * 0.02, index, fmt(value), va="center", fontsize=8.5, color=INK_2)
        ax.set_xlim(0, max(values) * 1.25 if max(values) else 1)
        ax.set_title(title, loc="left")

    fig.tight_layout()
    return _save(fig, path)


def dimension_chart(summary: dict, path: Path) -> Path:
    dimensions = [
        ("answer_relevancy", "Relevancy"),
        ("completeness", "Completeness"),
        ("faithfulness", "Faithfulness"),
        ("citation_quality", "Citations"),
        ("uncertainty_handling", "Uncertainty"),
        ("overall_quality", "Overall"),
    ]
    rows = summary["architectures"]

    fig, ax = plt.subplots(figsize=(10, 3.6))
    _style(ax, grid_axis="y")

    # A dot plot, not bars: scores sit near the top of the scale, and a
    # bar that does not start at zero would exaggerate the differences.
    offset = 0.6 / len(rows)

    for index, row in enumerate(rows):
        positions = [d + (index - (len(rows) - 1) / 2) * offset for d in range(len(dimensions))]
        values = [row["dimensions"][key] for key, _ in dimensions]
        ax.scatter(positions, values, s=55, color=COLORS[row["architecture"]], edgecolor=SURFACE, linewidth=2, zorder=3, label=row["architecture"])

    ax.set_xticks(range(len(dimensions)))
    ax.set_xticklabels([label for _, label in dimensions])
    ax.set_title("Mean score per rubric dimension", loc="left")
    ax.legend(frameon=False, ncol=4, loc="upper left", bbox_to_anchor=(0, -0.12), fontsize=8.5)

    return _save(fig, path)


# ---------------------------------------------------------------------------
# Tables as images (Medium's editor has no tables)


def _plain(text: str) -> str:
    return text.replace("**", "").replace("`", "")


def table_image(header: list[str], rows: list[list[str]], path: Path, highlight: int | None = None) -> Path:
    import textwrap

    columns = len(header)
    cells = [[_plain(str(cell)) for cell in row] for row in [header, *rows]]

    # Column width in characters, proportional to content, capped.
    widths = [
        min(42, max(8, max(len(row[index]) for row in cells)))
        for index in range(columns)
    ]
    total = sum(widths)
    budget = 118
    if total > budget:
        widths = [max(8, int(width * budget / total)) for width in widths]

    wrapped = [
        [textwrap.wrap(cell, width=widths[index]) or [""] for index, cell in enumerate(row)]
        for row in cells
    ]
    line_counts = [max(len(cell) for cell in row) for row in wrapped]

    char_w = 0.088  # inches per character at 9pt (generous, so text never overflows)
    line_h = 0.2
    pad = 0.12
    fig_w = sum(widths) * char_w + pad * 2 * columns
    fig_h = sum(count * line_h + pad * 2 for count in line_counts)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(fig_h, 0)
    ax.axis("off")

    y = 0.0
    for row_index, row in enumerate(wrapped):
        height = line_counts[row_index] * line_h + pad * 2
        is_header = row_index == 0

        if is_header:
            face = "#e8e7e2"
        elif highlight is not None and row_index - 1 == highlight:
            face = "#eef4fc"
        else:
            face = SURFACE if row_index % 2 else "#f6f5f2"

        ax.add_patch(plt.Rectangle((0, y), fig_w, height, facecolor=face, edgecolor="none"))

        x = 0.0
        for column, lines in enumerate(row):
            ax.text(
                x + pad,
                y + pad,
                "\n".join(lines),
                fontsize=9,
                va="top",
                ha="left",
                color=INK,
                weight="bold" if is_header else "normal",
                linespacing=1.45,
            )
            x += widths[column] * char_w + pad * 2

        y += height
        ax.plot([0, fig_w], [y, y], color=GRID, linewidth=0.8)

    return _save(fig, path)
