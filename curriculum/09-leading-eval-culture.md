# 09 — Leading eval culture: the lead engineer's playbook

> **Big idea:** The hard part isn't the code. It's getting a team to agree on
> what "good" means and to measure it habitually. That's leadership work.

## The maturity ladder

Figure out where your team is, and aim one rung up, not five.

| Level | Looks like |
|---|---|
| 0. Vibes | Manual spot-checks; "looks good to me" |
| 1. Golden set | A shared dataset and a script anyone can run |
| 2. Eval-gated changes | Every AI PR includes an eval comparison; guardrails block merges |
| 3. Production loop | Online monitoring, failures flow back into the dataset, quality SLOs |
| 4. Eval-driven org | Product requirements arrive with success criteria; model and vendor decisions are made from evals; evals are a shared platform |

## Your levers as a lead

**Standards**
- An "AI feature definition of done": success criteria written, eval exists, baseline recorded, guardrails defined, monitoring planned. (See `playbook/ai-feature-pr-checklist.md`.)
- Prompts in version control, reviewed like code.

**Reviews**
- Questions to ask in design reviews and PRs (the four parts from Module 2, and the error bars from Module 5).
- Push back on "it looked good when I tried it." Ask kindly and consistently: "What did the eval say?"

**Infrastructure**
- A shared, boring eval harness beats five bespoke notebooks. Make the easy path the right path.
- Make it fast (under 5 minutes for a smoke run) and cheap enough that nobody hesitates to run it.

**People**
- Involve domain experts (support leads, PMs) in writing labelling guidelines and reviewing failures. They own "what good means" as much as engineers do.
- Rotate "eval duty": someone reads a sample of production outputs every week.
- Celebrate added test cases, not just improved scores.

**Communication upward**
- Translate eval results into business terms: "94% correct routing means ~60 fewer mis-routed tickets/day."
- Be honest about uncertainty. Error bars build trust with leadership over time.

## Common failure modes (and what to do)

| Symptom | Likely cause | Response |
|---|---|---|
| Eval scores are high but users complain | Dataset doesn't reflect production | Sample production, add real failures |
| Scores bounce around between runs | Too few cases or trials; uncalibrated judge | More cases, paired comparison, calibrate |
| Nobody runs the eval | Slow, expensive, or hard to run | Invest in DX: one command, fast smoke set |
| Endless prompt tweaking with no progress | No hypothesis, no failure analysis | Require "which failure group does this target?" |
| Eval became the target | Goodhart's law | Holdout set, rotate cases, read raw outputs |
| Team argues about which prompt is better | No agreed success criteria | Write criteria *before* the next experiment |

## A 90-day rollout plan

See `playbook/team-rollout-90-days.md` for a template. The short version:
- **Days 1–30:** pick one AI feature. Write success criteria with the PM. Build a 30–50 case golden set and a script. Record a baseline.
- **Days 31–60:** require eval comparisons on PRs for that feature. Add guardrail gates in CI. Calibrate the judge.
- **Days 61–90:** add production sampling and a weekly failure review. Expand to a second feature. Present the results upward.

## Capstone

→ **Capstone** in `labs.md`: write your team's eval strategy for a real feature, using
`/apply`. This is the deliverable that turns the course into impact.
