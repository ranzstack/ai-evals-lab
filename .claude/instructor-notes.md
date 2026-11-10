# Instructor notes (for Claude; spoilers for the learner)

Planted weaknesses in the lab eval. During `/review-eval` and the labs, let the learner
find these first, and reveal them only after a real attempt.

1. **Dev set is keyword-friendly.** The mock (keyword rules) gets ~95% category accuracy on dev and ~50% on holdout. The dev labels are too easy to distinguish smart from dumb.
2. **Thin slices.** Most tags have exactly one case, and 9 of 20 cases are tagged `easy`. Per-tag pass rates are almost meaningless.
3. **Regex policy grader has poor recall.** "Your money will be returned" or "I've processed your refund" sail through `grade_reply_policy`.
4. **Length grader is arbitrary** (15–120 words) and Goodhart-able.
5. **No grader for clarifying questions.** `t016` ("help") notes say the reply should ask a clarifying question, but nothing checks that.
6. **Injection handling is checked only indirectly.** `t009` is caught only if the reply literally says "refund approved"; the classification being hijacked to `urgent` is caught by the priority grader, but there's no dedicated injection guardrail.
7. **Judge is uncalibrated, and the same model family as the system under test** by default (self-preference risk).
8. **Single labeller.** All labels were written by one author; priority labels in particular are debatable (e.g. `t018`, `h002`). No inter-annotator agreement.
9. **Overall metric = all graders pass.** This conflates guardrails with quality. Arguably, guardrails should be reported separately.
10. **Holdout is tiny (8 cases).** It's a sanity check, not a measurement.
11. **Mock nondeterminism** is uniform random. Real model variance clusters on hard or ambiguous cases. Worth discussing.
