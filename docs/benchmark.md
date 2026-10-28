# The benchmark (v2.0)

Twelve research questions in four tiers, three per tier. Questions, reference
answers, key points and trap claims are in
[`data/benchmark/benchmark.json`](../data/benchmark/benchmark.json). The frozen
evidence is in [`research.json`](../data/benchmark/research.json).

**The sources are synthetic** (example.com URLs). That is deliberate: it lets every
conflict, outdated fact and planted error be exactly controlled, and nobody has
to wonder whether a real web page changed. The trade-off is that they are cleaner
than real pages. Use custom cases with web search for real-world spot checks.

## Why tiers?

If every case is easy, every architecture scores about 0.98 and nothing is learned
(the smoke test showed exactly this). Specialist fact-checkers and critics can only
prove their value when the evidence is **messy**. The tiers make the difficulty
explicit, so the results can answer "when do extra agents pay off?"

## The cases

| ID | Tier | Question (short) | What makes it hard |
|---|---|---|---|
| `rag-benefits-001` | easy | Main advantages of RAG | Nothing. All sources agree. |
| `vector-db-purpose-002` | easy | What a vector DB is for | Must keep "approximate" (not exact) search |
| `context-window-003` | easy | Context window and overflow | Five key points to cover |
| `rag-reliability-004` | medium | Does RAG make answers reliable? | Balancing pros, cons and conditions across 5 sources |
| `build-vs-buy-005` | medium | In-house vs external AI platform | Six trade-off dimensions |
| `finetune-vs-rag-006` | medium | Fine-tune vs RAG vs both | Separating behaviour from knowledge needs |
| `conflicting-metrics-007` | hard | Northwind's resolution-time cut | 40% press release vs 22% audit; a distractor company |
| `token-cost-math-008` | hard | Monthly API cost | Arithmetic; outdated 2023 prices; two discounts that don't apply |
| `distractor-study-009` | hard | Helios study on small models | Only 1 of 4 sources answers; a near-identical "Helios-2" |
| `insufficient-evidence-010` | adversarial | Orion Assist parameter count | Correct answer: not disclosed. A forum guess of 70B is bait. |
| `false-premise-011` | adversarial | Why Lumen 3.0 deprecated GC | It didn't. False premise, plus a corrected blog post. |
| `planted-claim-012` | adversarial | Acme RAG chunk size | A content farm says 4,096; the docs and a maintainer say 1,024 max |

## Fields per case

| Field | Purpose |
|---|---|
| `question` | Shown to the agents |
| `reference_answer` | Shown to the judge only |
| `key_points` | Judge marks each covered / partial / missing; completeness = (covered + 0.5 × partial) / total |
| `must_not_claim` | Trap claims; any repetition is a **trap violation** and caps uncertainty handling at 0.4 |
| `design_notes` | Why the case is hard. Shown in the UI and docs, never to the agents or the judge. |

## Worked example: `token-cost-math-008`

Correct answer: input 2M × 1,500 = 3B tokens × $0.40/M = **$1,200**; output
2M × 300 = 600M tokens × $1.60/M = **$960**; total **$2,160**/month. The volume
discount needs more than 5B tokens (this is 3.6B). The batch discount excludes
interactive traffic. Using the archived 2023 prices gives the trap answer of $3,000.

This case tests whether a dedicated fact-checker catches the outdated price list,
and whether the critic catches the discounts that do not apply, more reliably than
a single agent doing everything at once.

## Adding or changing cases

1. Add the case to `benchmark.json` and its sources to `research.json`, using the same `case_id`.
2. Bump `version` in both files. The benchmark fingerprint in each run's manifest
   changes automatically, so old and new runs are never silently compared.
3. `uv run pytest` checks that every case has evidence and key points.
