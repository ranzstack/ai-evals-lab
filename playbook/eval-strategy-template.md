# Eval strategy: <feature name>

_Owner: · Last updated: · Status: draft_

## 1. What the feature does
One paragraph. Who uses it, and what decision or action does its output drive?

## 2. Success criteria
| Criterion | Type | Target | How measured |
|---|---|---|---|
| e.g. Correct routing category | quality | ≥ 95% | code grader vs labelled set |
| e.g. Never promise refunds | guardrail | 100% | regex + judge |
| e.g. Reply quality | quality | median ≥ 4/5 | calibrated LLM judge |
| e.g. p95 latency | ops | < 4s | harness timing |
| e.g. Cost per request | ops | < $0.01 | token usage |

## 3. Cost of errors
What happens when it's wrong? Who notices, and how bad is it? Which errors are much worse than others?

## 4. Dataset
- Sources (production sample / failures / expert-written / synthetic):
- Size now / target:
- Slices that must be covered:
- Labelling guidelines (link):
- Who labels? How do we measure labeller agreement?
- Holdout set: size, and who may run it:
- Privacy / anonymization:

## 5. Graders
| Grader | Kind | Checks | Calibrated? (agreement / kappa) |
|---|---|---|---|

## 6. When evals run
| Trigger | Set | Gate rule | Owner |
|---|---|---|---|
| PR touching prompts/models | smoke | guardrails block; quality warn > X pts | |
| Nightly | full + trials | report | |
| Model upgrade | full + holdout | go/no-go review | |

## 7. Production monitoring
Signals, sample rate, review cadence, alert thresholds, and who's on point.

## 8. Feedback loop
How production failures become test cases (process, owner, cadence).

## 9. Open questions / decisions needed
- TODO(verify):
