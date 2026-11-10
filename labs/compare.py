"""Compare two eval runs case-by-case (Lab 4/5).

    uv run python compare.py results/<baseline>.jsonl results/<candidate>.jsonl

Shows: overall delta with a paired-bootstrap confidence interval, per-grader
deltas, and the specific cases that regressed or improved. A change "wins"
only if the CI on the delta excludes 0 AND no important case regressed.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from evalkit.stats import mean, paired_bootstrap_delta

# Usage: compare a BASELINE run (a) with a CANDIDATE run (b) of the same cases.
# The key idea is PAIRING: we compare each case with itself across the two runs.


def load(path: str) -> dict[str, list[dict]]:
    # Read a results .jsonl file and group its records by case:
    # {"t001": [trial0, trial1, ...], ...}. defaultdict(list) starts missing keys as [].
    by_case = defaultdict(list)
    for line in Path(path).read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            by_case[r["case_id"]].append(r)
    return by_case


def case_score(rs: list[dict], grader: str | None = None) -> float:
    # One number per case: the fraction of its trials that passed.
    # With no grader name, "passed" means all graders passed; otherwise just that grader.
    if grader is None:
        return mean(r["all_passed"] for r in rs)
    vals = [g["passed"] for r in rs for g in r["grades"] if g["name"] == grader]
    return mean(vals) if vals else float("nan")


def main():
    # sys.argv is the command line as a list, like process.argv in Node:
    # ["compare.py", "baseline.jsonl", "candidate.jsonl"]
    if len(sys.argv) != 3:
        sys.exit(__doc__)  # print the usage text at the top of the file and stop
    a, b = load(sys.argv[1]), load(sys.argv[2])
    # set(a) is the set of case IDs in run a. & = intersection (in both), | = union (in either).
    shared = sorted(set(a) & set(b))
    if len(shared) < len(set(a) | set(b)):
        print(f"Note: comparing only the {len(shared)} cases present in both runs.")

    # pp = percentage points. The + in :+.1f always shows the sign (+3.0 / -2.0).
    pct = lambda x: f"{100 * x:+.1f}pp"
    # xa[i] and xb[i] are the SAME case in the two runs. That's what makes it paired.
    xa = [case_score(a[c]) for c in shared]
    xb = [case_score(b[c]) for c in shared]
    delta, (lo, hi) = paired_bootstrap_delta(xa, xb)
    print(f"\nOVERALL pass rate: {100*mean(xa):.1f}% -> {100*mean(xb):.1f}%   "
          f"delta {pct(delta)}  95% CI [{pct(lo)}, {pct(hi)}]")
    # If the whole interval is above 0 (or below 0), the change is probably real.
    # If it straddles 0, you can't tell it apart from noise.
    verdict = "significant" if lo > 0 or hi < 0 else "NOT distinguishable from noise"
    print(f"  -> {verdict} at n={len(shared)} cases")

    graders = sorted({g["name"] for rs in a.values() for r in rs for g in r["grades"]})
    print("\nPer grader:")
    for g in graders:
        ga = [case_score(a[c], g) for c in shared]
        gb = [case_score(b[c], g) for c in shared]
        d, (l, h) = paired_bootstrap_delta(ga, gb)
        print(f"  {g:<12} {100*mean(ga):5.1f}% -> {100*mean(gb):5.1f}%   {pct(d)} [{pct(l)}, {pct(h)}]")

    # A net delta can hide breakage: always list WHICH cases got worse.
    regressions = [c for c in shared if case_score(b[c]) < case_score(a[c])]
    improvements = [c for c in shared if case_score(b[c]) > case_score(a[c])]
    print(f"\nImproved ({len(improvements)}): {', '.join(improvements) or '-'}")
    print(f"Regressed ({len(regressions)}): {', '.join(regressions) or '-'}")
    for c in regressions:
        r = b[c][0]  # show the candidate's first trial for this case
        failed = [f"{g['name']}({g['detail'][:60]})" for g in r["grades"] if not g["passed"]]
        print(f"  {c}: {r['input'][:70]}\n      now failing: {'; '.join(failed) or r['error']}")


# Only runs when executed directly (python compare.py ...), not when imported.
if __name__ == "__main__":
    main()
