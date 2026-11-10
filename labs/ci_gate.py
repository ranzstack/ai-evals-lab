"""CI eval gate: run the smoke eval and decide whether a change may merge.

    uv run python ci_gate.py                     # gate against the committed baseline
    uv run python ci_gate.py --update-baseline   # record a new baseline (commit it!)
    uv run python ci_gate.py --real --limit 10   # real Claude API (costs money; needs ANTHROPIC_API_KEY)

Eval concepts this applies (see curriculum/08-production.md):
  1. GUARDRAILS ARE HARD GATES: any case that passed the policy grader in the
     baseline and fails it now blocks the merge. So does any errored case.
  2. QUALITY GATES MUST CLEAR THE NOISE: block only if the overall pass rate
     drops by more than --max-drop points AND the paired 95% CI on the
     per-case delta is entirely below zero. Raw deltas on 20 cases are noise.
  3. PAIRED COMPARISON: candidate vs baseline on the SAME cases (Module 5).
  4. READ THE REGRESSIONS: the report lists every case that got worse,
     even when the gate passes.
  5. GRADER/DATASET CHANGES RESET THE BASELINE: the baseline stores a
     fingerprint of the graders and dataset; if they changed, the gate fails
     and asks you to re-record the baseline in the same PR (so a reviewer
     sees the baseline diff).

Exit code 0 = pass, 1 = blocked. That's how CI knows to fail the check.
"""

from __future__ import annotations

import argparse
import hashlib  # for fingerprinting files (sha256)
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace  # a quick "object with attributes", like a plain JS object

import run_eval
from evalkit.stats import mean, paired_bootstrap_delta

HERE = Path(__file__).resolve().parent
BASELINE = HERE / "baselines" / "smoke_baseline.json"
DATA = HERE / "data" / "tickets.jsonl"
# Files that define WHAT is measured. If any change, old scores aren't comparable.
FINGERPRINT_FILES = [HERE / "evalkit" / "graders.py", DATA]


def fingerprint() -> str:
    # Hash the contents of the grader code + dataset into one short string.
    h = hashlib.sha256()
    for f in FINGERPRINT_FILES:
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def run_smoke(args) -> list[dict]:
    """Run the eval in-process and return the raw records (one per case x trial)."""
    cases = run_eval.load_cases(DATA, None, args.limit)
    # run_one expects an `args` object with these attributes, like the CLI's.
    run_args = SimpleNamespace(prompt=args.prompt, mock=not args.real, no_judge=True)
    return [run_eval.run_one(c, t, run_args) for c in cases for t in range(args.trials)]


def per_case(records: list[dict], grader: str | None = None) -> dict[str, float]:
    """{case_id: fraction of trials that passed}. grader=None means 'all graders passed'."""
    by = defaultdict(list)
    for r in records:
        if grader is None:
            by[r["case_id"]].append(r["all_passed"])
        else:
            # An errored record has no grades, so treat it as a failure.
            passed = next((g["passed"] for g in r["grades"] if g["name"] == grader), False)
            by[r["case_id"]].append(passed)
    return {cid: mean(v) for cid, v in by.items()}


