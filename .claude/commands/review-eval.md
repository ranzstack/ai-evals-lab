---
description: Audit an eval (from the labs or from work) against the eval health checklist
argument-hint: "[path to eval code/data, or blank for the lab eval]"
---

Audit the eval at **$ARGUMENTS** (default: the lab eval in `labs/`) using `playbook/eval-review-checklist.md`.

- Read the actual code, data, and grader logic, not just the README.
- Run cheap programmatic checks over the dataset: size, label balance, duplicates, tag coverage, and cases that leak the expected answer into the input.
- Spot-read a sample of 5–10 cases, and check whether each expected label is actually right.
- For each checklist section, report **observations and suggestions**, not verdicts: the eval's author may have context you don't. Cite `file:line`.
- Finish with the top 3 fixes, ranked by how much they'd change decisions made from this eval.
- If this is the lab eval, there are deliberately planted weaknesses. Ask me to find them first, before you reveal them.
