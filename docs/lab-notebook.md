# Lab notebook

A dated log of what you did and what you noticed. These notes become the most
authentic parts of the blog: surprises, failed ideas, things you changed and why.
Keep entries short and honest.

---

## 2026-10-26: v2 framework and smoke test

**Did:** Rebuilt the framework (shared role specs, 12-case benchmark, blind judges,
winner rule, free-tier handling, UI). Ran a smoke test: `rag-benefits-001`, 1 trial.

**Observed:**
- All four architectures scored about 0.98 on the easy case. There was no real difference,
  which is why the benchmark needs hard and adversarial tiers.
- Tokens per answer: 1-agent ≈ 1.1K, 2-agent ≈ 3.0K, 3-agent ≈ 5.2K, 4-agent ≈ 6.2K
  (about 6× from 1 to 4 agents).
- Latency: 22 s vs 57 s vs 87 s vs 86 s. Free-tier calls take 15–45 s each.
- The blind ranking judge ranked the **1-agent answer last**, because it used the word
  "hallucinations", which is not in the sources (outside terminology). The rubric
  judge did not penalise it. This is an example of the two judges disagreeing.

**Changed:** Architectures now run in parallel within a case (a full run takes about 1.5 h instead of about 4 h).

---

## 2026-10-26: first official attempt hit the judge's quota

**Did:** Started the official run (12 × 3) with generator `gemini-3.5-flash-lite`
and judge `gemini-3.5-flash`.

**Observed:** It paused after **2 of 36** case-trials with "daily free-tier quota
exhausted for gemini-3.5-flash". The generator still had quota. Free **Flash**
models allow only ~20 requests/day; **Flash-Lite** models allow ~500. The judge
needs ~180 calls per run, so it was the bottleneck.

**Changed (and why):** Generator → `gemini-3.1-flash-lite`, judge →
`gemini-3.5-flash-lite`. Each has its own ~500/day quota. The judge is the newer
model, and they are still different models (less self-preference bias). The paused
run `6786aa8b98` is abandoned. A run can't switch models halfway (the engine now
refuses), so the official run restarts from scratch.

**Lesson for the blog:** check per-model free limits *before* designing the run.
The cheapest-looking plan was blocked by the judge, not the agents.

**Smoke test on the new pair** (`617b9de596`, `vector-db-purpose-002`): calls take
2–6 s (against 15–45 s before). The first attempt lost 3 architectures to "Server
disconnected" network errors. Two fixes: transport errors are now retried, and a
unit with any failed architecture or judgement is marked failed (so Resume retries
it) instead of being saved with gaps. After resuming: all four scored ≈0.997 (an easy
case again), and tokens were 1.0K / 2.4K / 4.3K / 5.8K. The blind ranking put
**1-agent first** this time.

---

## 2026-10-27: official run

**Run ID:** `c6f6d5e938` (`results/runs/20261027T025551Z_benchmark_c6f6d5e938`)
**Config:** 12 cases × 3 trials · generator `gemini-3.1-flash-lite` · judge
`gemini-3.5-flash-lite` · prompts `8b075615a0f0fe7b` · 45 minutes (02:55–03:40 UTC)

**Verified:** `agent-lab report` matches the raw files, and `agent-lab replay` reproduced
all 36 case-trials offline.

**Observed:**
- **Winner: 1-agent.** Quality Index 0.976–0.983 for all four, with every CI overlapping;
  the best was 4-agent (0.983). 1-agent uses 1,089 tokens per answer against 6,411 (5.9×)
  and 5.2 s against 25.9 s.
- **Tier that differed most:** hard. 1-agent was best (0.964 vs 0.937–0.947), almost entirely
  because of `distractor-study-009`.
- **Memorable answers:**
  - Helios: every pipeline's Research agent narrowed the question to "<3B" and dropped
    the "benefits only at ≥7B" fact (kept 0/9 times, against 2/3 for one agent).
  - 2-agent: the critic+writer agent pasted its "### Critique" section into the
    final answer in 18/36 answers. No other architecture ever did this.
- **Trap violations:** none, in all 144 answers. Faithfulness was 1.00 everywhere: a
  ceiling effect.
- **Judges disagreed:** the side-by-side judge picked 4-agent first in 44% of comparisons
  (against 31% for 1-agent), while the rubric scores were tied. On Helios trial 1, the rubric
  favoured 1-agent and the ranker put 4-agent first.
- **Where the team helped:** `false-premise-011`. 4-agent explained the origin of the
  false claim 3/3 times; 1-agent 1/3.

**Surprises:** how well the single Flash-Lite call handled every trap, and that the
2-agent split (the "obvious" middle ground) was the worst on the side-by-side judge.

**Questions for a follow-up experiment:**
- A harder benchmark (real, messy web pages; longer source sets) to get off the ceiling.
- A weaker generator: does decomposition help small models more?
- Writers that also see the sources: does that remove the hand-off loss?
- Reflection loops (writer ↔ critic) instead of one-way pipelines.

All the qualitative counts above are reproduced by `uv run agent-lab findings c6f6d5e938`.

---

## Template

```
## YYYY-MM-DD: title

**Did:**
**Observed:**
**Changed (and why):**
**Next:**
```
