# Run `617b9de596`

Status: **completed** · 1/1 case-trials · generator `gemini-3.1-flash-lite` · judge `gemini-3.5-flash-lite` · git `7deff28-dirty` · prompts `8b075615a0f0fe7b`

## Winner

**1-agent**. 4-agent scored highest, but 1-agent is not significantly worse and uses fewer tokens, so the extra agents are not worth their cost.

> Winner = the cheapest architecture (fewest tokens per answer) whose Quality Index is not significantly lower than the best architecture's (paired bootstrap 95% CI of the difference includes 0, or the gap is below 0.02).

## Leaderboard

| Architecture | Quality Index (95% CI) | Faithfulness | Completeness | Uncertainty | Win rate | Tokens / answer | Latency (s) | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 1-agent | 0.997 (0.997–0.997) | 1.000 | 1.000 | 1.000 | 1.00 | 1037 | 4.1 | 0.00053 |
| 2-agent | 0.997 (0.997–0.997) | 1.000 | 1.000 | 1.000 | 0.00 | 2356 | 10.3 | 0.00147 |
| 3-agent | 0.997 (0.997–0.997) | 1.000 | 1.000 | 1.000 | 0.00 | 4317 | 11.6 | 0.00263 |
| 4-agent | 0.998 (0.998–0.998) | 1.000 | 1.000 | 1.000 | 0.00 | 5800 | 10.3 | 0.00330 |

## Is each architecture as good as the best?

Paired bootstrap over cases, against **4-agent**.

| Architecture | Gap (best − it) | 95% CI | As good as best? |
|---|---|---|---|
| 1-agent | 0.002 | 0.002 to 0.002 | yes |
| 2-agent | 0.002 | 0.002 to 0.002 | yes |
| 3-agent | 0.002 | 0.002 to 0.002 | yes |

## Quality by difficulty

| Difficulty | 1-agent | 2-agent | 3-agent | 4-agent | Best | Winner |
|---|---|---|---|---|---|---|
| easy (1) | 0.997 | 0.997 | 0.997 | 0.998 | 4-agent | 1-agent |

## Robustness to the scoring weights

| Scheme | Best quality | Winner |
|---|---|---|
| equal | 4-agent | 1-agent |
| trust_first | 4-agent | 1-agent |
| overall_only | 4-agent | 1-agent |
| blind_ranking | 1-agent | – |

## Verify this run

```bash
uv run agent-lab report <this directory>   # recompute summary.json from the raw case files
uv run agent-lab replay <this directory>   # re-run every call from llm_cache.jsonl, no API key needed
```
