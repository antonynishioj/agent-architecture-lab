# Running on the Gemini free tier

**Yes, the full experiment runs on a free key.** These are the numbers to plan around.

## Limits

Free-tier limits change, and they apply **per project and per model**. Check
yours at https://aistudio.google.com/rate-limit. When this was written
(October 2026), community trackers reported roughly:

| Model | Role here | Requests/min | Requests/day |
|---|---|---|---|
| gemini-3.1-flash-lite | **generator** | ~10–15 | ~500 |
| gemini-3.5-flash-lite | **judge** | ~10–15 | ~500 |
| gemini-3.5-flash, 3.6/3.8 Flash | not used | ~10 | **~20** |

> **Why two Flash-Lite models?** The first official attempt used
> `gemini-3.5-flash` as the judge and paused after 2 of 36 case-trials. Full Flash
> models allow only about 20 free requests per day, and the judge needs about 180.
> Two *different* Flash-Lite models each get their own ~500/day quota. The judge
> is the newer one, and using different models still limits self-preference bias.

Set the limits you actually have in `.env` (`GEMINI_RPM`, `GEMINI_RPD`,
`GEMINI_JUDGE_RPM`, `GEMINI_JUDGE_RPD`). The UI uses them for the quota meter and
the time estimate, and the rate limiter uses the RPM values.

Creating more API keys in the same Google Cloud project does **not** raise the quota.

## What a run costs in requests

Per case per trial:

| | Calls |
|---|---|
| Generator: 1 + 2 + 3 + 4 agents | 10 |
| Judge: 4 rubric scores + 1 blind ranking | 5 |

| Run | Generator | Judge | Approx. time |
|---|---|---|---|
| Smoke test (1 case × 1 trial) | 10 | 5 | ~1 min |
| One tier (3 cases × 3 trials) | 90 | 45 | ~15 min |
| **Official (12 cases × 3 trials)** | **360** | **180** | **≈ 1 h** (fits one day's quota) |

Call speed depends on the model. `gemini-3.5-flash-lite` took 15–45 s per call;
`gemini-3.1-flash-lite` took 2–6 s. The engine runs the four architectures
**in parallel** for each case, so with fast models the per-minute cap
(`GEMINI_RPM`) sets the pace. If your project allows more than 10 requests per
minute, raising it shortens the run.

Using **two different models** for generation and judging gives the run two
separate daily quotas. That is why the official run fits in one day. If you
already used part of today's quota on tests, the run pauses and finishes after
the reset.

## Don't multiply keys

API keys in the same Google Cloud project share one quota. Creating extra projects
or accounts just to multiply the free quota likely breaches Google's terms. It also
makes a pre-registered run harder to defend. If you need more capacity, enabling
billing on the project costs very little for this experiment. Every call's tokens
are recorded, and paid-tier prices are in `data/pricing.json`.

## What happens when something goes wrong

| Event | Behaviour |
|---|---|
| Too many requests per minute | Never sent: the rate limiter waits |
| Transient 429 / 500 / 503 | Retried with backoff, honouring the server's `retryDelay` |
| **Daily quota exhausted** | The run **pauses**; everything finished is saved |
| Backend stopped mid-run | Start it again and press **Resume** on the run page |

Resuming re-runs only unfinished case-trials. Any call already made is served
from `llm_cache.jsonl`, so nothing is paid for twice. Quotas reset at **midnight
Pacific time**.

## Tips

- Start the official run in the morning (Pacific time) with a fresh quota.
- Keep the backend terminal open. The run lives in the server process.
- Don't run custom cases during the official run. The server allows one run at a time anyway.
- On the free tier, Google may use prompts to improve its products. Keep private
  data out of custom cases.
- The `estimated_cost_usd` numbers are what the run **would** cost on the paid tier
  (prices in `data/pricing.json`). The actual cost is $0.
