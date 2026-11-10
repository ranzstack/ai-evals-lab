# 01 — Why evals: from vibe checks to measurement

> **Big idea:** Without evals, every AI change is shipped on vibes. Evals turn
> "it seems better" into "it's better on 92% of cases, here's what regressed."

## The vibe-check trap

The typical first AI feature is built like this: write a prompt, try five examples,
tweak, try the same five again, ship. Then:

- A customer hits case #6, which nobody tried.
- Someone "improves" the prompt for one complaint and silently breaks three other behaviours.
- A new model version comes out. Is it better *for us*? Nobody can say.
- Two engineers disagree about which prompt is better, and the loudest one wins.

Each of these is a **measurement problem**.

## What evals give you

1. **Regression safety.** Change prompts and models without fear, because you'll see what broke.
2. **Faster iteration.** A 2-minute eval run beats an afternoon of manual spot-checks.
3. **Model and vendor decisions.** "Should we switch to the cheaper model?" becomes a measurable question.
4. **Shared definition of quality.** Writing graders forces the team to agree on what "good" means.
5. **Communication.** "We're at 94% on the golden set, up from 81%" is something a PM or director can act on.

## Types of evals (a map)

- **Offline evals**: run on a fixed dataset before shipping. *(Modules 2–6)*
- **Online evals / monitoring**: score live traffic in production. *(Module 8)*
- **Capability evals**: "can it do X at all?" These are hard tasks where you hope to climb from a low score.
- **Regression evals**: "does it still do what it did?" These should sit near 100%, and any drop is a red flag.
- **Benchmarks**: public, standardized evals (e.g. for coding or reasoning). Useful for picking models, but a weak predictor of *your* use case. Your own eval beats a leaderboard.

## Eval-driven development

This is the AI equivalent of TDD:

1. Write down success criteria.
2. Build a small eval (even 20 cases) **before** you polish the prompt.
3. Get a baseline.
4. Change one thing, re-run, and compare.
5. Add every production failure you find as a new test case.

Step 5 is the most important. Your eval set grows as a record of everything that has gone wrong.

## Success criteria should be specific and measurable

Weak: "The bot should give good answers."
Strong: "Category matches the support team's label on ≥ 95% of tickets. Urgent tickets
are never classified below high. Replies never promise refunds. Replies get a median
judge score ≥ 4/5."

Notice the different *kinds* of criteria there: accuracy, a hard safety floor, a
policy constraint, and a quality bar. They will need different graders.

## As a lead engineer

- **Set the norm:** no AI change merges without an eval run attached to the PR. Start lightweight; the habit matters more than perfection.
- **Budget for it:** the eval set is a product asset. Plan for building and maintaining it the way you'd plan for a test suite.
- **Watch for the anti-pattern:** "We'll add evals after launch." After launch you'll have no baseline to compare against.

## Discussion prompts

- Think of an AI feature you've seen shipped (at work or elsewhere). How was "good enough" decided?
- Which of the five benefits above would land best with your manager?
