# 90-day eval rollout plan: <team name>

_Goal: move from maturity level __ to level __ (see Module 9)._

## Days 1–30: Foundation (one feature)
- [ ] Pick the pilot feature: _____ (pick one with real usage and a clear failure cost)
- [ ] Write success criteria with the PM / domain expert
- [ ] Write labelling guidelines (1 page)
- [ ] Build a golden set of 30–50 cases (production sample + known failures)
- [ ] One-command eval script; baseline recorded
- [ ] Demo to the team: "here's how we measure this now"

## Days 31–60: Make it a habit
- [ ] PR checklist adopted for the pilot feature
- [ ] Guardrail checks gate merges in CI
- [ ] LLM judge calibrated against ≥ 30 human labels
- [ ] Holdout set created and access-controlled
- [ ] Experiments log started

## Days 61–90: Close the loop
- [ ] Production sampling + weekly 30-minute failure review
- [ ] Failure → test case process documented
- [ ] Quality SLOs proposed
- [ ] Second feature onboarded
- [ ] Results shared upward: what we caught, what we shipped faster, and what it cost

## Risks & mitigations
| Risk | Mitigation |
|---|---|
| Eval too slow, so nobody runs it | Smoke set < 5 minutes; parallelism |
| Labelling bottleneck | Small batches; rotate labellers; domain-expert office hours |
| Flaky CI gates | Thresholds above noise; guardrails only as hard gates at first |
