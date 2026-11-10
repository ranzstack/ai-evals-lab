"""Small helpers shared by the lesson notebooks (labs/lesson_*.ipynb).

They wrap the same harness the CLI uses (evalkit + run_eval.summarize), so the
notebooks show the real machinery rather than a parallel copy of it.
Everything defaults to the free, offline mock model.
"""

from __future__ import annotations

import json
from pathlib import Path

import run_eval
from evalkit import app, graders

HERE = Path(__file__).resolve().parent  # the labs/ folder
DEV = HERE / "data" / "tickets.jsonl"
HOLDOUT = HERE / "data" / "tickets_holdout.jsonl"


def load(path: Path = DEV) -> list[dict]:
    """Load a JSONL dataset of cases."""
    # One JSON object per line: split into lines, skip blanks, parse each (json.loads = JSON.parse).
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def mock_task(text: str, seed: int = 0) -> dict:
    """The default system under test: the free keyword-rule mock model."""
    return app.mock_triage(text, seed=seed)


# `task=mock_task` passes a FUNCTION as a default argument. Functions are values
# in Python, so you can hand run() any function with the same shape to test it.
def run(cases: list[dict], trials: int = 1, task=mock_task) -> list[dict]:
    """Run every case `trials` times through `task`, then through the code graders.

    `task(text, seed=...)` must return {"category", "priority", "reply"}.
    Errors are recorded as FAILED cases, never skipped (same rule as run_eval.py).
    """
    records = []
    for case in cases:  # every case...
        for trial in range(trials):  # ...run `trials` times. range(3) = 0, 1, 2
            rec = {"case_id": case["id"], "trial": trial, "tags": case.get("tags", []),
                   "input": case["input"], "expected": case["expected"],
                   "cost_usd": 0.0, "latency_s": 0.0}
            try:
                # TASK: the trial number doubles as the random seed, so each trial is a different "run".
                out = task(case["input"], seed=trial)
                grades = [g(case, out) for g in graders.CODE_GRADERS]  # GRADERS: every code grader
                rec.update(output=out, grades=[g.to_dict() for g in grades], error=None)
            except Exception as e:  # a crash becomes a recorded failure, never a skip
                rec.update(output=None, grades=[], error=f"{type(e).__name__}: {e}")
            rec["all_passed"] = rec["error"] is None and all(g["passed"] for g in rec["grades"])
            records.append(rec)
    return records


def report(records: list[dict], trials: int = 1, label: str = "") -> dict:
    """Print a one-line summary and return run_eval.summarize()'s full dict."""
    s = run_eval.summarize(records, trials)  # METRICS: the same function the CLI uses
    lo, hi = s["overall_ci95"]
    per = "  ".join(f"{k}={v['pass_rate']:.0%}" for k, v in s["graders"].items())
    extra = ""
    if "pass_at_k" in s:
        extra = f"  pass@{trials}={s['pass_at_k']:.0%} pass^{trials}={s['pass_hat_k']:.0%}"
    print(f"{label:<12} n={s['n_cases']:<3} overall={s['overall_pass_rate']:4.0%} "
          f"CI[{lo:.0%},{hi:.0%}]  {per}{extra}")
    return s


def failures(records: list[dict]) -> None:
    """Print the failed records with the reason each grader gave."""
    bad = [r for r in records if not r["all_passed"]]  # keep only the failed records
    print(f"{len(bad)} failures out of {len(records)}\n")
    for r in bad:
        print(f"[{r['case_id']} t{r['trial']}] {', '.join(r['tags'])}: {r['input'][:80]}")
        if r["error"]:
            print(f"   ERROR {r['error']}")
        for g in r["grades"]:
            if not g["passed"]:
                print(f"   x {g['name']}: {g['detail'][:120]}")
