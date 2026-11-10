# 04 — Graders: code, model, and human

> **Big idea:** Use the cheapest grader that can reliably judge each property.
> Code first, model next, humans to calibrate both.

## The three families

| | Code-based | Model-based (LLM-as-judge) | Human |
|---|---|---|---|
| Examples | exact match, regex, JSON schema, unit tests, numeric tolerance | rubric scoring, pairwise "A vs B", fact-checking against a reference | expert review, user ratings |
| Speed / cost | instant, free | seconds, cents | minutes, dollars |
| Consistency | perfect | good, but it varies | varies between people |
| Handles nuance | poorly | well | best |
| Lab file | `graders.py`: `grade_category`, `grade_priority`, `grade_reply_policy`, `grade_reply_length` | `grade_reply_judge` | `calibrate_judge.py` |

## Code-based graders

Use them for anything with a checkable answer: labels, formats, schemas, numbers, forbidden
content, and "did the code it wrote pass the tests?".

Things to notice in the lab:
- **Partial credit vs pass/fail.** `grade_priority` scores off-by-one as 0.5 but still *fails* it. Report the graded score, and gate on the threshold.
- **Regex policy checks are brittle.** `grade_reply_policy` catches "we will refund you", but does it catch "your money will be returned"? Code graders give you precision; recall is your responsibility.

## LLM-as-judge

Use a model when the property needs judgement: helpfulness, tone, faithfulness to a
source, or whether the reply addresses the actual issue.

What makes a judge reliable:
1. **A specific rubric** with anchored levels (see `JUDGE_RUBRIC` in `graders.py`). "Rate 1–10 how good this is" doesn't work well.
2. **Reasoning before the score.** The judge schema puts `reasoning` before `score`.
3. **Structured output**, so you never have to parse free text.
4. **One property per judge** if you can. A judge that checks five things gives muddy scores.
5. **Give it what it needs**: the input, the output, and a reference answer when one exists.
6. **Pairwise comparison** ("which reply is better, A or B?") is often more reliable than absolute scores when you're comparing two versions.

Known judge biases:
- **Position bias** (in pairwise comparison): it prefers whichever answer comes first, or second. Fix: run both orders.
- **Verbosity bias**: it prefers longer answers.
- **Self-preference**: it may prefer outputs in its own style or from its own model family. Consider a different judge model, and above all, calibrate.
- **Leniency**: judges often grade generously. Calibrate against humans to find out.

## Calibration: the step everyone skips

A judge is a measuring instrument. **Before you trust it, check it against human judgement:**

1. Have humans (you!) score 20–50 outputs blind, without seeing the judge's score.
2. Compare: pass/fail agreement, and **Cohen's kappa** (agreement beyond chance; > 0.6 is decent, > 0.8 is strong).
3. Read every disagreement. Is the rubric unclear? Is the judge missing context? Is the *human* wrong?
4. Fix the rubric, then re-measure.

The lab's `calibrate_judge.py` does exactly this.

## Human evaluation

Humans are needed for: building ground truth, calibrating judges, judging high-stakes or
subjective outputs, and periodic audits of production traffic. Make it efficient:
written guidelines, a simple labelling interface, and two labellers on a subset so you
can measure how much humans agree with *each other*. That number is the ceiling for your
judge.

## As a lead engineer

- **Review graders the way you review code.** A buggy grader is worse than none, because it gives false confidence. Put grader changes through PR review.
- **Grader changes reset the baseline.** If you change a grader, re-run the baseline too, or your comparisons are meaningless.
- **Ask:** "What's the judge's agreement with humans?" If nobody knows, the judge's numbers are a guess.

## Lab

→ **Lab 3**: calibrate the LLM judge against your own labels.
