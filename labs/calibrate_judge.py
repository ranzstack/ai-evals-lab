"""Calibrate the LLM judge against YOUR judgement (Lab 3).

Step 1 - export replies for you to label:
    uv run python calibrate_judge.py export results/<run>.jsonl
  -> writes data/labels/to_label.jsonl. Open it and fill in "human_score"
     (1-5, using the rubric in evalkit/graders.py) for every line.
     Don't look at judge_score while you label! (It's hidden in the file
     on purpose - see the "_judge" field only after you're done.)

Step 2 - measure agreement:
    uv run python calibrate_judge.py score data/labels/to_label.jsonl

A judge you can trust for gating typically agrees with humans on pass/fail
(score >= 4) at least ~85-90% of the time, with kappa > 0.6. If not: fix the
rubric, add examples to the judge prompt, or switch to a code-based check.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from evalkit.stats import cohens_kappa

HERE = Path(__file__).resolve().parent


def export(results_path: str):
    # STEP 1: write one row per case (trial 0 only) for a human to score blind.
    out_dir = HERE / "data" / "labels"
    out_dir.mkdir(parents=True, exist_ok=True)  # like `mkdir -p`
    rows = []
    for line in Path(results_path).read_text().splitlines():
        r = json.loads(line)
        if r["error"] or r["trial"] != 0:
            continue  # skip errored runs and repeat trials
        # Find the judge's grade in this record. next(..., None) returns None
        # if there isn't one, like grades.find(...) ?? null in JS.
        judge = next((g for g in r["grades"] if g["name"] == "judge"), None)
        if judge is None:
            sys.exit("This run has no judge grades. Re-run without --no-judge.")
        rows.append({
            "case_id": r["case_id"],
            "ticket": r["input"],
            "reply": r["output"]["reply"],
            "human_score": None,
            "_judge": judge["detail"],  # scroll past this while labelling
        })
    path = out_dir / "to_label.jsonl"
    # ensure_ascii=False keeps characters like "sesión" readable in the file instead of \u escapes.
    path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n")
    print(f"Wrote {len(rows)} rows to {path.relative_to(HERE)}. Fill in human_score (1-5) for each.")


def score(labels_path: str):
    # STEP 2: compare your scores with the judge's scores.
    rows = [json.loads(l) for l in Path(labels_path).read_text().splitlines() if l.strip()]
    rows = [r for r in rows if r.get("human_score") is not None]  # only rows you've labelled
    if not rows:
        sys.exit("No human_score values filled in yet.")
    human = [int(r["human_score"]) for r in rows]
    # The judge's detail looks like "4/5 - has next step". The regex grabs the first digit.
    judge = [int(re.match(r"(\d)", r["_judge"]).group(1)) for r in rows]
    # Turn 1-5 scores into pass/fail (4 or above passes), for both you and the judge.
    hp = [h >= 4 for h in human]
    jp = [j >= 4 for j in judge]

    n = len(rows)
    print(f"\nLabelled rows: {n}")
    print(f"Exact score agreement:      {sum(h == j for h, j in zip(human, judge)) / n:.0%}")
    print(f"Within 1 point:             {sum(abs(h - j) <= 1 for h, j in zip(human, judge)) / n:.0%}")
    print(f"Pass/fail agreement:        {sum(a == b for a, b in zip(hp, jp)) / n:.0%}")
    # Kappa corrects for agreement you'd get by chance. Raw agreement alone can mislead.
    print(f"Cohen's kappa (pass/fail):  {cohens_kappa(hp, jp):.2f}")
    print(f"Judge more lenient on {sum(j > h for h, j in zip(human, judge))} rows, "
          f"stricter on {sum(j < h for h, j in zip(human, judge))}.")

    print("\nDisagreements on pass/fail (study these to improve the rubric):")
    for r, h, j in zip(rows, human, judge):
        if (h >= 4) != (j >= 4):  # you and the judge disagree on pass/fail
            print(f"  {r['case_id']}: you={h} judge={j}\n    reply: {r['reply'][:120]}\n    judge said: {r['_judge'][:160]}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in {"export", "score"}:
        sys.exit(__doc__)
    # Pick the function by name from a dict and call it. It's equivalent to:
    #   if sys.argv[1] == "export": export(sys.argv[2])
    #   else: score(sys.argv[2])
    {"export": export, "score": score}[sys.argv[1]](sys.argv[2])
