# Labs

All commands run from `labs/`. Use `/lab n` in Claude Code to be guided step by step.
Labs 1–4 work fully in free `--mock` mode. Labs 5 and 7 are better with the real API.

---

## Lab 1 — Your first eval (Module 2)

**Goal:** run the eval, read the report, and connect each number to code.

1. `uv run python run_eval.py --mock`
2. Find each of the four parts (dataset, task, graders, metrics) in the code that produced the output.
3. Which grader fails most? Read 3 failures in full. Is the *system* wrong, or the *grader*?
4. Open the saved `results/*.jsonl` and find one complete record.
5. **Question:** the overall pass rate is much lower than any single grader's pass rate. Why? Is "all graders must pass" the right headline metric for this feature?

## Lab 2 — Break it with better cases (Module 3)

**Goal:** expand coverage and find blind spots.

1. List the input dimensions for triage (see Module 3). Which ones have ≤ 1 case in `data/tickets.jsonl`?
2. Write **8 new cases** in a new file `data/tickets_mine.jsonl`. Include at least: 2 adversarial (injection, or a misleading framing), 2 non-English, 2 policy-sensitive, and 2 that you suspect the mock model will get wrong.
3. Write `notes` explaining *why* each case exists. Use `acceptable` where you honestly think two labels are both right.
4. Run `uv run python run_eval.py --mock --data data/tickets_mine.jsonl`.
5. Then run the mock on `data/tickets_holdout.jsonl`. Category accuracy drops from ~95% (dev) to ~50%. **Explain why.** What does that tell you about the dev set?

## Lab 3 — Calibrate the judge (Module 4)

**Goal:** find out whether the LLM judge agrees with *you*.

1. Run with a judge: `uv run python run_eval.py --mock` (free; the mock judge is a heuristic), or without `--mock` for a real judge (~40 calls).
2. `uv run python calibrate_judge.py export results/<that run>.jsonl`
3. Open `data/labels/to_label.jsonl`. For each row, set `human_score` to 1–5 using the rubric in `evalkit/graders.py`. **Don't look at `_judge` while you label.**
4. `uv run python calibrate_judge.py score data/labels/to_label.jsonl`
5. Read the disagreements. Edit `JUDGE_RUBRIC` to fix one systematic disagreement, then re-run with the real judge and re-score.
6. Bonus: find a reply that passes `grade_reply_policy` but clearly violates the spirit of the refund policy. What does this tell you about regex guardrails?

## Lab 4 — Noise and comparison (Module 5)

**Goal:** see noise with your own eyes, and learn to compare runs properly.

1. Run `uv run python run_eval.py --mock --trials 5`. Compare pass@5 and pass^5. Which cases are flaky?
2. Run the *same config* twice with `--trials 1` and `compare.py` the two results. You'll see "improvements" and "regressions" from a change that **changed nothing**. Remember this feeling.
3. Make a real change: edit the mock rules in `evalkit/app.py` (e.g. make "deleted" or "someone else" trigger urgent). Re-run and compare. Is the delta's CI clear of zero?
4. **Question:** with 20 cases, roughly how big would an improvement have to be before you'd believe it?

## Lab 5 — Eval-driven prompt iteration (Module 6) — real API

**Goal:** improve the real system without overfitting.
**Cost:** each full run is ~40 calls (20 cases + 20 judge calls). Use `--no-judge` for faster, cheaper loops.

1. Baseline: `uv run python run_eval.py --prompt triage_v1`. Save the filename.
2. Group the failures by cause. Pick the biggest group.
3. Copy `prompts/triage_v1.txt` to `prompts/triage_v2.txt`. Make **one** general fix. Ideas: category and priority definitions, the refund policy, treating ticket text as data, and what a good reply includes.
4. Run v2, then `compare.py baseline v2`. Keep or revert. Log it in `notes/experiments.md` (hypothesis → change → result → decision).
5. Repeat 2–4 two or three times.
6. **Only now**, run v1 and your final version on `--data data/tickets_holdout.jsonl`. Did the gains transfer?
7. Bonus: try `EVAL_MODEL=claude-haiku-5-5` with your best prompt. Compare quality, cost, and latency. Would you ship the cheaper model?

## Lab 6 — Design an agent or RAG eval (Module 7) — design only

**Goal:** apply the outcome / component / trajectory thinking to a real system.

Pick a feature, ideally one from work (or use "an agent that resolves billing tickets by looking up invoices and issuing credits up to $50"). Write `playbook/<feature>-eval-design.md` covering:
- Outcome graders (state-based where possible)
- Component evals (retrieval? tool-argument validity?)
- Trajectory checks you'd use for diagnosis, not gating
- Safety guardrails as hard fails
- Dataset sources, size, and the trials per case
- What runs on each PR, nightly, and on model upgrades

Use `/apply` to get help, and ask Claude to critique your design.

## Lab 7 — CI gate (Module 8)

**Goal:** make the eval a merge gate.

1. Write `labs/ci_gate.py`. It runs the smoke eval (code graders only), compares against a committed baseline summary, and exits non-zero if:
   - any **policy** failure appears (hard guardrail), or
   - the overall pass rate drops by more than your noise threshold (from Lab 4).
2. Write the GitHub Actions (or your CI's) YAML that runs it when files under `labs/prompts/` or `labs/evalkit/` change.
3. **Question:** what would you need to change before turning this on for a real team? (Secrets, cost caps, flakiness, and who owns the baseline.)

## Capstone — Your team's eval strategy (Module 9)

Use `/apply eval strategy` to produce `playbook/<your-feature>-eval-strategy.md` from
`playbook/eval-strategy-template.md` for a real feature on your team. Then:
- Get feedback from one teammate and one non-engineer (PM or domain expert).
- Pick the first concrete step and put it on your team's board.
