"""Question 3: tests of solve_meowdoku.py. Output: results/Q3_results.txt and solution files."""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from generate_grid import write_grid, generate_grid
from meowdoku_to_dimacs import read_grid
from solve_meowdoku import check_solution, solve_grid

os.chdir(Path(__file__).resolve().parent)
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)
TIMEOUT = 60
lines = []


def log(text=""):
    print(text)
    lines.append(text)


# Grid of the assignment (Figure 1b) and the solution of its Figure 2
ASSIGNMENT_GRID = """c Grille 1
GRID 6 6
ZONES A B C D E F

A B C B B D
A B B B B D
A A B D D D
A A A E D D
A A A A D D
F A D D D D
"""
ASSIGNMENT_SOLUTION = ["A 3 2", "B 2 5", "C 1 3", "D 5 6", "E 4 4", "F 6 1"]

log("Grid of the assignment (Figure 1b)")
with tempfile.TemporaryDirectory() as directory:
    grid_path = Path(directory) / "assignment_grid.txt"
    grid_path.write_text(ASSIGNMENT_GRID, encoding="utf-8")
    output = RESULTS / "Q3_solution_assignment_grid.txt"
    solve_grid(grid_path, output)
text = output.read_text(encoding="utf-8")
found = [line for line in text.splitlines() if line[:1] in "ABCDEF" and len(line.split()) == 3]
log(f"  solution identical to Figure 2 of the assignment: {found == ASSIGNMENT_SOLUTION}")

log()
log("Board of Figure 1 (image_grid.txt)")
output = RESULTS / "Q3_solution_figure1_board.txt"
solve_grid("image_grid.txt", output)
log("  result file written to " + str(output))

# Generated boards: sequential runs, so that the times are not disturbed
log()
log("Generated boards, one run each, limit 60 s (time in seconds, rc = exit status)")
log("  n   seed 1          seed 2          seed 3")
with tempfile.TemporaryDirectory() as directory:
    for size in (4, 6, 8, 10, 12, 15, 20):
        cells = []
        for seed in (1, 2, 3):
            grid_path = Path(directory) / f"grid_{size}_{seed}.txt"
            regions, grid, _ = generate_grid(size, seed)
            write_grid(grid_path, regions, grid, seed)
            start = time.time()
            try:
                done = subprocess.run(
                    [sys.executable, "solve_meowdoku.py", str(grid_path),
                     str(Path(directory) / "out.txt")],
                    capture_output=True, text=True, timeout=TIMEOUT)
                cells.append(f"{time.time() - start:6.2f} rc={done.returncode}")
            except subprocess.TimeoutExpired:
                cells.append(f"timeout>{TIMEOUT}")
        log(f"  {size:<3d} " + "   ".join(f"{c:14s}" for c in cells))

# The check on wrong placements
log()
log("check_solution on the board of Figure 1")
_, _, regions, grid = read_grid("image_grid.txt")
legal = [(1, 2), (2, 4), (3, 6), (4, 3), (5, 1), (6, 5)]
cases = {
    "legal placement": legal,
    "two cats in a row": [(1, 2), (1, 4)] + legal[2:],
    "two cats touching diagonally": [(1, 2), (2, 3)] + legal[2:],
    "cat moved into an occupied column": legal[:5] + [(6, 2)],
}
for name, cats in cases.items():
    problems = check_solution(regions, grid, cats)
    log(f"  {name}: {problems if problems else 'no violation'}")

# Grid without solution: two regions on a 2x2 board
log()
log("Grid without solution (2x2, regions A A / B B)")
with tempfile.TemporaryDirectory() as directory:
    grid_path = Path(directory) / "unsat.txt"
    grid_path.write_text("GRID 2 2\nZONES A B\n\nA A\nB B\n", encoding="utf-8")
    output = Path(directory) / "out.txt"
    done = subprocess.run([sys.executable, "solve_meowdoku.py", str(grid_path), str(output)],
                          capture_output=True, text=True)
    log(f"  exit status {done.returncode}, message '{done.stderr.strip()}', "
        f"file written: {output.exists()}")

(RESULTS / "Q3_results.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
