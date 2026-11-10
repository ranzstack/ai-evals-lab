"""Run the triage eval.

Examples (run from the labs/ folder):
    uv run python run_eval.py --mock                     # free, offline
    uv run python run_eval.py --mock --trials 5          # see nondeterminism
    uv run python run_eval.py --prompt triage_v1         # real Claude calls
    uv run python run_eval.py --prompt triage_v2 --data data/tickets_holdout.jsonl
    uv run python run_eval.py --tag injection --no-judge
"""

# The big picture of this script:
#   load_cases()    read the dataset             (DATASET)
#   run_one()       run the task + graders once  (TASK + GRADERS)
#   summarize()     aggregate into pass rates    (METRICS)
#   print_report()  show numbers AND failures
#   main()          parse command-line flags, run everything, save results

from __future__ import annotations

import argparse  # parses command-line flags like --mock (similar to yargs/commander in Node)
import json
import sys
import time
from collections import defaultdict  # a dict that creates a default value for missing keys
from concurrent.futures import ThreadPoolExecutor  # runs several cases at the same time
from pathlib import Path

from evalkit import app, graders
from evalkit.llm import MODEL
from evalkit.stats import bootstrap_ci, mean, percentile

HERE = Path(__file__).resolve().parent  # the labs/ folder, wherever you run the script from


def load_cases(path: Path, tag: str | None, limit: int | None) -> list[dict]:
    # `str | None` means "a string, or None". JSONL = one JSON object per line,
    # so: read the file, split into lines, skip blank lines, parse each one.
    cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if tag:
        # Keep only cases with that tag. c.get("tags", []) avoids a crash if "tags" is missing.
        cases = [c for c in cases if tag in c.get("tags", [])]
    # cases[:limit] is "slicing": the first `limit` items, like cases.slice(0, limit).
    return cases[:limit] if limit else cases


def run_one(case: dict, trial: int, args) -> dict:
    # A "record" is everything about one run of one case. It's saved to the
    # results file, so you can re-read or re-grade it later.
    rec = {"case_id": case["id"], "trial": trial, "tags": case.get("tags", []), "input": case["input"]}
    cost, latency = 0.0, 0.0  # assign two variables at once
    try:
        # TASK: run the system under test. The trial number is used as the seed,
        # so trial 0, 1, 2... behave like separate runs.
        out, usage = app.triage(case["input"], args.prompt, mock=args.mock, seed=trial)
        cost += usage.cost_usd
        latency = usage.latency_s
        # GRADERS: call every code grader on this output. g is each function in turn.
        grades = [g(case, out) for g in graders.CODE_GRADERS]
        if not args.no_judge:
            g, judge_usage = graders.grade_reply_judge(case, out, mock=args.mock)
            grades.append(g)
            cost += judge_usage.cost_usd
        # .update() merges keys into the dict, like Object.assign(rec, {...}).
        rec.update(output=out, grades=[g.to_dict() for g in grades], error=None)
    except Exception as e:  # an error is a failed case, not a skipped one
        # type(e).__name__ is the error's class name, e.g. "TimeoutError".
        rec.update(output=None, grades=[], error=f"{type(e).__name__}: {e}")
    # all(...) is True only if every item is True, like grades.every(g => g.passed).
    rec["all_passed"] = rec["error"] is None and all(g["passed"] for g in rec["grades"])
    rec.update(cost_usd=cost, latency_s=latency)
    return rec


def summarize(records: list[dict], trials: int) -> dict:
    # Group records by case: {"t001": [trial0, trial1, ...], "t002": [...]}.
    # defaultdict(list) means a missing key starts as an empty list, so we can append straight away.
    by_case = defaultdict(list)
    for r in records:
        by_case[r["case_id"]].append(r)

    # Per-grader: average per case first (so every case counts once), then CI across cases.
    # {... for ...} with single values builds a set (unique grader names).
    grader_names = sorted({g["name"] for r in records for g in r["grades"]})
    graders_summary = {}
    for name in grader_names:
        per_case_pass = []
        per_case_score = []
        for rs in by_case.values():  # rs = all trials of one case
            # A comprehension with two `for`s flattens nested loops:
            # for each record r, for each grade g in r, keep the ones named `name`.
            gs = [g for r in rs for g in r["grades"] if g["name"] == name]
            if gs:
                per_case_pass.append(mean(g["passed"] for g in gs))
                per_case_score.append(mean(g["score"] for g in gs))
        graders_summary[name] = {
            "pass_rate": mean(per_case_pass),
            "pass_rate_ci95": bootstrap_ci(per_case_pass),
            "mean_score": mean(per_case_score),
        }

    # Overall = the fraction of trials where EVERY grader passed, averaged per case.
    overall = [mean(r["all_passed"] for r in rs) for rs in by_case.values()]
    tags = defaultdict(list)
    for rs in by_case.values():
        for t in rs[0]["tags"]:  # every trial of a case has the same tags, so read trial 0's
            tags[t].append(mean(r["all_passed"] for r in rs))

    summary = {
        "n_cases": len(by_case),
        "trials": trials,
        "overall_pass_rate": mean(overall),
        "overall_ci95": bootstrap_ci(overall),
        "graders": graders_summary,
        # A dict comprehension: {key: value for ...}. sorted(dict.items()) gives (key, value) pairs in order.
        "by_tag": {t: {"n": len(v), "pass_rate": mean(v)} for t, v in sorted(tags.items())},
        "errors": sum(r["error"] is not None for r in records),  # summing True/False counts the Trues
        "total_cost_usd": sum(r["cost_usd"] for r in records),
        "latency_p50_s": percentile([r["latency_s"] for r in records], 50),
        "latency_p95_s": percentile([r["latency_s"] for r in records], 95),
    }
    if trials > 1:
        # pass@k: passed at least once. pass^k: passed EVERY time (what users feel).
        # any() = .some(), all() = .every()
        summary["pass_at_k"] = mean(any(r["all_passed"] for r in rs) for rs in by_case.values())
        summary["pass_hat_k"] = mean(all(r["all_passed"] for r in rs) for rs in by_case.values())
    return summary


