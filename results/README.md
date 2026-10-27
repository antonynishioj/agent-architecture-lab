# Results

Every experiment run is saved here and **committed to git**, so anyone can
check the conclusions without trusting the author.

```
results/runs/<UTC timestamp>_<type>_<run_id>/
  manifest.json     models, temperatures, seeds, git commit, benchmark and prompt fingerprints, progress
  cases.json        the exact questions and evidence used
  cases/*.json      one file per (case, trial): every answer, every agent's notes, every judge verdict
  llm_cache.jsonl   every prompt sent and every response received
  summary.json      aggregated statistics and the winner
  summary.csv       one row per architecture
  REPORT.md         human-readable report (renders on GitHub)
```

## How to verify a run

No API key is needed for either check.

```bash
uv sync
# 1. Recompute every statistic from the raw per-case files
uv run agent-lab report results/runs/<dir>
# -> VERIFIED: summary.json matches the raw case files

# 2. Re-execute the whole run offline from the recorded responses
uv run agent-lab replay results/runs/<dir>
# -> VERIFIED: replayed N case-trials offline ... reproduced every number
```

Check 1 shows that the published statistics follow from the raw data. Check 2 shows
that the raw data follows from the recorded model responses through the published
code. Compare `prompt_fingerprint` and `benchmark_fingerprint` in two manifests to
confirm that two runs used the same prompts and benchmark.

## Runs

| Run | What it is |
|---|---|
| `20261026T154844Z_benchmark_6bf7a549d7` | Smoke test: 1 easy case × 1 trial. Pipeline check only, not a result. |
| `20261026T171827Z_benchmark_6786aa8b98` | First official attempt with judge `gemini-3.5-flash`. Paused at 2/36 on the judge's ~20/day free quota. Abandoned; not a result. |
| `20261026T174528Z_benchmark_617b9de596` | Smoke test of the Flash-Lite pair (generator `gemini-3.1-flash-lite`, judge `gemini-3.5-flash-lite`): 1 easy case × 1 trial. Pipeline check only. |
| `20261027T025551Z_benchmark_c6f6d5e938` | **Official run.** 12 cases × 3 trials, generator `gemini-3.1-flash-lite`, judge `gemini-3.5-flash-lite`. Winner: **1-agent**. Verified with `report` and `replay`. |
