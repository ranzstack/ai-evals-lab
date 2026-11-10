# 02 — Anatomy of an eval

> **Big idea:** Every eval has the same four parts: **dataset → task → grader → metric**.
> Once you can see those parts, you can build, debug, and critique any eval.

## The four parts

```
 dataset (cases)        task (system under test)       grader(s)          metric(s)
 ┌──────────────┐       ┌──────────────────────┐      ┌───────────┐     ┌──────────────┐
 │ input        │──────▶│ prompt + model +     │─────▶│ score each │────▶│ aggregate    │
 │ expected     │       │ tools/context        │ out  │ output     │     │ across cases │
 │ tags, notes  │       └──────────────────────┘      └───────────┘     └──────────────┘
 └──────────────┘
```

In the lab code:

| Part | Where |
|---|---|
| Dataset | `labs/data/tickets.jsonl`: one JSON object per line with `id`, `input`, `expected`, `tags` |
| Task | `labs/evalkit/app.py` → `triage()` |
| Graders | `labs/evalkit/graders.py`: four code graders plus an LLM judge |
| Metrics | `labs/run_eval.py` → `summarize()`: pass rates, CIs, per-tag breakdown, cost, latency |

## Cases

A good case has:
- **input**: exactly what the system would see in production.
- **expected**: the reference answer, or the properties a good answer must have.
- **acceptable alternatives**, where reasonable experts would disagree (see `t006`).
- **tags**: so you can slice results ("how do we do on non-English tickets?").
- **notes**: *why* this case exists. Future-you will thank you.

## Graders

A grader turns one output into a score. You'll go deeper in Module 4. For now, notice
that the lab uses **several graders per case**, each checking one thing: category,
priority, policy, length, and reply quality. Single-purpose graders make failures easy
to diagnose.

## Metrics

- **Per-grader pass rate**: what fraction of cases pass each check.
- **Overall pass rate**: what fraction pass *all* checks. It's strict, and it's what a user experiences.
- **Per-tag pass rate**: where you're weak.
- **Cost and latency**: quality is only half the story.

## Harness hygiene (the boring part that bites)

- **Errors count as failures**, never as skips (`run_eval.py`, `run_one`). If you skip errored cases, a prompt that crashes on hard inputs looks *better*.
- **Same inputs every time.** Don't regenerate the dataset between runs you want to compare.
- **Save raw outputs**, not just scores (`results/*.jsonl`). You will want to re-grade later.
- **Record the config**: prompt version, model, and date. The filename does this in the lab.

## As a lead engineer

When someone shows you an eval result, ask about all four parts:
1. *Dataset:* how many cases, where did they come from, and who labelled them?
2. *Task:* is this exactly the production prompt and config?
3. *Grader:* how do we know the grader is right?
4. *Metric:* what's the error bar, and what are the failures?

Most bad decisions come from a strong-looking metric sitting on a weak dataset or grader.

## Lab

→ **Lab 1** in `labs.md`: run your first eval and read the failures.
