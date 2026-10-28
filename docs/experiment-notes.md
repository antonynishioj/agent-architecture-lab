# Experiment Notes

## Research Question

How many AI agents do we actually need for a research task?

## Hypothesis

Increasing agent specialization may improve answer quality and factual
reliability, but may also increase cost, latency, and system complexity.
The detailed, testable hypotheses (H1–H4) are in
[experiment-design.md](experiment-design.md).

## Architectures

1. Single Agent: research + fact-check + critique + writing in one call
2. Two Agents: (research + fact-check) → (critique + writing)
3. Three Agents: research → (fact-check + critique) → writing
4. Four Agents: research → fact-check → critique → writing

All four perform all four roles with identical role instructions. See
[architectures.md](architectures.md).

## Core Evaluation

- Answer Relevancy
- Completeness (key-point checklist)
- Faithfulness
- Citation Quality
- Uncertainty Handling (conflicts, missing evidence, false premises)
- Overall Quality
- Blind side-by-side ranking
- Cost, Latency, Token Usage, LLM Calls

## Status

- [x] v1 outline: four architectures, Gemini provider, single LLM judge
- [x] v2 framework: shared role specs, 12-case benchmark in four tiers, blind
      rubric + ranking judges, bootstrap statistics, winner rule, free-tier
      rate limiting and resume, committed and verifiable results, UI
- [x] Smoke test: 1 case × 1 trial (`results/runs/*_6bf7a549d7`)
- [x] First official attempt (`6786aa8b98`): paused at 2/36. Judge `gemini-3.5-flash`
      allows only ~20 free requests/day. Abandoned.
- [x] Switched to generator `gemini-3.1-flash-lite` + judge `gemini-3.5-flash-lite`
      (~500/day each)
- [x] Official run `c6f6d5e938`: 12 cases × 3 trials. **Winner: 1-agent**
      (all four tied on quality; 1-agent is ~6× cheaper)
- [x] Verified with `agent-lab report` and `agent-lab replay` (36/36 reproduced offline)
- [x] Blog rebuilt with results, findings and UI screenshots
- [ ] Commit `results/runs/` and `docs/blog/`, then publish

## Changes from v1 (and why)

| v1 | v2 | Why |
|---|---|---|
| Hand-written prompts per architecture | One role spec, assembled per agent | Prompt wording was a confound |
| Fact-checkers in 2/3/4-agent never saw the sources | Research and fact-check roles always see the sources | They were "checking" the brief against itself |
| 3 cases, one with no evidence | 12 cases with curated evidence, easy → adversarial | Easy cases cannot separate architectures |
| One judge call, one trial | Rubric judge + blind ranking judge + deterministic checks, 3 trials | Noise and single-judge bias |
| No winner rule | Pre-registered rule with a paired bootstrap | A "proper final answer" needs a rule fixed in advance |
| No rate limiting or retries | Rate limiter, backoff, quota pause, response cache | Free tier |
| Static UI mockup | Live benchmark and custom runs with results and drill-down | Usability |
