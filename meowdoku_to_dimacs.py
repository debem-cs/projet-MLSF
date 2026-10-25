"""Convert a Meowdoku grid into a DIMACS CNF formula."""

import argparse
from pathlib import Path


def read_grid(path):
    """Read the GRID and ZONES headers followed by N rows of region labels."""
    lines = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("c"):
            lines.append(line)

    if len(lines) < 2:
        raise ValueError("Missing GRID and ZONES lines")

    header = lines[0].split()
    if len(header) != 3 or header[0] != "GRID":
        raise ValueError("The first non-comment line must be: GRID N M")
    row_count, column_count = int(header[1]), int(header[2])
    if row_count <= 0 or column_count <= 0:
        raise ValueError("N and M must be positive")

    declaration = lines[1].split()
    if len(declaration) < 2 or declaration[0] != "ZONES":
        raise ValueError("The second non-comment line must be: ZONES A B ...")
    regions = declaration[1:]
    if len(regions) != len(set(regions)):
        raise ValueError("Region names must be distinct")

    if len(lines[2:]) != row_count:
        raise ValueError(f"The grid must contain {row_count} region rows")
    grid = [line.split() for line in lines[2:]]
    if any(len(row) != column_count for row in grid):
        raise ValueError(f"Each grid row must contain {column_count} regions")

    used_regions = {region for row in grid for region in row}
    if used_regions != set(regions):
        raise ValueError("Grid regions must match the ZONES declaration")

    return row_count, column_count, regions, grid


def encode_grid(row_count, column_count, regions, grid):
    """Return the CNF as a list of integer clauses."""
    def cell_id(row, column):
        # Grid coordinates start at 1, as in the assignment.
        return (row - 1) * column_count + column

    clauses = []

    # Rule 1: at most one cat in each row.
    for row in range(1, row_count + 1):
        for first_column in range(1, column_count + 1):
            for second_column in range(first_column + 1, column_count + 1):
                clauses.append([
                    -cell_id(row, first_column),
                    -cell_id(row, second_column),
                ])

    # Rule 2: at most one cat in each column.
    for column in range(1, column_count + 1):
        for first_row in range(1, row_count + 1):
            for second_row in range(first_row + 1, row_count + 1):
                clauses.append([
                    -cell_id(first_row, column),
                    -cell_id(second_row, column),
                ])

    # Rule 3: exactly one cat in each region.
    cells_by_region = {region: [] for region in regions}
    for row in range(1, row_count + 1):
        for column in range(1, column_count + 1):
            region = grid[row - 1][column - 1]
            cells_by_region[region].append(cell_id(row, column))

    for region in regions:
        cells = cells_by_region[region]
        clauses.append(cells[:])  # At least one cat.
        for first in range(len(cells)):
            for second in range(first + 1, len(cells)):
                clauses.append([-cells[first], -cells[second]])

    # Rule 4: diagonal neighbors; row and column rules cover the other neighbors.
    for row in range(1, row_count):
        for column in range(1, column_count):
            clauses.append([
                -cell_id(row, column),
                -cell_id(row + 1, column + 1),
            ])
            clauses.append([
                -cell_id(row, column + 1),
                -cell_id(row + 1, column),
            ])

    return clauses


def write_dimacs(path, variable_count, clauses):
    lines = [f"p cnf {variable_count} {len(clauses)}"]
    lines.extend(" ".join(map(str, clause)) + " 0" for clause in clauses)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("grid", help="Meowdoku grid file")
    parser.add_argument("output", help="DIMACS CNF file to write")
    args = parser.parse_args()

    row_count, column_count, regions, grid = read_grid(args.grid)
    clauses = encode_grid(row_count, column_count, regions, grid)
    write_dimacs(args.output, row_count * column_count, clauses)
    print(f"{row_count * column_count} variables and {len(clauses)} "
          f"clauses written to {args.output}")


if __name__ == "__main__":
    main()
