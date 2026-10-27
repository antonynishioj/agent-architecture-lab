"""
Builds docs/blog/how-many-agents.docx, formatted for pasting into Medium.

Medium's editor has a title, two heading sizes, paragraphs, bullet lists,
quotes, images with captions and links, but no tables or shaded boxes.
So tables are rendered as images, and every image is also exported in
order to docs/blog/medium/ (pasting from Word into Medium often drops
images, so they can be uploaded one by one).

Narrative sections are fixed text. Every number in the results sections
is read from the run's summary, and the run-specific interpretation comes
from docs/blog/findings.md. With no qualifying run, the results sections
are marked "pending" rather than filled with made-up numbers.
"""

import re
import shutil
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from agent_lab.analysis.report import build_summary
from agent_lab.blog import figures
from agent_lab.blog.findings_doc import load_findings
from agent_lab.experiments.benchmark import BenchmarkLoader
from agent_lab.settings import load_settings


REPOSITORY = "https://github.com/antonynishioj/agent-architecture-lab"

INK = RGBColor(0x0B, 0x0B, 0x0B)
INK_2 = RGBColor(0x52, 0x51, 0x4E)

INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\(https?://[^)]+\))")


# ---------------------------------------------------------------------------
# docx helpers


def _hyperlink(paragraph, text: str, url: str, size: float | None = None) -> None:
    relationship = paragraph.part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), relationship)

    run = OxmlElement("w:r")
    properties = OxmlElement("w:rPr")

    color = OxmlElement("w:color")
    color.set(qn("w:val"), "1A5FB4")
    properties.append(color)

    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    properties.append(underline)

    if size:
        font_size = OxmlElement("w:sz")
        font_size.set(qn("w:val"), str(int(size * 2)))
        properties.append(font_size)

    run.append(properties)

    text_element = OxmlElement("w:t")
    text_element.text = text
    text_element.set(qn("xml:space"), "preserve")
    run.append(text_element)

    link.append(run)
    paragraph._p.append(link)


def _runs(paragraph, text: str, size: float | None = None, color: RGBColor | None = None, italic: bool = False) -> None:
    """Add text with **bold**, `code` and [link](url) spans."""

    for part in INLINE.split(text):
        if not part:
            continue

        link = re.fullmatch(r"\[([^\]]+)\]\((https?://[^)]+)\)", part)

        if link:
            _hyperlink(paragraph, link.group(1), link.group(2), size)
            continue

        if part.startswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
        else:
            run = paragraph.add_run(part)

        run.italic = italic

        if size:
            run.font.size = Pt(size)
        if color:
            run.font.color.rgb = color


