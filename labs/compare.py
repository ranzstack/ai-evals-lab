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


def load(path: str) -> dict[str, list[dict]]:
    by_case = defaultdict(list)
    for line in Path(path).read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            by_case[r["case_id"]].append(r)
    return by_case


def case_score(rs: list[dict], grader: str | None = None) -> float:
    if grader is None:
        return mean(r["all_passed"] for r in rs)
    vals = [g["passed"] for r in rs for g in r["grades"] if g["name"] == grader]
    return mean(vals) if vals else float("nan")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    a, b = load(sys.argv[1]), load(sys.argv[2])
    shared = sorted(set(a) & set(b))
    if len(shared) < len(set(a) | set(b)):
        print(f"Note: comparing only the {len(shared)} cases present in both runs.")

    pct = lambda x: f"{100 * x:+.1f}pp"
    xa = [case_score(a[c]) for c in shared]
    xb = [case_score(b[c]) for c in shared]
    delta, (lo, hi) = paired_bootstrap_delta(xa, xb)
    print(f"\nOVERALL pass rate: {100*mean(xa):.1f}% -> {100*mean(xb):.1f}%   "
          f"delta {pct(delta)}  95% CI [{pct(lo)}, {pct(hi)}]")
    verdict = "significant" if lo > 0 or hi < 0 else "NOT distinguishable from noise"
    print(f"  -> {verdict} at n={len(shared)} cases")

    graders = sorted({g["name"] for rs in a.values() for r in rs for g in r["grades"]})
    print("\nPer grader:")
    for g in graders:
        ga = [case_score(a[c], g) for c in shared]
        gb = [case_score(b[c], g) for c in shared]
        d, (l, h) = paired_bootstrap_delta(ga, gb)
        print(f"  {g:<12} {100*mean(ga):5.1f}% -> {100*mean(gb):5.1f}%   {pct(d)} [{pct(l)}, {pct(h)}]")

    regressions = [c for c in shared if case_score(b[c]) < case_score(a[c])]
    improvements = [c for c in shared if case_score(b[c]) > case_score(a[c])]
    print(f"\nImproved ({len(improvements)}): {', '.join(improvements) or '-'}")
    print(f"Regressed ({len(regressions)}): {', '.join(regressions) or '-'}")
    for c in regressions:
        r = b[c][0]
        failed = [f"{g['name']}({g['detail'][:60]})" for g in r["grades"] if not g["passed"]]
        print(f"  {c}: {r['input'][:70]}\n      now failing: {'; '.join(failed) or r['error']}")


if __name__ == "__main__":
    main()
