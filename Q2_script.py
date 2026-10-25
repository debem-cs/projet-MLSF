"""Question 2: checks of the reader and validation of the two DPLL versions.

Output: results/Q2_runs.json (every run) and results/Q2_summary.txt.
Each public instance is solved three times by dpll_status and by dpll_model,
through sat.py, with a limit of 60 seconds per run.
"""

import argparse
import json
import os
import statistics
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from benchmark import run_cli_once
from dimacs_to_pylist import read_dimacs
from meowdoku_to_dimacs import encode_grid, read_grid, write_dimacs
from sat import dpll_model, run_deep

os.chdir(Path(__file__).resolve().parent)
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)
PUBLIC = Path("public-instances")
lines = []


def log(text=""):
    print(text)
    lines.append(text)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--timeout", type=int, default=60)
parser.add_argument("--workers", type=int, default=8)
parser.add_argument("--runs", type=int, default=3)
args = parser.parse_args()

expected = json.loads((PUBLIC / "expected.json").read_text())
names = sorted(expected)

# 1. The reader on the 41 files and on the two empty cases
log("Reader")
for name in names:
    read_dimacs(PUBLIC / "instances" / name)
log(f"  {len(names)} public files read without error")
for name in ("edge_no_clause_sat.cnf", "edge_empty_clause_unsat.cnf"):
    log(f"  {name} -> {read_dimacs(PUBLIC / 'instances' / name)}")

# 2. The board of Figure 1: DIMACS file, reader, model
n, m, regions, grid = read_grid("image_grid.txt")
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "board.cnf"
    write_dimacs(path, n * m, encode_grid(n, m, regions, grid))
    head = path.read_text().splitlines()[:3]
    variable_count, clauses = read_dimacs(path)
log(f"  board of Figure 1: first lines {head}, V = {variable_count}, "
    f"{len(clauses)} clauses, first clauses {clauses[:2]}")
model = run_deep(variable_count, dpll_model, clauses)
log(f"  dpll_model true variables: {sorted(v for v, x in model.items() if x)}")

# 3. Validation: instances x versions x runs
jobs = [(name, version, run) for name in names for version in ("status", "model")
        for run in range(args.runs)]


def execute(job):
    name, version, run = job
    outcome = run_cli_once("dpll", PUBLIC / "instances" / name, expected[name],
                           args.timeout, output_model=(version == "model"))
    return dict(outcome, instance=name, version=version, run=run, expected=expected[name])


with ThreadPoolExecutor(args.workers) as pool:
    runs = list(pool.map(execute, jobs))
(RESULTS / "Q2_runs.json").write_text(json.dumps(runs, indent=1))


def cell(instance, version):
    rs = [r for r in runs if r["instance"] == instance and r["version"] == version]
    good = [r["time"] for r in rs if r["correct"]]
    if not good:
        return len(good), None
    return len(good), statistics.median(good)


wrong = [r for r in runs if not r["correct"] and r["answer"] != "TIMEOUT"]
log()
log(f"Validation: {len(runs)} runs, limit {args.timeout} s")
log(f"  wrong answers (wrong status, invalid model or error): {len(wrong)}")
solved_all = [n_ for n_ in names
              if cell(n_, "status")[0] == args.runs and cell(n_, "model")[0] == args.runs]
log(f"  solved in all runs by both versions: {len(solved_all)} of {len(names)}")
log("  not solved in every run: " + ", ".join(n_ for n_ in names if n_ not in solved_all))


def show(k, median):
    return f"{k}/{args.runs}, " + (f"{median:.1f} s" if median is not None else "timeout")


log()
log("Benchmark instances with a median above 1 s in a version, or not always solved")
log(f"  {'instance':16s}{'status':>7s}  {'dpll_model':22s}{'dpll_status'}")
rest = []
for name in names:
    if not name.startswith("public"):
        continue
    model_cell, status_cell = cell(name, "model"), cell(name, "status")
    medians = [c[1] for c in (model_cell, status_cell) if c[1] is not None]
    slow = any(med > 1 for med in medians)
    if name not in solved_all or slow:
        log(f"  {name:16s}{expected[name]:>7s}  {show(*model_cell):22s}{show(*status_cell)}")
    else:
        rest.append(max(medians))
log(f"  other benchmark instances: {len(rest)}, largest median {max(rest):.2f} s")

text = "\n".join(lines) + "\n"
(RESULTS / "Q2_summary.txt").write_text(text, encoding="utf-8")