def print_report(summary: dict, records: list[dict], args) -> None:
    # `lambda x: ...` is a one-line anonymous function, like (x) => ... in JS.
    # {100 * x:5.1f} formats a number 5 characters wide with 1 decimal place.
    pct = lambda x: f"{100 * x:5.1f}%"
    lo, hi = summary["overall_ci95"]
    print(f"\n=== {args.prompt} on {args.data.name} | model={'mock' if args.mock else MODEL} ===")
    print(f"cases={summary['n_cases']} trials={summary['trials']} errors={summary['errors']}")
    print(f"\nOVERALL (all graders pass): {pct(summary['overall_pass_rate'])}   95% CI [{pct(lo)}, {pct(hi)}]")
    if "pass_at_k" in summary:  # `key in dict` checks whether the key exists
        print(f"pass@{args.trials} (ever passed): {pct(summary['pass_at_k'])}   "
              f"pass^{args.trials} (always passed): {pct(summary['pass_hat_k'])}")

    print("\nPer grader:            pass rate   95% CI            mean score")
    for name, g in summary["graders"].items():  # .items() gives (key, value) pairs
        lo, hi = g["pass_rate_ci95"]
        # {name:<20} left-aligns the text in a 20-character column.
        print(f"  {name:<20} {pct(g['pass_rate'])}   [{pct(lo)}, {pct(hi)}]   {g['mean_score']:.2f}")

    print("\nBy tag:")
    for t, v in summary["by_tag"].items():
        print(f"  {t:<16} n={v['n']:<3} {pct(v['pass_rate'])}")

    print(f"\nCost: ${summary['total_cost_usd']:.4f}   "
          f"latency p50={summary['latency_p50_s']:.2f}s p95={summary['latency_p95_s']:.2f}s")

    failures = [r for r in records if not r["all_passed"]]
    if failures:
        print(f"\nFailures ({len(failures)}) - READ THESE, the numbers alone won't teach you much:")
        for r in failures[: args.show]:  # only the first `--show` failures
            print(f"\n  [{r['case_id']} trial {r['trial']}] {r['input'][:90]}")  # [:90] = first 90 characters
            if r["error"]:
                print(f"    ERROR: {r['error']}")
                continue  # skip to the next failure
            for g in r["grades"]:
                if not g["passed"]:
                    print(f"    x {g['name']}: {g['detail'][:160]}")
            print(f"    reply: {r['output']['reply'][:160]}")
        if len(failures) > args.show:
            print(f"\n  ... {len(failures) - args.show} more in the results file")


def main(argv=None):
    # Define the command-line flags. argv=None means "read the real command line";
    # the notebooks pass a list instead, e.g. main(["--mock", "--limit", "5"]).
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prompt", default="triage_v1", help="prompt file name in prompts/ (no .txt)")
    p.add_argument("--data", type=Path, default=HERE / "data" / "tickets.jsonl")
    p.add_argument("--mock", action="store_true", help="use the free offline mock model and judge")  # store_true = a boolean flag
    p.add_argument("--trials", type=int, default=1, help="runs per case (to measure variance)")
    p.add_argument("--tag", help="only run cases with this tag")
    p.add_argument("--limit", type=int, help="only run the first N cases")
    p.add_argument("--no-judge", action="store_true", help="skip the LLM-as-judge grader")  # becomes args.no_judge
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--show", type=int, default=8, help="how many failures to print")
    args = p.parse_args(argv)
    if not args.data.is_absolute():
        args.data = (Path.cwd() / args.data).resolve()

    # DATASET
    cases = load_cases(args.data, args.tag, args.limit)
    if not cases:
        sys.exit("No cases matched.")
    # One job per (case, trial) pair: 20 cases x 3 trials = 60 jobs.
    jobs = [(c, t) for c in cases for t in range(args.trials)]
    if not args.mock:
        print(f"Running {len(jobs)} calls to {MODEL} (+ judge calls unless --no-judge). Ctrl-C to abort.")

    # Run the jobs 4 at a time (--workers) in background threads. `with` makes sure
    # the pool is cleaned up afterwards, like try/finally. pool.map keeps the
    # results in the same order as `jobs`.
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(lambda job: run_one(job[0], job[1], args), jobs))

    # METRICS + report
    summary = summarize(records, args.trials)
    print_report(summary, records, args)

    # Save the raw records and the summary. The filename records the date, prompt
    # and dataset, so you can always tell which run is which.
    results_dir = HERE / "results"
    results_dir.mkdir(exist_ok=True)  # exist_ok=True: don't fail if the folder already exists
    stem = f"{time.strftime('%Y%m%d-%H%M%S')}_{args.prompt}_{args.data.stem}{'_mock' if args.mock else ''}"
    (results_dir / f"{stem}.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")  # json.dumps = JSON.stringify
    (results_dir / f"{stem}.summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nSaved results/{stem}.jsonl")


# This block only runs when you execute the file directly (python run_eval.py),
# not when another file imports it (like the notebooks do). It's similar to
# `if (require.main === module)` in Node.
if __name__ == "__main__":
    main()
