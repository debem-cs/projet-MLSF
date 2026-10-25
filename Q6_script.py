"""Question 6: run sat.py in both modes on the 41 public instances.

Output: results/Q6_runs.json and results/Q6_summary.txt. One run each, limit 60
seconds, an answer being correct as in the competition: right status and, for a
satisfiable formula, a model that satisfies every clause.
"""

import argparse
import json
import os
from pathlib import Path

import benchmark

os.chdir(Path(__file__).resolve().parent)
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--timeout", type=int, default=60)
parser.add_argument("--workers", type=int, default=8)
args = parser.parse_args()

benchmark.run_cli(RESULTS / "Q6_runs.json", args.timeout, args.workers)
runs = json.loads((RESULTS / "Q6_runs.json").read_text())

by_instance = {}
for run in runs:
    by_instance.setdefault(run["instance"], {})[run["mode"]] = run
lines = []


def log(text=""):
    print(text)
    lines.append(text)


log(f"{len(runs)} runs, limit {args.timeout} s")
for mode in ("dpll", "optimized"):
    rs = [r for r in runs if r["mode"] == mode]
    good = [r for r in rs if r["correct"]]
    wrong = [r for r in rs if not r["correct"] and r["answer"] != "TIMEOUT"]
    log(f"{mode:10s} correct {len(good)} of {len(rs)}, total time of these answers "
        f"{sum(r['time'] for r in good):.1f} s, wrong answers {len(wrong)}")
    log(f"           not solved: {', '.join(r['instance'] for r in rs if not r['correct'])}")

both = [i for i, modes in by_instance.items() if all(m["correct"] for m in modes.values())]
log(f"solved by both modes: {len(both)}")
for mode in ("dpll", "optimized"):
    log(f"  {mode:10s} time on these {sum(by_instance[i][mode]['time'] for i in both):.1f} s")
for mode in ("dpll", "optimized"):
    slowest = sorted(((by_instance[i][mode]["time"], i) for i in by_instance
                      if by_instance[i][mode]["correct"]), reverse=True)[:3]
    log(f"slowest answers of {mode}: " + ", ".join(f"{i} {t:.1f} s" for t, i in slowest))

(RESULTS / "Q6_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
