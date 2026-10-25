"""Solve a Meowdoku grid file and write the solution file."""

import argparse
import sys
import tempfile
from pathlib import Path

from dimacs_to_pylist import read_dimacs
from meowdoku_to_dimacs import encode_grid, read_grid, write_dimacs
from sat import dpll_model, run_deep


def cats_from_model(model, row_count, column_count):
    """Return the (row, column) cells whose variable is true in the model."""
    cats = []
    for variable, value in sorted(model.items()):
        if value:
            # Inverse of id(i, j) = (i - 1) * M + j, with i and j from 1.
            row = (variable - 1) // column_count + 1
            column = (variable - 1) % column_count + 1
            cats.append((row, column))
    return cats


def check_solution(regions, grid, cats):
    """Return a list of rule violations; it is empty for a legal placement.

    The check uses only the grid and the cat positions, not the CNF formula.
    """
    problems = []

    for region in regions:
        count = sum(1 for row, column in cats if grid[row - 1][column - 1] == region)
        if count != 1:
            problems.append(f"region {region} contains {count} cats")

    for first in range(len(cats)):
        for second in range(first + 1, len(cats)):
            (row, column), (other_row, other_column) = cats[first], cats[second]
            if row == other_row:
                problems.append(f"cats {cats[first]} and {cats[second]} share a row")
            if column == other_column:
                problems.append(f"cats {cats[first]} and {cats[second]} share a column")
            if abs(row - other_row) <= 1 and abs(column - other_column) <= 1:
                problems.append(f"cats {cats[first]} and {cats[second]} touch")
    return problems


def format_solution(row_count, column_count, regions, grid, cats):
    """Return the two descriptions of the solution, as in the assignment."""
    cat_of_region = {grid[row - 1][column - 1]: (row, column) for row, column in cats}
    region_lines = [
        f"{region} {cat_of_region[region][0]} {cat_of_region[region][1]}"
        for region in regions
    ]
    cat_cells = set(cats)
    grid_lines = [
        " ".join(
            "*" if (row, column) in cat_cells else "."
            for column in range(1, column_count + 1)
        )
        for row in range(1, row_count + 1)
    ]
    return "\n".join(region_lines) + "\n\n" + "\n".join(grid_lines) + "\n"


def solve_grid(grid_path, result_path):
    """Solve the grid, check the solution and write the result file."""
    row_count, column_count, regions, grid = read_grid(grid_path)
    clauses = encode_grid(row_count, column_count, regions, grid)

    # The search goes through a DIMACS file, as the solver reads that format.
    with tempfile.TemporaryDirectory() as directory:
        dimacs_path = Path(directory) / "grid.cnf"
        write_dimacs(dimacs_path, row_count * column_count, clauses)
        variable_count, formula = read_dimacs(dimacs_path)
    model = run_deep(variable_count, dpll_model, formula)
    if model is None:
        raise ValueError("The grid has no solution")

    cats = cats_from_model(model, row_count, column_count)
    problems = check_solution(regions, grid, cats)
    if problems:
        raise RuntimeError("Invalid solution: " + "; ".join(problems))

    original = Path(grid_path).read_text(encoding="utf-8").rstrip("\n")
    solution = format_solution(row_count, column_count, regions, grid, cats)
    Path(result_path).write_text(original + "\n\n" + solution, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("grid", help="Meowdoku grid file")
    parser.add_argument("output", help="solution file to write")
    args = parser.parse_args()

    try:
        solve_grid(args.grid, args.output)
    except (ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
    print(f"Solution written to {args.output}")


if __name__ == "__main__":
    main()
