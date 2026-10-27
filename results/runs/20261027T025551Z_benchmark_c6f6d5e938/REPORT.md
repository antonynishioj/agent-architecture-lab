# Run `c6f6d5e938`

Status: **completed** · 36/36 case-trials · generator `gemini-3.1-flash-lite` · judge `gemini-3.5-flash-lite` · git `7deff28-dirty` · prompts `8b075615a0f0fe7b`

## Winner

**1-agent**. 4-agent scored highest, but 1-agent is not significantly worse and uses fewer tokens, so the extra agents are not worth their cost.

> Winner = the cheapest architecture (fewest tokens per answer) whose Quality Index is not significantly lower than the best architecture's (paired bootstrap 95% CI of the difference includes 0, or the gap is below 0.02).

## Leaderboard

| Architecture | Quality Index (95% CI) | Faithfulness | Completeness | Uncertainty | Win rate | Tokens / answer | Latency (s) | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 1-agent | 0.981 (0.966–0.993) | 1.000 | 0.941 | 0.985 | 0.31 | 1089 | 5.2 | 0.00053 |
| 2-agent | 0.976 (0.950–0.993) | 1.000 | 0.932 | 0.985 | 0.14 | 2749 | 15.4 | 0.00181 |
| 3-agent | 0.982 (0.957–0.996) | 1.000 | 0.944 | 0.985 | 0.11 | 4739 | 22.7 | 0.00285 |
| 4-agent | 0.983 (0.960–0.998) | 1.000 | 0.941 | 0.990 | 0.44 | 6411 | 25.9 | 0.00361 |

## Is each architecture as good as the best?

Paired bootstrap over cases, against **4-agent**.

| Architecture | Gap (best − it) | 95% CI | As good as best? |
|---|---|---|---|
| 1-agent | 0.002 | -0.016 to 0.019 | yes |
| 2-agent | 0.007 | -0.002 to 0.014 | yes |
| 3-agent | 0.001 | -0.007 to 0.008 | yes |

## Quality by difficulty

| Difficulty | 1-agent | 2-agent | 3-agent | 4-agent | Best | Winner |
|---|---|---|---|---|---|---|
| easy (3) | 0.987 | 0.989 | 0.998 | 0.997 | 3-agent | 1-agent |
| medium (3) | 0.995 | 0.996 | 0.996 | 0.997 | 4-agent | 1-agent |
| hard (3) | 0.964 | 0.937 | 0.947 | 0.939 | 1-agent | 1-agent |
| adversarial (3) | 0.977 | 0.983 | 0.987 | 0.999 | 4-agent | 1-agent |

## Robustness to the scoring weights

| Scheme | Best quality | Winner |
|---|---|---|
| equal | 4-agent | 1-agent |
| trust_first | 4-agent | 1-agent |
| overall_only | 4-agent | 1-agent |
| blind_ranking | 4-agent | – |

## Verify this run

```bash
uv run agent-lab report <this directory>   # recompute summary.json from the raw case files
uv run agent-lab replay <this directory>   # re-run every call from llm_cache.jsonl, no API key needed
```
