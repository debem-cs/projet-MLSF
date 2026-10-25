"""Measure the DPLL_H heuristics on the teachers' instances and on Meowdoku formulas.

    python3 benchmark.py generate          write the Meowdoku instances
    python3 benchmark.py all results.json  run every heuristic on every instance
    python3 benchmark.py run H3d file.cnf  one run, printed as JSON
    python3 benchmark.py cli results.json  run sat.py in both modes on the 41 public files
"""

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dimacs_to_pylist import read_dimacs
from generate_grid import generate_grid
from meowdoku_to_dimacs import encode_grid, write_dimacs
from sat import HEURISTIC_NAMES, Stats, dpll_h, make_heuristic, run_deep

PUBLIC = Path("public-instances")
MEOWDOKU = Path("meowdoku-instances")
SAT_SIZES = (10, 15, 20)
UNSAT_SIZES = (8, 9, 10)
SEEDS = (1, 2, 3)


def generate_instances():
    """Write satisfiable boards and unsatisfiable boards as DIMACS files.

    A generated board has a planted solution. Giving three cells without a cat
    a new region of their own makes n + 1 regions on n rows, hence no solution.
    """
    MEOWDOKU.mkdir(exist_ok=True)
    expected = {}
    for size in SAT_SIZES:
        for seed in SEEDS:
            regions, grid, cats = generate_grid(size, seed)
            name = f"sat-n{size}-s{seed}.cnf"
            write_dimacs(MEOWDOKU / name, size * size,
                         encode_grid(size, size, regions, grid))
            expected[name] = "SAT"
    for size in UNSAT_SIZES:
        for seed in SEEDS:
            regions, grid, cats = generate_grid(size, seed)
            free_cells = [
                (r, c) for r in range(1, size + 1) for c in range(1, size + 1)
                if (r, c) not in cats
            ]
            for row, column in free_cells[:3]:
                grid[row - 1][column - 1] = "X"
            name = f"unsat-n{size}-s{seed}.cnf"
            write_dimacs(MEOWDOKU / name, size * size,
                         encode_grid(size, size, regions + ["X"], grid))
            expected[name] = "UNSAT"
    (MEOWDOKU / "expected.json").write_text(json.dumps(expected, indent=1))


def run_once(heuristic, path):
    """Solve one instance and return the counters."""
    variable_count, clauses = read_dimacs(path)
    stats = Stats()
    choose = make_heuristic(heuristic, clauses)
    start = time.process_time()
    model = run_deep(variable_count, dpll_h, clauses, choose, stats)
    cpu = time.process_time() - start
    valid = model is None or all(
        any(model.get(abs(l), False) == (l > 0) for l in clause)
        for clause in clauses
    )
    return {
        "status": "UNSAT" if model is None else "SAT",
        "valid": valid,
        "decisions": stats.decisions,
        "backtracks": stats.backtracks,
        "cpu": cpu,
        "heuristic_time": stats.heuristic_time,
    }


def run_in_process(heuristic, path, timeout):
    """Run one measurement in a separate process, with a time limit."""
    command = [sys.executable, __file__, "run", heuristic, str(path)]
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        return json.loads(done.stdout)
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT"}


def run_all(output, timeout, workers):
    expected = {}
    for name, status in json.loads((PUBLIC / "expected.json").read_text()).items():
        if name.startswith("public"):
            expected[PUBLIC / "instances" / name] = status
    for name, status in json.loads((MEOWDOKU / "expected.json").read_text()).items():
        expected[MEOWDOKU / name] = status
    jobs = [(h, path) for path in sorted(expected) for h in HEURISTIC_NAMES]
    with ThreadPoolExecutor(workers) as pool:
        outcomes = list(pool.map(lambda job: run_in_process(*job, timeout), jobs))
    results = []
    for (heuristic, path), outcome in zip(jobs, outcomes):
        outcome.update(heuristic=heuristic, instance=path.name,
                       expected=expected[path],
                       folder="meowdoku" if path.parent == MEOWDOKU else "public")
        results.append(outcome)
    Path(output).write_text(json.dumps(results, indent=1))


def run_cli_once(mode, path, expected, timeout):
    """Run sat.py as the competition does and check the answer."""
    command = [sys.executable, "sat.py", str(path), "--mode", mode, "--output-model"]
    start = time.time()
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"correct": False, "time": timeout, "answer": "TIMEOUT"}
    elapsed = time.time() - start
    lines = done.stdout.splitlines()
    answer = {"s SATISFIABLE": "SAT", "s UNSATISFIABLE": "UNSAT"}.get(
        lines[0] if lines else "", "ERROR")
    correct = answer == expected
    if correct and answer == "SAT":
        values = {int(word) for word in lines[1].split()[1:-1]}
        _, clauses = read_dimacs(path)
        correct = all(any(l in values for l in clause) for clause in clauses)
    return {"correct": correct, "time": elapsed, "answer": answer}


def run_cli(output, timeout, workers):
    expected = json.loads((PUBLIC / "expected.json").read_text())
    jobs = [(mode, PUBLIC / "instances" / name, status)
            for name, status in sorted(expected.items())
            for mode in ("dpll", "optimized")]
    with ThreadPoolExecutor(workers) as pool:
        outcomes = list(pool.map(lambda job: run_cli_once(*job, timeout), jobs))
    results = [dict(outcome, mode=mode, instance=path.name, expected=status)
               for (mode, path, status), outcome in zip(jobs, outcomes)]
    Path(output).write_text(json.dumps(results, indent=1))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("command", choices=["generate", "all", "run", "cli"])
    parser.add_argument("arguments", nargs="*")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    if args.command == "generate":
        generate_instances()
    elif args.command == "all":
        run_all(args.arguments[0], args.timeout, args.workers)
    elif args.command == "cli":
        run_cli(args.arguments[0], args.timeout, args.workers)
    else:
        print(json.dumps(run_once(*args.arguments)))


if __name__ == "__main__":
    main()
