# 05 — Metrics and statistics (just enough)

> **Big idea:** Every eval number has an error bar. With small datasets and
> nondeterministic models, many "improvements" are noise.

## Two sources of noise

1. **Sampling noise (which cases).** With 20 cases, one case flipping moves the pass rate by 5 points. Your dataset is a sample of all possible inputs.
2. **Model nondeterminism (which run).** The same input can produce different outputs from run to run. The mock model simulates this: run with `--trials 5` and look at how priority varies.

## Confidence intervals

A 95% **confidence interval (CI)** gives the range the "true" pass rate plausibly falls in.
The lab uses the **bootstrap**: resample the cases with replacement thousands of times,
recompute the mean each time, and take the middle 95% (`stats.py → bootstrap_ci`).

Rough intuition for a pass rate around 80%:

| Cases | ±95% CI (approx.) |
|---|---|
| 20 | ±18 points |
| 50 | ±11 points |
| 100 | ±8 points |
| 400 | ±4 points |

So with a 20-case eval, "78% → 85%" is **not** evidence of anything.

## Paired comparison: your best friend

When you compare prompt A with prompt B on the **same cases**, compare *per-case
differences* rather than two separate averages. Case difficulty cancels out, so you can
detect real changes with far fewer cases. `compare.py` uses a **paired bootstrap** on the
delta. If its CI excludes 0, the change is probably real.

Also count **regressions**. A change that fixes 6 cases and breaks 2 is different from one
that fixes 4 and breaks none, even though both are +4 net. Always read the broken cases.

## Multiple trials: pass@k vs pass^k

Run each case *k* times:
- **pass@k**: passed *at least once* in k tries. This is relevant when a human or a verifier can pick the best attempt (e.g. generating code candidates that tests will check).
- **pass^k** ("pass hat k"): passed *every* time. This is relevant for customer-facing features, where each user gets one shot. **This is the one your users feel.**

A system can have a high pass@5 and a terrible pass^5. That gap measures **unreliability**.

## Choosing metrics

- **Classification**: accuracy, plus **precision/recall per class** when classes matter differently. Missing an `urgent` ticket (low recall on urgent) is much worse than over-flagging one.
- **Asymmetric costs**: weight errors by their impact. The lab gives partial credit on priority; you might add a hard rule that urgent must never be predicted below high.
- **Guardrail metrics**: things that must stay at ~100% (policy, safety, format). Track them separately from quality metrics. Don't let a quality win hide a guardrail loss.
- **Cost & latency**: report them next to quality. A 2-point gain at 3× the cost may be a loss.

## Saturation

If you're at ~98% on your eval, it can no longer distinguish good from better. You need
harder cases. A saturated eval mostly measures noise and formatting quirks.

## As a lead engineer

- **Demand error bars.** "Prompt v3 is better" should come with "on n cases, delta +X, CI [a, b], and these cases regressed."
- **Pre-register the decision rule:** decide *before* the run what result would make you ship. This prevents p-hacking by re-running until it looks good.
- **Don't over-index on one number.** A dashboard with an overall score, guardrails, per-slice scores, cost, and latency beats a single score.

## Lab

→ **Lab 4**: measure noise, and compare two runs properly.
