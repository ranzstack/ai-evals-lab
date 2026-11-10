# Eval review checklist

Use this to audit any eval, including your own. Report observations and suggestions,
not verdicts. The eval's author may have context you don't.

## Does it run?
- [ ] Runs end to end today, with one command
- [ ] Errors are counted as failures, not skipped

## Task design (the cases)
- [ ] Success criteria are unambiguous: two experts would agree on pass/fail
- [ ] Expected labels are correct (re-derive 10 at random)
- [ ] Ground-truth provenance is known (human-written? model-generated? by which model?)
- [ ] Cases reflect the production distribution, and their *shape* matches (single vs multi-turn)
- [ ] Important slices have enough cases (not 1 each)
- [ ] No leakage of answers into prompts, examples, or tools
- [ ] A trivial baseline (majority class, keyword rules) doesn't score suspiciously well
- [ ] Not saturated: there's headroom at the top
- [ ] A holdout set exists and isn't tuned against

## Harness
- [ ] The eval uses the exact production prompt and config
- [ ] Raw outputs are saved, and the config is recorded
- [ ] Inputs are identical across compared runs

## Graders
- [ ] Code graders are used wherever the property is checkable
- [ ] Code graders tested against known good and bad examples (precision *and* recall)
- [ ] The LLM judge has an anchored rubric and reasons before scoring
- [ ] The judge is calibrated against human labels (agreement %, kappa)
- [ ] Pairwise judges run both orders (position bias)

## Metrics & decisions
- [ ] Results reported with CIs / error bars
- [ ] Paired comparison used for A/B
- [ ] Multiple trials where outputs vary; pass^k reported for user-facing features
- [ ] Guardrails tracked separately from quality
- [ ] Cost and latency reported alongside quality
- [ ] Decision rule defined before the run
