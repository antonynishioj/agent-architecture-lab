# Experiment design

This document was written **before** the official run. The winner rule in
[`analysis/winner.py`](../src/agent_lab/analysis/winner.py) implements exactly
what is described here. If you change the rule after seeing results, say so in the
write-up.

## Research question

> For evidence-based research answers, how many LLM agents are needed before
> adding another one stops improving quality enough to justify its cost?

## Hypotheses

| | Hypothesis | What would support it |
|---|---|---|
| H1 | On **easy** cases, one agent is as good as a team. | No architecture is significantly better than 1-agent in the easy tier. |
| H2 | Dedicated fact-checking and critique help most on **hard** and **adversarial** cases (conflicts, traps, missing evidence). | The gap between multi-agent and 1-agent grows with difficulty; trap violations fall with more agents. |
| H3 | Hand-offs lose information. Agents that see only notes (critic, writer) can drop facts or citations. | Completeness or citation quality falls for architectures where the writer is isolated (3- and 4-agent). |
| H4 | Cost grows roughly linearly with agent count, but quality does not. | Tokens and latency rise steadily; the Quality Index flattens after 2 agents. |

## Variables

**Independent variable:** how the four roles are grouped into agents (1, 2, 3 or 4 LLM calls).

**Controlled:**

| Control | How |
|---|---|
| Role instructions | Defined once in `roles.py`. Every agent prompt is assembled from the same text. |
| Evidence | Frozen sources per case (`data/benchmark/research.json`); no live search during runs. |
| Context rule | Agents doing research or fact-checking get the sources. Every agent gets all earlier agents' notes. |
| Model and sampling | One generator model, temperature 0.3, seed = 1000 + trial number. |
| Output format | Final answers cite sources as `[S1]`; the writer role always produces the final answer. |
| Judge | A different, stronger model (temperature 0, fixed seed), blind to the architecture. |

**Measured (dependent variables):**

- Rubric scores (0–1): answer relevancy, completeness (from the key-point checklist),
  faithfulness, citation quality, uncertainty handling, overall quality.
- **Quality Index** = the unweighted mean of the six rubric scores.
- Blind ranking: win rate and mean rank when all answers are compared side by side.
- Trap violations and unsupported claims (from the judge).
- Citation validity and coverage (deterministic regex checks).
- Calls, input/output/thinking tokens, latency, and estimated cost at paid-tier prices.

## Unit of analysis

Each (case, trial) pair is one unit. Trials within a case are **averaged first**,
so each case counts once. The 12 cases are the independent observations used for
confidence intervals. This avoids pretending 36 correlated trials are 36
independent data points.

## Winner rule (pre-registered)

1. Compute each architecture's mean Quality Index across cases.
2. **Best** = the highest mean (ties go to fewer agents).
3. For every other architecture, take the per-case difference (best − it) and
   compute a **paired bootstrap 95% CI** (2,000 resamples, fixed seed).
   It is **as good as the best** if the CI includes 0 **or** the mean gap is below
   **0.02**.
4. **Winner** = the architecture with the fewest mean tokens per answer among those
   that are as good as the best. Ties go to fewer agents.

Also reported, without changing the headline:

- The same rule within each difficulty tier (3 cases each, so treat it as indicative).
- Robustness checks: "trust first" weights (faithfulness ×2, uncertainty ×1.5),
  overall-quality only, and the blind-ranking order.

## Procedure

1. Run the smoke test (1 case × 1 trial) to check the pipeline.
2. Run the official benchmark: 12 cases × 3 trials × 4 architectures.
   If it pauses on quota, resume the next day; the cache makes resumption free.
3. Commit `results/runs/<run>/`.
4. Verify with `uv run agent-lab report <run>` and `uv run agent-lab replay <run>`.
5. Rebuild the blog with `uv run agent-lab blog`.

## Threats to validity

| Threat | Mitigation | Residual risk |
|---|---|---|
| LLM-judge bias (length, style, self-preference) | A different, stronger judge model; blind scoring; key-point checklist; "do not reward length" instruction; a second, comparative judge | Judges still prefer some styles. Spot-check answers in the UI drill-down. |
| Position bias in the ranking judge | Labels A–D shuffled with a seed per (case, trial) | Small with 36 rankings. |
| Too few cases | Confidence intervals and a paired test; the conclusion is "not significantly different", never "equal" | Subtle differences go undetected. |
| Synthetic sources | They make traps precise | Real web pages are messier. Custom cases with Tavily give real-world spot checks. |
| One model family | Documented | Results may not transfer to much larger or smaller models. |
| Latency measured under parallel load | All architectures run concurrently under the same conditions | Absolute latencies depend on free-tier load that day. |
| Free-tier data use | Benchmark content is synthetic and public | Do not put private data in custom cases on the free tier. |
