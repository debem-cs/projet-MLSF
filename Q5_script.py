"""Question 5: measure the heuristics. Output: results/Q5_runs.json and results/Q5_summary.txt.

Every heuristic is run once on each of the 30 benchmark instances of the teachers
and on the 18 Meowdoku formulas, with a limit of 60 seconds per run.
"""

import argparse
import json
import os
from pathlib import Path

import benchmark
from sat import HEURISTIC_NAMES

os.chdir(Path(__file__).resolve().parent)
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--timeout", type=int, default=60)
parser.add_argument("--workers", type=int, default=10)
args = parser.parse_args()

benchmark.generate_instances()
benchmark.run_all(RESULTS / "Q5_runs.json", args.timeout, args.workers)
runs = json.loads((RESULTS / "Q5_runs.json").read_text())

instances = {}
for run in runs:
    instances.setdefault(run["instance"], {})[run["heuristic"]] = run
GROUPS = {
    "Public SAT": lambda i: i.startswith("public") and instances[i]["H0"]["expected"] == "SAT",
    "Public UNSAT": lambda i: i.startswith("public") and instances[i]["H0"]["expected"] == "UNSAT",
    "Meowdoku SAT": lambda i: i.startswith("sat-"),
    "Meowdoku UNSAT": lambda i: i.startswith("unsat-"),
}
solved = lambda i, h: instances[i][h]["status"] != "TIMEOUT"
lines = []


def log(text=""):
    print(text)
    lines.append(text)


wrong = [r for r in runs if r["status"] != "TIMEOUT"
         and (r["status"] != r["expected"] or not r["valid"])]
log(f"{len(runs)} runs, limit {args.timeout} s, wrong answers: {len(wrong)}")

log()
log("Instances solved")
log(f"{'':6s}" + "".join(f"{g + ' (' + str(sum(1 for i in instances if f(i))) + ')':>20s}"
                         for g, f in GROUPS.items()) + "    Total")
for h in HEURISTIC_NAMES:
    counts = [sum(solved(i, h) for i in instances if f(i)) for f in GROUPS.values()]
    log(f"{h:6s}" + "".join(f"{c:>20d}" for c in counts) + f"{sum(counts):>9d}")
log("Unsolved: " + "; ".join(
    f"{i} ({', '.join(h for h in HEURISTIC_NAMES if not solved(i, h))})"
    for i in sorted(instances) if not all(solved(i, h) for h in HEURISTIC_NAMES)))

common = {g: [i for i in instances if f(i) and all(solved(i, h) for h in HEURISTIC_NAMES)]
          for g, f in GROUPS.items()}
log()
log("Effort on the instances solved by all heuristics: "
    + ", ".join(f"{g} {len(c)}" for g, c in common.items()))
log(f"{'':6s}" + "".join(f"{g:>22s}" for g in GROUPS) + "   heuristic share  backtracks/decisions")
for h in HEURISTIC_NAMES:
    cells, cpu, share, decisions, backtracks = [], 0.0, 0.0, 0, 0
    for g in GROUPS:
        rs = [instances[i][h] for i in common[g]]
        d, c = sum(r["decisions"] for r in rs), sum(r["cpu"] for r in rs)
        cells.append(f"{d / 1000:8.1f}k {c:8.1f} s")
        cpu, share = cpu + c, share + sum(r["heuristic_time"] for r in rs)
        decisions, backtracks = decisions + d, backtracks + sum(r["backtracks"] for r in rs)
    log(f"{h:6s}" + "".join(f"{c:>22s}" for c in cells)
        + f"   {100 * share / cpu:13.1f} %   {100 * backtracks / decisions:12.1f} %")

(RESULTS / "Q5_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
