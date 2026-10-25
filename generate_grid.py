"""Generate square Meowdoku grids with a known solution."""

import argparse
from collections import deque
from pathlib import Path
from random import Random


def cat_columns(size, rng):
    """Choose one cat column per row, retrying earlier choices if needed."""
    if size < 1:
        raise ValueError("Grid size must be positive")
    if size == 1:
        return [1]
    if size < 4:
        raise ValueError("No square grid with N=M=K=2 or 3 can have a solution")

    columns = []
    used = set()

    def place_next_cat():
        if len(columns) == size:
            return True

        candidates = [
            column for column in range(1, size + 1)
            if column not in used
            and (not columns or abs(column - columns[-1]) > 1)
        ]
        rng.shuffle(candidates)

        for column in candidates:
            columns.append(column)
            used.add(column)
            if place_next_cat():
                return True
            used.remove(column)
            columns.pop()
        return False

    if not place_next_cat():
        raise RuntimeError("Could not construct a solution")
    return columns


def generate_grid(size, seed=None):
    """Return region names, the grid, and the planted cat coordinates."""
    rng = Random(seed)
    columns = cat_columns(size, rng)
    regions = [f"R{index}" for index in range(1, size + 1)]
    grid = [[None for _ in range(size)] for _ in range(size)]
    cats = []
    frontier = []

    # Give each cat its own initial region before expanding any region.
    for row, column in enumerate(columns, start=1):
        grid[row - 1][column - 1] = regions[row - 1]
        cats.append((row, column))
        frontier.append((row - 1, column - 1))

    rng.shuffle(frontier)
    frontier = deque(frontier)

    # Expansion through shared edges keeps every region connected. Assigned
    # cells never change region, including cells that contain another cat.
    while frontier:
        row, column = frontier.popleft()
        neighbors = [
            (row - 1, column), (row + 1, column),
            (row, column - 1), (row, column + 1),
        ]
        rng.shuffle(neighbors)
        for next_row, next_column in neighbors:
            if not (0 <= next_row < size and 0 <= next_column < size):
                continue
            if grid[next_row][next_column] is None:
                grid[next_row][next_column] = grid[row][column]
                frontier.append((next_row, next_column))

    return regions, grid, cats


def write_grid(path, regions, grid, seed=None):
    """Write a grid in the format accepted by meowdoku_to_dimacs.py."""
    size = len(grid)
    lines = ["c Generated grid with a planted solution"]
    if seed is not None:
        lines.append(f"c Random seed: {seed}")
    lines.extend([f"GRID {size} {size}", "ZONES " + " ".join(regions), ""])
    lines.extend(" ".join(row) for row in grid)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("size", type=int, help="N for an N x N grid with N regions")
    parser.add_argument("output", help="Grid file to write")
    parser.add_argument("--seed", type=int, help="Repeat the same random choices")
    args = parser.parse_args()

    regions, grid, cats = generate_grid(args.size, args.seed)
    write_grid(args.output, regions, grid, args.seed)
    print(f"Grid written to {args.output}")
    print("Planted solution: " + ", ".join(
        f"{region}=({row},{column})"
        for region, (row, column) in zip(regions, cats)
    ))


if __name__ == "__main__":
    main()
