"""Question 1: produce the numbers quoted in the report. Output: results/Q1_results.txt"""

import itertools
import os
import time
from math import comb
from pathlib import Path

from generate_grid import generate_grid
from meowdoku_to_dimacs import encode_grid, read_grid
from sat import dpll_model, run_deep

os.chdir(Path(__file__).resolve().parent)
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)
lines = []


def log(text=""):
    print(text)
    lines.append(text)


def satisfies(clauses, true_variables):
    """True if setting exactly true_variables to true satisfies every clause."""
    true_variables = set(true_variables)
    return all(
        any((l > 0) == (abs(l) in true_variables) for l in clause) for clause in clauses
    )


def cats_of(model, size):
    return sorted(((v - 1) // size + 1, (v - 1) % size + 1) for v, x in model.items() if x)


# 1. The board of Figure 1: clauses per rule, planted solution, number of solutions
n, m, regions, grid = read_grid("image_grid.txt")
clauses = encode_grid(n, m, regions, grid)
sizes = [sum(row.count(r) for row in grid) for r in regions]
by_rule = {
    "rows": n * comb(m, 2),
    "columns": m * comb(n, 2),
    "regions": sum(1 + comb(s, 2) for s in sizes),
    "diagonals": 2 * (n - 1) * (m - 1),
}
log("Board of Figure 1 (image_grid.txt)")
log(f"  region sizes {sizes}")
log(f"  clauses per rule {by_rule}, total {sum(by_rule.values())}, "
    f"emitted by the converter {len(clauses)}")
log(f"  first clauses {clauses[:3]}")
planted = [2, 10, 18, 21, 25, 35]
log(f"  cats {planted} satisfy all clauses: {satisfies(clauses, planted)}")
solutions = [
    ids for ids in ([(i) * m + p[i] for i in range(n)] for p in itertools.permutations(range(1, m + 1)))
    if satisfies(clauses, ids)
]
log(f"  placements with one cat per row and column tested: 720; "
    f"solutions: {len(solutions)} {solutions}")

# 2. Generator: planted solution, region sizes, clauses, time
log()
log("Generator, seed 1")
log("  n   time(ms)  clauses   region sizes (min-max)  planted solution satisfies the CNF")
for size in (4, 5, 8, 12, 20, 30, 50):
    start = time.perf_counter()
    gen_regions, gen_grid, cats = generate_grid(size, 1)
    elapsed = (time.perf_counter() - start) * 1000
    gen_clauses = encode_grid(size, size, gen_regions, gen_grid)
    region_sizes = sorted(sum(row.count(r) for row in gen_grid) for r in gen_regions)
    ok = satisfies(gen_clauses, [(r - 1) * size + c for r, c in cats])
    log(f"  {size:<3d} {elapsed:8.1f}  {len(gen_clauses):7d}   "
        f"{region_sizes[0]:3d}-{region_sizes[-1]:<3d}                 {ok}")

# 3. Example 5x5, seed 1, and the placement found by the solver
gen_regions, gen_grid, cats = generate_grid(5, 1)
log()
log("Example n=5, seed 1")
for row in gen_grid:
    log("  " + " ".join(row))
log("  planted solution " + ", ".join(
    f"{r}=({row},{col})" for r, (row, col) in zip(gen_regions, cats)))
example_clauses = encode_grid(5, 5, gen_regions, gen_grid)
example_solutions = [
    [(cats_row) * 5 + p[cats_row] for cats_row in range(5)]
    for p in itertools.permutations(range(1, 6))
    if satisfies(example_clauses, [(r) * 5 + p[r] for r in range(5)])
]
log(f"  number of solutions of this board: {len(example_solutions)}")
model = run_deep(25, dpll_model, example_clauses)
log(f"  placement returned by the solver (random choices, varies): {cats_of(model, 5)}")

(RESULTS / "Q1_results.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