class Post:
    def __init__(self, image_dir: Path, medium_dir: Path):
        self.doc = Document()
        self.image_dir = image_dir
        self.medium_dir = medium_dir
        self.images: list[tuple[str, str]] = []

        section = self.doc.sections[0]
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.left_margin = section.right_margin = Cm(2.4)
        section.top_margin = section.bottom_margin = Cm(2.0)

        styles = self.doc.styles
        styles["Normal"].font.name = "Georgia"
        styles["Normal"].font.size = Pt(11.5)
        styles["Normal"].paragraph_format.space_after = Pt(10)
        styles["Normal"].paragraph_format.line_spacing = 1.3

        # Medium has two heading sizes: Heading 1 (large) and Heading 2 (small).
        for name, size in (("Heading 1", 19), ("Heading 2", 14.5)):
            style = styles[name]
            style.font.name = "Arial"
            style.font.size = Pt(size)
            style.font.color.rgb = INK
            style.paragraph_format.space_before = Pt(20 if name == "Heading 1" else 14)

        if self.medium_dir.exists():
            shutil.rmtree(self.medium_dir)
        self.medium_dir.mkdir(parents=True)

    def title(self, text: str, subtitle: str) -> None:
        heading = self.doc.add_heading(text, level=0)
        heading.runs[0].font.size = Pt(30)
        heading.runs[0].font.name = "Arial"
        heading.runs[0].font.color.rgb = INK

        paragraph = self.doc.add_paragraph()
        _runs(paragraph, subtitle, size=14, color=INK_2)

    def h1(self, text: str) -> None:
        self.doc.add_heading(text, level=1)

    def h2(self, text: str) -> None:
        self.doc.add_heading(text, level=2)

    def p(self, text: str) -> None:
        _runs(self.doc.add_paragraph(), text)

    def quote(self, text: str) -> None:
        _runs(self.doc.add_paragraph(style="Quote"), text, italic=True)

    def bullets(self, items: list[str]) -> None:
        for item in items:
            _runs(self.doc.add_paragraph(style="List Bullet"), item)

    def code(self, lines: list[str]) -> None:
        # Monospace lines; in Medium, select them and press ``` for a code block.
        for index, line in enumerate(lines):
            paragraph = self.doc.add_paragraph()
            paragraph.paragraph_format.space_after = Pt(0 if index < len(lines) - 1 else 10)
            run = paragraph.add_run(line)
            run.font.name = "Consolas"
            run.font.size = Pt(10)

    def figure(self, path: Path, caption: str, width_cm: float | None = None) -> None:
        if width_cm is None:
            from PIL import Image

            with Image.open(path) as image:
                width, height = image.size

            # Keep tall screenshots from filling more than about a page.
            width_cm = 16.2 if height / width < 0.9 else min(16.2, 19.0 * width / height)

        self.doc.add_picture(str(path), width=Cm(width_cm))
        self.doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

        if caption:
            paragraph = self.doc.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _runs(paragraph, caption, size=9.5, color=INK_2)

        exported = f"{len(self.images) + 1:02d}-{path.stem}.png"
        shutil.copy(path, self.medium_dir / exported)
        self.images.append((exported, caption))

    def table(self, header: list[str], rows: list[list[str]], name: str, caption: str, highlight: int | None = None) -> None:
        path = figures.table_image(header, rows, self.image_dir / f"{name}.png", highlight=highlight)
        self.figure(path, caption)

    def save(self, path: Path) -> Path:
        # python-docx's default template omits the required w:percent
        # attribute on <w:zoom>, which fails strict schema validation.
        for zoom in self.doc.settings.element.iter(qn("w:zoom")):
            zoom.set(qn("w:percent"), "100")

        path.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(path)

        lines = [
            "# Images for Medium, in order",
            "",
            "Pasting from Word into Medium often drops images. Upload each one where it appears",
            "in the document and paste its caption underneath. This folder is regenerated by",
            "`uv run agent-lab blog`.",
            "",
        ]
        lines += [
            f"{index}. `{name}`: {caption or '(no caption)'}"
            for index, (name, caption) in enumerate(self.images, start=1)
        ]
        (self.medium_dir / "IMAGES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        return path


def render_blocks(post: Post, blocks: list, table_prefix: str) -> None:
    tables = 0
    heading = ""

    for block in blocks:
        kind = block[0]

        if kind == "h3":
            heading = block[1]
            post.h2(block[1])
        elif kind == "p":
            post.p(block[1])
        elif kind == "bullets":
            post.bullets(block[1])
        elif kind == "table":
            tables += 1
            # A table's caption is the heading it sits under.
            post.table(block[1], block[2], f"{table_prefix}-table{tables}", heading)
        elif kind == "image" and block[2].exists():
            post.figure(block[2], block[1])


def screenshot(post: Post, directory: Path, name: str, caption: str) -> None:
    path = directory / f"{name}.png"

    if path.exists():
        post.figure(path, caption)


# ---------------------------------------------------------------------------
# Result helpers


def is_publishable(summary: dict | None) -> bool:
    """Only a run covering every difficulty tier counts as a result."""

    return bool(
        summary
        and summary["winner"]["winner"]
        and len(summary["by_difficulty"]) >= 4
        and summary["config"]["units_completed"] >= 12
    )


def _fmt(value, digits=3) -> str:
    return "–" if value is None else f"{value:.{digits}f}"


def _signed(value) -> str:
    return "–" if value is None else f"{value:.3f}".replace("-", "−")


# ---------------------------------------------------------------------------
# The post


def build_blog(run_path: Path | None, output: Path) -> Path:
    settings = load_settings()
    loader = BenchmarkLoader(settings.benchmark_file, settings.research_file)
    cases = loader.load_all()

    blog_dir = output.parent
    image_dir = blog_dir / "images"
    shots = blog_dir / "screenshots"

    summary = build_summary(run_path) if run_path else None
    publishable = is_publishable(summary)

    findings = (load_findings(blog_dir / "findings.md", summary["run_id"]) if publishable else None) or {}

    if publishable:
        generator_model = summary["config"]["generator_model"]
        judge_model = summary["config"]["judge_model"]
        run_id = summary["run_id"]
    else:
        generator_model = settings.generator_model
        judge_model = settings.judge_model
        run_id = "<run>"

    post = Post(image_dir, blog_dir / "medium")

    post.title(
        "How Many AI Agents Do You Actually Need?",
        "I split the same research task across one, two, three and four AI agents, "
        "judged every answer blind, and ran the whole experiment on a free Gemini API key.",
    )

    cover = image_dir / "cover-tug-of-war.png"
    if cover.exists():
        post.figure(cover, "One agent against a team of four. (Image generated with Gemini.)")

    # --- The story --------------------------------------------------------
    post.h1("Why I ran this experiment")
    post.p(
        "I build LLM products at my company. To be precise, we build multi-agent "
        "applications. When I started as a fresher, one question kept bothering me: "
        "why do we need multiple agents in the first place? If every agent calls the "
        "same model through the same API, how different can the results really be?"
    )

    thinking = image_dir / "thinking.png"
    if thinking.exists():
        post.figure(thinking, "The question I never asked out loud.")

    post.p(
        "I understand giving each agent its own prompt. It keeps the project's folders "
        "and files clean and easy to navigate. But going multi-agent also pulls in extra "
        "frameworks and protocols for agents to talk to each other and to their tools: "
        "A2A, MCP, LangGraph and so on. Each one is more to learn, more to maintain, and "
        "more that can break."
    )
    post.p(
        "I never asked anyone about it. I assumed that if the whole world was doing it, it "
        "must be the right way. But I don't accept things that easily; I want proof before I "
        "believe something. So I built an experimental framework to measure the quality, "
        "cost, latency and reliability of different agent architectures, to answer one "
        "question: **how many agents do we actually need?** The task is a research system: "
        "answering questions from a set of sources, with citations."
    )
    post.p(
        "To be clear, every architecture, protocol and library has its own use cases, and I'm "
        "not saying any of them is bad. But for linear chains of agent calls and simple "
        "applications, I wanted to see which architecture actually earns its place. Here is "
        "what I found."
    )

    # --- TL;DR ------------------------------------------------------------
    post.h1("TL;DR")

    if publishable:
        tldr = [item for block in findings.get("TL;DR", []) if block[0] == "bullets" for item in block[1]]

        if not tldr:
            winner = summary["winner"]
            tldr = [f"**Winner: {winner['winner']}.** {winner['explanation']}"]

        post.bullets(tldr)
    else:
        post.quote(
            "[pending] The results fill in automatically from the official run. Run the benchmark "
            "from the UI, then run `uv run agent-lab blog` again. No numbers here are invented."
        )

    # --- Design -----------------------------------------------------------
    post.h1("The setup: same work, different team sizes")
    post.p("Every architecture does the same four jobs, in the same order:")
    post.bullets(
        [
            "**Research:** pull the relevant facts out of the sources, tagged with source IDs.",
            "**Fact-checking:** mark each claim as supported, partly supported, unsupported or contradicted, and spot conflicts and false premises.",
            "**Critique:** decide whether the evidence really answers the question, and which caveats are needed.",
            "**Writing:** produce the final, cited answer for the user.",
        ]
    )
    post.p("The only thing that changes is how those jobs are grouped into agents, that is, into separate LLM calls:")
    post.figure(
        figures.architectures_diagram(image_dir / "fig1_architectures.png"),
        "The four architectures. Every one covers all four jobs; only the grouping changes.",
    )

    post.h2("Keeping the comparison fair")
    post.p(
        "A comparison like this is easy to rig by accident. If the 4-agent prompts are written "
        "more carefully than the 1-agent prompt, you measure prompt quality, not team size. So "
        "everything except the number of agents is held constant:"
    )
    post.bullets(
        [
            "**One set of instructions per job.** Each job's instructions are written once in code. "
            "An agent's prompt is built by stacking the instructions for its jobs, so the fact-checking "
            "text is word-for-word identical whether a specialist or a generalist does the checking.",
            "**Frozen evidence.** Every architecture answers from the same sources. Nobody searches "
            "the web mid-run, so retrieval luck can't decide the result.",
            "**One context rule.** Agents that research or fact-check see the raw sources. Every agent "
            "sees the notes of all earlier agents. The critic and the writer work from notes, as they "
            "would in a real pipeline.",
            "**Same model and settings.** One generator model, temperature 0.3, a fixed seed per trial, "
            "and three trials per question.",
            f"**A different judge.** Answers are scored by a different, newer model ({judge_model}) "
            f"than the one that wrote them ({generator_model}), so the judge is less likely to favour "
            "its own writing style.",
        ]
    )
    post.figure(
        figures.experiment_flow_diagram(image_dir / "fig2_experiment_flow.png", generator_model, judge_model),
        "One question through the pipeline: four architectures answer in parallel, and three kinds of evaluation feed the statistics.",
    )

    # --- Benchmark --------------------------------------------------------
    post.h1("The benchmark: from easy lookups to traps")
    post.p(
        "If every question is easy, every architecture scores about 0.98 and you learn nothing. "
        "The interesting question is whether specialist fact-checkers and critics earn their keep "
        "**when the evidence is messy**. So the twelve questions climb a difficulty ladder:"
    )
    post.figure(
        figures.difficulty_ladder(image_dir / "fig3_difficulty.png", cases),
        "Twelve questions in four tiers. The hard and adversarial tiers contain deliberate traps.",
    )
    post.table(
        ["Tier", "Example question", "The trap"],
        [
            ["Easy", "What is a vector database used for?", "None. A baseline where one agent should be enough."],
            ["Medium", "When should a team fine-tune instead of using RAG?", "Must separate two kinds of need across five sources."],
            ["Hard", "What will 2M chat requests per month cost?", "An outdated 2023 price list, plus two discounts that look applicable but aren't."],
            ["Hard", "How much did Northwind's assistant cut resolution time?", "A 40% press-release figure against a 22% independent audit."],
            ["Adversarial", "How many parameters does Orion Assist have?", "The honest answer is \"not disclosed\"; a forum guess of 70B is bait."],
            ["Adversarial", "Why did Lumen 3.0 deprecate garbage collection?", "It didn't. The question has a false premise."],
        ],
        "table-benchmark-examples",
        "Examples from the benchmark.",
    )
    post.p(
        "The sources are synthetic (example.com URLs), so conflicts, outdated facts and planted "
        "errors are exactly controlled. Each question also lists the **key points** a complete "
        "answer must contain and the **trap claims** it must not make, which turns vague "
        "judgments into checklists."
    )

    # --- Measurement ------------------------------------------------------
    post.h1("How the answers are scored")
    post.p("Each answer is evaluated in three independent ways:")
    post.bullets(
        [
            "**A rubric judge** scores six dimensions from 0 to 1: relevancy, completeness, faithfulness "
            "to the sources, citation quality, handling of uncertainty, and overall quality. Completeness "
            "is calculated from the key-point checklist (covered = 1, partial = 0.5), not taken from a gut "
            "feeling. The judge never sees which architecture wrote the answer.",
            "**A blind ranking judge** sees all four answers side by side, shuffled and labelled A–D, and "
            "ranks them. This catches differences that absolute scores compress.",
            "**Automatic checks** that need no LLM: citations that point to sources that don't exist, "
            "citation coverage, answer length, tokens, latency, and cost at paid-tier prices.",
        ]
    )
    post.p("The **Quality Index** is the plain average of the six rubric scores.")

    post.h2("Deciding the winner before seeing the data")
    post.p(
        "If you choose the winning rule after seeing the results, you can make any architecture "
        "win. So the rule was written into the code before the official run:"
    )
    post.figure(
        figures.winner_rule_diagram(image_dir / "fig4_winner_rule.png"),
        "The winner is the smallest team that is not measurably worse than the best.",
    )
    post.p(
        "Step 3 compares architectures **question by question** (a paired bootstrap), which removes "
        "the noise from some questions simply being harder than others. An architecture counts as tied "
        "with the best if the 95% confidence interval of its gap includes zero, or the gap is below "
        "0.02 on the 0–1 scale."
    )

    # --- Free tier --------------------------------------------------------
    post.h1("Running it on a free Gemini key")
    post.p(
        "The whole experiment runs on the Gemini API free tier. A full run is 12 questions × 3 trials. "
        "Each one needs 10 generator calls (1 + 2 + 3 + 4) and 5 judge calls: about 360 generator and "
        "180 judge requests in total. Free-tier quotas are counted per model, so using a different model "
        "for the judge gives the run two separate daily budgets."
    )
    post.bullets(
        [
            "A **rate limiter** keeps requests under the per-minute cap.",
            "**Retries with backoff** handle temporary errors and dropped connections.",
            "If the **daily quota runs out, the run pauses** instead of crashing. Resuming the next day reuses a response cache, so no call is paid for twice.",
            "The four architectures run **in parallel** for each question, which made the official run take 45 minutes.",
        ]
    )
    post.p(
        "**A lesson learned the hard way:** my first official attempt used a full Flash model as the "
        "judge and paused after 2 of 36 units. On the free tier, Flash models currently allow only about "
        "20 requests per day, while Flash-Lite models allow about 500. Switching to two different "
        "Flash-Lite models (an older one answering, a newer one judging) fixed it. Check your real "
        "per-model limits at aistudio.google.com/rate-limit before planning a run."
    )

    if publishable:
        post.h2("The lab")
        post.p(
            "Everything runs from a small local web app: pick the questions, check the request budget, "
            "watch each agent finish live, then explore every answer side by side."
        )
        screenshot(post, shots, "ui_home", "The lab's home page, with the free-tier usage after the official run.")
        screenshot(post, shots, "ui_benchmark_cases", "Choosing benchmark questions by difficulty tier.")

    post.h2("Did I need LangGraph or LangChain?")
    post.p(
        "No, and for this experiment I'd argue against them. The pipelines are straight sequences of "
        "calls, so a for-loop is the whole orchestration layer. Plain Python keeps every prompt visible "
        "and every token counted, and guarantees that no framework-added prompts, retries or memory "
        "differ between architectures. Graph frameworks earn their place when you need branching, loops, "
        "persistence or human-in-the-loop steps. None of those were being tested here."
    )

    # --- Results ----------------------------------------------------------
    post.h1("Results")

    if publishable:
        _results_sections(post, summary, image_dir, findings, shots)
    else:
        post.quote(
            "[pending] This section is generated from the official run's summary.json: the winner, the "
            "leaderboard, quality against cost, quality by difficulty, and what happened inside the pipelines."
        )

    # --- Limitations ------------------------------------------------------
    post.h1("What this experiment can and can't tell you")

    specific = [item for block in findings.get("Limitations", []) if block[0] == "bullets" for item in block[1]]

    post.bullets(
        specific
        + [
            "**One task.** Answering questions from sources. Tasks with tools, code execution or long-horizon "
            "planning may reward specialisation differently.",
            "**Twelve questions.** Enough to detect large differences, not subtle ones; the confidence "
            "intervals show how much to trust each gap.",
            "**Linear pipelines only.** No debate, voting or reflection loops. Those deserve their own experiment.",
            "**Synthetic sources.** Precise control over the traps, but cleaner than real web pages.",
        ]
    )

    # --- Conclusion -------------------------------------------------------
    post.h1("The takeaway")

    if findings.get("Takeaway"):
        render_blocks(post, findings["Takeaway"], "takeaway")
    elif not publishable:
        post.p("[pending] The conclusion is written after the official run.")

    post.p(
        "I believe that if something can be made simpler, it is almost always better to keep it simple "
        "than to make it complex just to look impressive. Simple designs are easier to debug, easier to "
        "hand over to teammates, and cheaper to run. What matters is checking the trade-offs, and that is "
        "exactly what this experiment set out to do."
    )
    post.p(
        "I'm not saying a single agent is always the better architecture. But for simple tasks like the "
        "one in this experiment, my results suggest it is. At the end of the day, I just wanted to try it "
        "for myself, and this is my experience and my results."
    )

    # --- Reproduce --------------------------------------------------------
    post.h2("Try it or check my numbers")
    post.p(
        f"All the code, the benchmark, and every prompt and model response are on GitHub: "
        f"[{REPOSITORY.removeprefix('https://')}]({REPOSITORY}). You can check every number without an "
        "API key:"
    )
    post.code(
        [
            f"git clone {REPOSITORY}",
            "cd agent-architecture-lab",
            "uv sync",
            f"uv run agent-lab report {run_id}    # recompute every statistic from the raw files",
            f"uv run agent-lab replay {run_id}    # re-run every answer from the recorded responses",
        ]
    )
    post.p(
        "To run it yourself, get a free key from Google AI Studio, put it in `.env`, start the backend "
        "with `uv run agent-lab serve`, and start the UI with `npm run dev` in the frontend folder."
    )

    return post.save(output)


def _results_sections(post: Post, summary: dict, image_dir: Path, findings: dict, shots: Path) -> None:
    config = summary["config"]
    winner = summary["winner"]

    post.p(
        f"The official run: {config['cases_planned']} questions × {config['trials']} trials × "
        f"{len(config['architectures'])} architectures, "
        f"{config['units_completed'] * len(config['architectures'])} answers in total, written by "
        f"`{config['generator_model']}` and judged by `{config['judge_model']}`."
    )

    post.quote(f"Winner: {winner['winner']}. {winner['explanation']}")

    rows = []
    highlight = None

    for index, row in enumerate(summary["architectures"]):
        if row["architecture"] == winner["winner"]:
            highlight = index
        rows.append(
            [
                row["architecture"],
                f"{_fmt(row['quality_index'])} ({_fmt(row['quality_ci_low'], 2)}–{_fmt(row['quality_ci_high'], 2)})",
                _fmt(row["dimensions"]["faithfulness"], 2),
                "–" if row["win_rate"] is None else f"{row['win_rate']:.0%}",
                "–" if row["trap_violation_rate"] is None else f"{row['trap_violation_rate']:.0%}",
                "–" if row["total_tokens"] is None else f"{row['total_tokens']:,.0f}",
                "–" if row["latency_s"] is None else f"{row['latency_s']:.1f} s",
            ]
        )

    post.table(
        ["Architecture", "Quality Index (95% CI)", "Faithfulness", "Blind wins", "Trap violations", "Tokens / answer", "Latency"],
        rows,
        "table-leaderboard",
        "The leaderboard. Blind wins: how often the side-by-side judge ranked that architecture first.",
        highlight=highlight,
    )

    post.figure(
        figures.quality_interval_chart(summary, image_dir / "fig5_quality.png"),
        "Mean Quality Index with 95% confidence intervals. Note the narrow axis: all four intervals overlap heavily.",
    )

    comparisons = winner["comparisons"]
    if comparisons:
        tied = [c for c in comparisons if c["as_good_as_best"]]
        details = "; ".join(
            f"{c['architecture']} {_signed(c['diff_mean'])} (CI {_signed(c['ci_low'])} to {_signed(c['ci_high'])})"
            for c in comparisons
        )
        verdict = (
            "Every one of them counts as tied with the best."
            if len(tied) == len(comparisons)
            else f"{len(tied)} of {len(comparisons)} count as tied with the best."
        )
        post.p(
            f"Compared question by question with the best scorer ({winner['best_quality']}), the gaps were: "
            f"{details}. {verdict}"
        )

    post.figure(
        figures.tradeoff_chart(summary, image_dir / "fig6_tradeoff.png"),
        "Quality against tokens per answer. Quality stays flat while cost climbs with every agent.",
    )

    screenshot(post, shots, "ui_winner", "The run page in the lab: the winner and the rule that picked it.")
    screenshot(post, shots, "ui_charts", "The results dashboard in the lab UI.")

    post.h2("Does difficulty change the answer?")
    post.figure(
        figures.tier_chart(summary, image_dir / "fig7_tiers.png"),
        "Quality by difficulty tier. The axis spans only about 0.93–1.00, and each tier has just 3 questions.",
    )

    tiers = summary["by_difficulty"]
    best = ", ".join(f"{tier} → {data['best_quality']}" for tier, data in tiers.items())
    winners = {data["winner"] for data in tiers.values()}

    if len(winners) == 1:
        rule = (
            f"Applying the same winner rule within each tier picks **{winners.pop()} every time**, because "
            "the gaps are small and it is the cheapest."
        )
    else:
        rule = "The tier winners under the same rule: " + ", ".join(
            f"{tier} → {data['winner']}" for tier, data in tiers.items()
        ) + "."

    post.p(f"The highest-scoring architecture per tier was: {best}. {rule}")

    schemes = {
        scheme: data["winner"]
        for scheme, data in summary["sensitivity"].items()
        if data["winner"]
    }

    if schemes and len(set(schemes.values())) == 1:
        post.p(
            "Changing how the six scores are weighted (for example, doubling the weight of faithfulness) "
            f"doesn't change the verdict: the winner is still {next(iter(schemes.values()))}."
        )

    if findings.get("Findings"):
        post.h1("What actually happened inside the pipelines")
        render_blocks(post, findings["Findings"], "findings")
