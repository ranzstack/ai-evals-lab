# AI feature PR checklist

For any PR that changes a prompt, model, model parameters, retrieval, tools, or
output parsing.

**Author**
- [ ] What changed, and what failure group is it meant to fix? (hypothesis)
- [ ] Eval comparison attached: baseline vs this PR (`compare.py` output or equivalent)
- [ ] Overall delta **with CI**, and the number of cases
- [ ] Every regressed case listed and explained (or accepted on purpose)
- [ ] Guardrail metrics unchanged (policy, safety, schema validity)
- [ ] Cost and latency impact noted
- [ ] New failure cases found during this work were added to the dataset
- [ ] Prompt version name updated

**Reviewer**
- [ ] Is the eval run on the *exact* config being shipped?
- [ ] Is the improvement bigger than the noise?
- [ ] Are any fixes suspiciously specific to eval cases (overfitting / leakage)?
- [ ] If graders changed: was the baseline re-run with the new graders?
- [ ] Spot-read 3–5 raw outputs, not just the numbers
- [ ] Rollback plan: can we revert the prompt or model quickly?