def gate(base: dict, cand_records: list[dict], max_drop: float) -> tuple[bool, list[str], list[str]]:
    """Return (ok, blocking_reasons, report_lines)."""
    blocks, lines = [], []
    base_records = base["records"]

    # --- 0. Is the baseline still comparable? ---
    if base["fingerprint"] != fingerprint():
        blocks.append("Graders or dataset changed since the baseline was recorded. "
                      "Run `uv run python ci_gate.py --update-baseline` and commit the new baseline in this PR.")
        return False, blocks, lines

    # --- 1. Hard guardrails ---
    errors = [r["case_id"] for r in cand_records if r["error"]]
    if errors:
        blocks.append(f"{len(errors)} errored runs (errors count as failures): {sorted(set(errors))}")

    pol_a, pol_b = per_case(base_records, "policy"), per_case(cand_records, "policy")
    policy_regressions = [c for c in pol_a if c in pol_b and pol_b[c] < pol_a[c]]
    if policy_regressions:
        blocks.append(f"Policy guardrail regressed on: {policy_regressions}")

    # --- 2. Quality, judged against the noise (paired) ---
    a, b = per_case(base_records), per_case(cand_records)
    shared = sorted(set(a) & set(b))
    xa, xb = [a[c] for c in shared], [b[c] for c in shared]
    delta, (lo, hi) = paired_bootstrap_delta(xa, xb)
    lines.append(f"Overall pass rate: {mean(xa):.1%} -> {mean(xb):.1%}  "
                 f"(delta {delta:+.1%}, paired 95% CI [{lo:+.1%}, {hi:+.1%}], n={len(shared)} cases)")
    if delta < -max_drop and hi < 0:
        blocks.append(f"Quality dropped {delta:+.1%} (more than {max_drop:.0%}) and the CI excludes zero.")
    elif delta < 0:
        lines.append("Quality dipped, but within noise / threshold: not blocking. Read the regressions below.")

    # --- 3. Per-grader table + regressed cases (always shown) ---
    lines.append("")
    lines.append("| grader | baseline | candidate |")
    lines.append("|---|---|---|")
    for g in sorted({g["name"] for r in base_records for g in r["grades"]}):
        ga, gb = per_case(base_records, g), per_case(cand_records, g)
        lines.append(f"| {g} | {mean(ga[c] for c in shared):.0%} | {mean(gb[c] for c in shared):.0%} |")

    regressed = [c for c in shared if b[c] < a[c]]
    improved = [c for c in shared if b[c] > a[c]]
    lines.append("")
    lines.append(f"Improved ({len(improved)}): {', '.join(improved) or '-'}")
    lines.append(f"Regressed ({len(regressed)}): {', '.join(regressed) or '-'}")
    return not blocks, blocks, lines


def write_summary(text: str) -> None:
    # On GitHub Actions, anything written to $GITHUB_STEP_SUMMARY appears as
    # markdown on the run's summary page. Locally the variable isn't set.
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a") as f:  # "a" = append mode
            f.write(text + "\n")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--update-baseline", action="store_true", help="record the current results as the new baseline")
    p.add_argument("--trials", type=int, default=3, help="runs per case (more trials = less noise)")
    p.add_argument("--max-drop", type=float, default=0.05, help="quality drop that may block, e.g. 0.05 = 5 points")
    p.add_argument("--prompt", default="triage_v1")
    p.add_argument("--limit", type=int, help="only the first N cases (cost cap for --real)")
    p.add_argument("--real", action="store_true", help="use the real Claude API instead of the mock")
    args = p.parse_args(argv)

    records = run_smoke(args)
    summary = run_eval.summarize(records, args.trials)
    mode = "real" if args.real else "mock"
    print(f"Smoke eval ({mode}): {summary['n_cases']} cases x {args.trials} trials, "
          f"overall {summary['overall_pass_rate']:.1%}, cost ${summary['total_cost_usd']:.4f}")

    # Save the raw records so CI can upload them as an artifact ("save raw outputs").
    out = HERE / "results" / f"ci_{mode}.jsonl"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(json.dumps(r) for r in records) + "\n")

    if args.update_baseline:
        BASELINE.parent.mkdir(exist_ok=True)
        BASELINE.write_text(json.dumps({
            "fingerprint": fingerprint(),
            "config": {"prompt": args.prompt, "trials": args.trials, "mode": mode, "limit": args.limit},
            "summary": summary,
            "records": records,
        }, indent=1))
        print(f"Baseline written to {BASELINE.relative_to(HERE)}. Commit it.")
        return 0

    if not BASELINE.exists():
        print("No baseline yet. Run with --update-baseline first and commit it.")
        return 1

    base = json.loads(BASELINE.read_text())
    if base["config"]["mode"] != mode:
        print(f"Baseline was recorded in {base['config']['mode']} mode; this run is {mode}. "
              "Comparing them would be meaningless.")
        return 1

    ok, blocks, lines = gate(base, records, args.max_drop)
    verdict = "PASS" if ok else "BLOCKED"
    report = "\n".join([f"## AI eval gate: {verdict}", ""]
                       + [f"- :x: {b}" for b in blocks] + ([""] if blocks else []) + lines)
    print("\n" + report)
    write_summary(report)
    return 0 if ok else 1  # non-zero exit fails the CI step


if __name__ == "__main__":
    sys.exit(main())
