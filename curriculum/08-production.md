# 08 — Evals in production: CI gates, online evals, monitoring

> **Big idea:** Offline evals guard the door, and online evals watch the house.
> You need both, and they feed each other.

## Offline evals in CI

Put the eval in your pipeline the way you would tests:

| When | What | Size | Gate? |
|---|---|---|---|
| Every PR touching prompts, models, or AI code | smoke set | 20–50 cases, code graders (+ judge) | Block on guardrail failures. Warn on quality drops beyond the noise. |
| Nightly / pre-release | full set + holdout | all cases, multiple trials | Release review |
| Model upgrade | full set, side by side | all cases, multiple trials | Explicit go/no-go decision |

Gating rules that work in practice:
- **Guardrails are hard gates**: policy violations, safety, and schema validity. Any regression blocks the merge.
- **Quality gates use thresholds above noise**: e.g. "block if the overall pass rate drops more than X points *and* the paired CI excludes 0." Gating on raw deltas from small sets creates flaky CI, and people learn to ignore it.
- **Post the comparison to the PR** (`compare.py` output) so reviewers see what changed, not just pass/fail.

## Online evals (on live traffic)

Production is where you find the cases you didn't think of.

- **Implicit signals**: thumbs up/down, edits to AI drafts, retries, escalations, abandonment, and whether a human agent re-categorized the ticket.
- **Sampled LLM-judge scoring**: run your (calibrated!) judge on a sample of production outputs.
- **Guardrail monitors**: run policy and safety checks on 100% of traffic if they're cheap code checks.
- **Human review queues**: sample N items per week for expert review. Weight the sample toward low-confidence or flagged items.

## Monitoring basics

Track, over time and per slice:
- Quality proxies (judge scores, feedback rate, edit rate)
- Guardrail violation rate
- Refusals, errors, and timeouts (`stop_reason` values: `refusal`, `max_tokens`)
- Cost per request and per successful outcome
- Latency p50/p95
- **Input drift**: is the mix of inputs changing (new languages, new product areas)?

## Closing the loop

```
production traffic ──▶ monitors & sampling ──▶ failures found
        ▲                                             │
        │                                             ▼
   ship change ◀── offline eval passes ◀── add failures as test cases
```

This loop is the core operating rhythm of a healthy AI feature team.

## Model and vendor upgrades

New model versions come out often. Treat an upgrade like a dependency major-version bump:
run the full eval side by side, read the regressions, check cost and latency, and adjust
prompts (newer models often need *less* prescriptive prompting). Then decide.

## As a lead engineer

- **Own the pipeline design**: which evals run where, who gets paged on a guardrail breach, and who triages online eval failures.
- **Define the SLOs** for AI quality, just like uptime: "policy violations < 0.1% of replies, judged quality ≥ 4.0 median."
- **Incident process for AI**: what happens when the bot says something bad? Who rolls back the prompt, and how fast? Prompt rollback should be as easy as a code rollback.

## Lab

→ **Lab 7**: turn the lab eval into a CI gate script.
