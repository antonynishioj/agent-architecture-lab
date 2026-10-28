# Blog notes

Material for writing the post. The illustrated draft is
[`blog/how-many-agents.docx`](blog/how-many-agents.docx). It is regenerated with
`uv run agent-lab blog`, and its results sections fill in from the official run.
Edit the generated text in Word for voice and flow. If you change the experiment,
change [`src/agent_lab/blog/build.py`](../src/agent_lab/blog/build.py) too, so the
draft stays reproducible.

## Working title options

- How Many AI Agents Do You Actually Need?
- I Split One Job Across 1, 2, 3 and 4 AI Agents. Here's What Changed.
- Multi-Agent or Single Prompt? A Controlled Experiment on a Free API Key

## Outline (matches the draft)

1. **Hook.** Multi-agent hype, and every agent costs a call. The question is how many is enough.
2. **The setup.** Four roles; four groupings; only the grouping changes (Figure 1).
3. **Fairness.** Shared role specs, frozen evidence, context rule, separate judge (Figure 2).
4. **The benchmark.** Difficulty ladder and traps (Figure 3, table of examples).
5. **Measurement.** Rubric judge with key-point checklist, blind ranking, deterministic checks.
6. **The winner rule, decided in advance** (Figure 4).
7. **Free tier engineering.** Quotas, rate limiter, pause and resume, parallelism.
8. **LangGraph?** Not needed, and why a framework could even hurt here.
9. **Results.** Winner, leaderboard, quality vs cost, by tier, robustness, most revealing case.
10. **Limitations.**
11. **Reproduce and verify.**
12. **Takeaway.**

## Key talking points

- **The independent variable is only the grouping.** Most "multi-agent vs single agent"
  comparisons change the prompts too. Here the fact-checking text is byte-identical
  whether a specialist or a generalist does it.
- **Easy questions can't separate architectures.** The smoke test scored about 0.98
  across the board. Any claim that "4 agents are better" needs hard cases to back it.
- **Cost is not subtle.** In the smoke test, the 4-agent pipeline used about 6× the
  tokens and about 4× the latency of a single agent. Quality has to rise a lot to justify that.
- **Hand-offs lose information.** The writer in the 3- and 4-agent pipelines never sees
  the sources, only notes. Watch completeness and citations for this.
- **Two judges disagree sometimes.** In the smoke test the rubric judge rated all four
  answers about the same, but the blind ranking judge put the 1-agent answer last for using
  a term not in the sources. Use concrete examples like this in the post.
- **Pre-registration matters.** "The smallest team that is not measurably worse than
  the best" was fixed before the run. Without it, you can make any architecture win.
- **Everything is verifiable.** Readers can recompute every number, or replay every call
  offline, from the committed run folder.

## The LangGraph / LangChain question

Short answer for the post: *not required, and deliberately not used.*

- The architectures are linear chains: research → check → critique → write. A for-loop is enough.
- An experiment must control everything except the variable. Frameworks add their own
  system prompts, retries, output parsers and memory, which are invisible confounds.
- Token accounting and exact prompts are easier to audit in plain code.
- Where LangGraph does help: branching, cycles (reflection or debate loops),
  persistence or checkpointing, human-in-the-loop. These are natural follow-up experiments.

## Screenshots to take for the post

1. Home page: the four architecture cards and the "how the winner is chosen" section.
2. Benchmark page with the 12 cases and the estimate panel.
3. Run page **during** the run: live progress feed with agents finishing.
4. Results: the winner banner and leaderboard.
5. Charts: quality vs cost and quality by difficulty.
6. Drill-down on a hard or adversarial case: answers side by side, with one trap violation visible.
7. An expanded **agent trace** for the 4-agent pipeline (shows the notes passed between agents).

## Numbers to quote (fill in after the official run)

Official run `c6f6d5e938`. The interpretation lives in
[`blog/findings.md`](blog/findings.md).

| Number | Value | Source |
|---|---|---|
| Winner | **1-agent** | `summary.json → winner.winner` |
| Best raw quality | 4-agent, 0.983 (1-agent 0.981, 3-agent 0.982, 2-agent 0.976) | `winner.best_quality` |
| Largest gap to best | 0.007 (2-agent), CI −0.002 to 0.014 | `winner.comparisons` |
| Token multiple, 4-agent vs 1-agent | 5.9× (6,411 vs 1,089) | `architectures[].total_tokens` |
| Latency multiple, 4-agent vs 1-agent | 5.0× (25.9 s vs 5.2 s) | `architectures[].latency_s` |
| Paid-tier cost per answer | $0.00053 vs $0.0036 (6.8×) | `estimated_cost_usd` |
| Trap violations | 0 of 144 answers | `trap_violation_rate` |
| Blind side-by-side wins | 4-agent 44%, 1-agent 31%, 2-agent 14%, 3-agent 11% | `win_rate` |
| Tier with the biggest gap | hard: 1-agent best (0.964 vs ≤0.947) | `by_difficulty` |
| 2-agent answers leaking the internal critique | 18 of 36 | `agent-lab findings` |
| Helios "≥7B" fact kept | 1-agent 2/3, pipelines 0/9 | `agent-lab findings` |
| Wall time | 45 minutes | manifest |
| Total cost | $0 (free tier) | |

## Follow-up experiments (good "what's next" section)

- Debate or voting topologies instead of linear chains.
- Reflection loops: the writer revises after the critic, with N rounds.
- A bigger or smaller generator. Does decomposition help weaker models more?
- Real web evidence (custom cases) instead of curated sources.
- Human ratings on a subset to calibrate the LLM judge.

## Publishing on Medium

The Word file is laid out for Medium: a title and subtitle, two heading sizes, no
tables (they are rendered as images), quotes instead of shaded boxes, and real links.

1. In Medium, **New story**. Paste the title into the title field and the first
   paragraph (the subtitle) into the subtitle line (select it, then the small "T").
2. Copy the rest of the document from Word and paste it in. Headings, bold, lists,
   quotes and links usually survive. **Images usually don't.**
3. Upload the images from [`blog/medium/`](blog/medium/) in numbered order. Each one
   goes where its caption appears, and [`IMAGES.md`](blog/medium/IMAGES.md) lists
   every caption. Use the cover (`01-…`) as the story's featured image.
4. Select the monospace command lines near the end and press ``` to turn them into a
   code block.
5. Suggested tags (Medium allows 5): `AI Agents`, `LLM`, `Multi Agent Systems`,
   `Machine Learning`, `Software Engineering`.
6. Image rights: the cover is AI-generated (its caption says so, as Medium asks).
   Make sure you have the rights to the "thinking" illustration. If it came from a
   stock site, credit it the way its licence requires.
