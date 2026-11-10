"""Run the triage eval.

Examples (run from the labs/ folder):
    uv run python run_eval.py --mock                     # free, offline
    uv run python run_eval.py --mock --trials 5          # see nondeterminism
    uv run python run_eval.py --prompt triage_v1         # real Claude calls
    uv run python run_eval.py --prompt triage_v2 --data data/tickets_holdout.jsonl
    uv run python run_eval.py --tag injection --no-judge
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from evalkit import app, graders
from evalkit.llm import MODEL
from evalkit.stats import bootstrap_ci, mean, percentile

HERE = Path(__file__).resolve().parent


def load_cases(path: Path, tag: str | None, limit: int | None) -> list[dict]:
    cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if tag:
        cases = [c for c in cases if tag in c.get("tags", [])]
    return cases[:limit] if limit else cases


def run_one(case: dict, trial: int, args) -> dict:
    rec = {"case_id": case["id"], "trial": trial, "tags": case.get("tags", []), "input": case["input"]}
    cost, latency = 0.0, 0.0
    try:
        out, usage = app.triage(case["input"], args.prompt, mock=args.mock, seed=trial)
        cost += usage.cost_usd
        latency = usage.latency_s
        grades = [g(case, out) for g in graders.CODE_GRADERS]
        if not args.no_judge:
            g, judge_usage = graders.grade_reply_judge(case, out, mock=args.mock)
            grades.append(g)
            cost += judge_usage.cost_usd
        rec.update(output=out, grades=[g.to_dict() for g in grades], error=None)
    except Exception as e:  # an error is a failed case, not a skipped one
        rec.update(output=None, grades=[], error=f"{type(e).__name__}: {e}")
    rec["all_passed"] = rec["error"] is None and all(g["passed"] for g in rec["grades"])
    rec.update(cost_usd=cost, latency_s=latency)
    return rec


def summarize(records: list[dict], trials: int) -> dict:
    by_case = defaultdict(list)
    for r in records:
        by_case[r["case_id"]].append(r)

    # Per-grader: average per case first (so every case counts once), then CI across cases.
    grader_names = sorted({g["name"] for r in records for g in r["grades"]})
    graders_summary = {}
    for name in grader_names:
        per_case_pass = []
        per_case_score = []
        for rs in by_case.values():
            gs = [g for r in rs for g in r["grades"] if g["name"] == name]
            if gs:
                per_case_pass.append(mean(g["passed"] for g in gs))
                per_case_score.append(mean(g["score"] for g in gs))
        graders_summary[name] = {
            "pass_rate": mean(per_case_pass),
            "pass_rate_ci95": bootstrap_ci(per_case_pass),
            "mean_score": mean(per_case_score),
        }

    overall = [mean(r["all_passed"] for r in rs) for rs in by_case.values()]
    tags = defaultdict(list)
    for rs in by_case.values():
        for t in rs[0]["tags"]:
            tags[t].append(mean(r["all_passed"] for r in rs))

    summary = {
        "n_cases": len(by_case),
        "trials": trials,
        "overall_pass_rate": mean(overall),
        "overall_ci95": bootstrap_ci(overall),
        "graders": graders_summary,
        "by_tag": {t: {"n": len(v), "pass_rate": mean(v)} for t, v in sorted(tags.items())},
        "errors": sum(r["error"] is not None for r in records),
        "total_cost_usd": sum(r["cost_usd"] for r in records),
        "latency_p50_s": percentile([r["latency_s"] for r in records], 50),
        "latency_p95_s": percentile([r["latency_s"] for r in records], 95),
    }
    if trials > 1:
        # pass@k: passed at least once. pass^k: passed EVERY time (what users feel).
        summary["pass_at_k"] = mean(any(r["all_passed"] for r in rs) for rs in by_case.values())
        summary["pass_hat_k"] = mean(all(r["all_passed"] for r in rs) for rs in by_case.values())
    return summary


def print_report(summary: dict, records: list[dict], args) -> None:
    pct = lambda x: f"{100 * x:5.1f}%"
    lo, hi = summary["overall_ci95"]
    print(f"\n=== {args.prompt} on {args.data.name} | model={'mock' if args.mock else MODEL} ===")
    print(f"cases={summary['n_cases']} trials={summary['trials']} errors={summary['errors']}")
    print(f"\nOVERALL (all graders pass): {pct(summary['overall_pass_rate'])}   95% CI [{pct(lo)}, {pct(hi)}]")
    if "pass_at_k" in summary:
        print(f"pass@{args.trials} (ever passed): {pct(summary['pass_at_k'])}   "
              f"pass^{args.trials} (always passed): {pct(summary['pass_hat_k'])}")

    print("\nPer grader:            pass rate   95% CI            mean score")
    for name, g in summary["graders"].items():
        lo, hi = g["pass_rate_ci95"]
        print(f"  {name:<20} {pct(g['pass_rate'])}   [{pct(lo)}, {pct(hi)}]   {g['mean_score']:.2f}")

    print("\nBy tag:")
    for t, v in summary["by_tag"].items():
        print(f"  {t:<16} n={v['n']:<3} {pct(v['pass_rate'])}")

    print(f"\nCost: ${summary['total_cost_usd']:.4f}   "
          f"latency p50={summary['latency_p50_s']:.2f}s p95={summary['latency_p95_s']:.2f}s")

    failures = [r for r in records if not r["all_passed"]]
    if failures:
        print(f"\nFailures ({len(failures)}) - READ THESE, the numbers alone won't teach you much:")
        for r in failures[: args.show]:
            print(f"\n  [{r['case_id']} trial {r['trial']}] {r['input'][:90]}")
            if r["error"]:
                print(f"    ERROR: {r['error']}")
                continue
            for g in r["grades"]:
                if not g["passed"]:
                    print(f"    x {g['name']}: {g['detail'][:160]}")
            print(f"    reply: {r['output']['reply'][:160]}")
        if len(failures) > args.show:
            print(f"\n  ... {len(failures) - args.show} more in the results file")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prompt", default="triage_v1", help="prompt file name in prompts/ (no .txt)")
    p.add_argument("--data", type=Path, default=HERE / "data" / "tickets.jsonl")
    p.add_argument("--mock", action="store_true", help="use the free offline mock model and judge")
    p.add_argument("--trials", type=int, default=1, help="runs per case (to measure variance)")
    p.add_argument("--tag", help="only run cases with this tag")
    p.add_argument("--limit", type=int, help="only run the first N cases")
    p.add_argument("--no-judge", action="store_true", help="skip the LLM-as-judge grader")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--show", type=int, default=8, help="how many failures to print")
    args = p.parse_args(argv)
    if not args.data.is_absolute():
        args.data = (Path.cwd() / args.data).resolve()

    cases = load_cases(args.data, args.tag, args.limit)
    if not cases:
        sys.exit("No cases matched.")
    jobs = [(c, t) for c in cases for t in range(args.trials)]
    if not args.mock:
        print(f"Running {len(jobs)} calls to {MODEL} (+ judge calls unless --no-judge). Ctrl-C to abort.")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(lambda job: run_one(job[0], job[1], args), jobs))

    summary = summarize(records, args.trials)
    print_report(summary, records, args)

    results_dir = HERE / "results"
    results_dir.mkdir(exist_ok=True)
    stem = f"{time.strftime('%Y%m%d-%H%M%S')}_{args.prompt}_{args.data.stem}{'_mock' if args.mock else ''}"
    (results_dir / f"{stem}.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")
    (results_dir / f"{stem}.summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nSaved results/{stem}.jsonl")


if __name__ == "__main__":
    main()
