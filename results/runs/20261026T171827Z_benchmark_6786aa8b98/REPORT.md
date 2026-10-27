# Run `6786aa8b98`

Status: **paused** · 2/36 case-trials · generator `gemini-3.5-flash-lite` · judge `gemini-3.5-flash` · git `7deff28-dirty` · prompts `8b075615a0f0fe7b`

## Winner

**1-agent**. 3-agent scored highest, but 1-agent is not significantly worse and uses fewer tokens, so the extra agents are not worth their cost.

> Winner = the cheapest architecture (fewest tokens per answer) whose Quality Index is not significantly lower than the best architecture's (paired bootstrap 95% CI of the difference includes 0, or the gap is below 0.02).

## Leaderboard

| Architecture | Quality Index (95% CI) | Faithfulness | Completeness | Uncertainty | Win rate | Tokens / answer | Latency (s) | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 1-agent | 0.977 (0.973–0.982) | 0.995 | 0.938 | 0.975 | 0.00 | 1014 | 24.6 | 0.00071 |
| 2-agent | 0.983 (0.980–0.985) | 0.985 | 1.000 | 0.965 | 0.50 | 3040 | 35.3 | 0.00324 |
| 3-agent | 0.987 (0.977–0.997) | 0.990 | 1.000 | 0.975 | 0.50 | 4942 | 62.4 | 0.00480 |
| 4-agent | 0.987 (0.983–0.990) | 0.990 | 1.000 | 0.975 | 0.00 | 6230 | 81.1 | 0.00543 |

## Is each architecture as good as the best?

Paired bootstrap over cases, against **3-agent**.

| Architecture | Gap (best − it) | 95% CI | As good as best? |
|---|---|---|---|
| 1-agent | 0.010 | -0.005 to 0.024 | yes |
| 2-agent | 0.004 | -0.003 to 0.012 | yes |
| 4-agent | 0.000 | -0.007 to 0.007 | yes |

## Quality by difficulty

| Difficulty | 1-agent | 2-agent | 3-agent | 4-agent | Best | Winner |
|---|---|---|---|---|---|---|
| easy (2) | 0.977 | 0.983 | 0.987 | 0.987 | 3-agent | 1-agent |

## Robustness to the scoring weights

| Scheme | Best quality | Winner |
|---|---|---|
| equal | 3-agent | 1-agent |
| trust_first | 3-agent | 1-agent |
| overall_only | 4-agent | 1-agent |
| blind_ranking | 3-agent | – |

## Verify this run

```bash
uv run agent-lab report <this directory>   # recompute summary.json from the raw case files
uv run agent-lab replay <this directory>   # re-run every call from llm_cache.jsonl, no API key needed
```
