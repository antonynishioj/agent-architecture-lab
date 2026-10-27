# Run `6bf7a549d7`

Status: **completed** · 1/1 case-trials · generator `gemini-3.5-flash-lite` · judge `gemini-3.5-flash` · git `7deff28-dirty` · prompts `8b075615a0f0fe7b`

## Winner

**1-agent**. 2-agent scored highest, but 1-agent is not significantly worse and uses fewer tokens, so the extra agents are not worth their cost.

> Winner = the cheapest architecture (fewest tokens per answer) whose Quality Index is not significantly lower than the best architecture's (paired bootstrap 95% CI of the difference includes 0, or the gap is below 0.02).

## Leaderboard

| Architecture | Quality Index (95% CI) | Faithfulness | Completeness | Uncertainty | Win rate | Tokens / answer | Latency (s) | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 1-agent | 0.977 (0.977–0.977) | 0.980 | 1.000 | 0.950 | 0.00 | 1054 | 21.6 | 0.00079 |
| 2-agent | 0.983 (0.983–0.983) | 0.990 | 1.000 | 0.970 | 0.00 | 3002 | 57.1 | 0.00316 |
| 3-agent | 0.977 (0.977–0.977) | 0.980 | 1.000 | 0.950 | 1.00 | 5174 | 87.4 | 0.00511 |
| 4-agent | 0.983 (0.983–0.983) | 0.990 | 1.000 | 0.970 | 0.00 | 6194 | 85.9 | 0.00535 |

## Is each architecture as good as the best?

Paired bootstrap over cases, against **2-agent**.

| Architecture | Gap (best − it) | 95% CI | As good as best? |
|---|---|---|---|
| 1-agent | 0.007 | 0.007 to 0.007 | yes |
| 3-agent | 0.007 | 0.007 to 0.007 | yes |
| 4-agent | 0.000 | 0.000 to 0.000 | yes |

## Quality by difficulty

| Difficulty | 1-agent | 2-agent | 3-agent | 4-agent | Best | Winner |
|---|---|---|---|---|---|---|
| easy (1) | 0.977 | 0.983 | 0.977 | 0.983 | 2-agent | 1-agent |

## Robustness to the scoring weights

| Scheme | Best quality | Winner |
|---|---|---|
| equal | 2-agent | 1-agent |
| trust_first | 2-agent | 1-agent |
| overall_only | 2-agent | 1-agent |
| blind_ranking | 3-agent | – |

## Verify this run

```bash
uv run agent-lab report <this directory>   # recompute summary.json from the raw case files
uv run agent-lab replay <this directory>   # re-run every call from llm_cache.jsonl, no API key needed
```
