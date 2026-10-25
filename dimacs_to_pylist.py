"""Read a DIMACS CNF file into a list of clauses."""

import argparse
from pathlib import Path


def read_dimacs(path):
    """Return (variable_count, clauses), where each clause is a list of integers.

    For example, (x1 OR NOT x2) AND x3 becomes [[1, -2], [3]].
    The formula [] is true; a formula containing an empty clause, [[]], is false.
    """
    variable_count = None
    declared_clause_count = None
    clauses = []
    current_clause = []

    with Path(path).open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            tokens = line.split()
            if not tokens or tokens[0] == "c":
                continue

            if variable_count is None:
                if len(tokens) != 4 or tokens[:2] != ["p", "cnf"]:
                    raise ValueError(f"Line {line_number}: expected 'p cnf N M'")
                try:
                    variable_count = int(tokens[2])
                    declared_clause_count = int(tokens[3])
                except ValueError as error:
                    raise ValueError(
                        f"Line {line_number}: N and M must be integers"
                    ) from error
                if variable_count < 0 or declared_clause_count < 0:
                    raise ValueError(f"Line {line_number}: N and M cannot be negative")
                continue

            for token in tokens:
                try:
                    literal = int(token)
                except ValueError as error:
                    raise ValueError(
                        f"Line {line_number}: invalid literal: {token}"
                    ) from error

                if literal == 0:
                    clauses.append(current_clause)
                    current_clause = []
                elif abs(literal) > variable_count:
                    raise ValueError(
                        f"Line {line_number}: variable {abs(literal)} "
                        f"is outside 1..{variable_count}"
                    )
                else:
                    current_clause.append(literal)

    if variable_count is None:
        raise ValueError("Missing 'p cnf N M' header")
    if current_clause:
        raise ValueError("The last clause does not end with 0")
    if len(clauses) != declared_clause_count:
        raise ValueError(
            f"The header declares {declared_clause_count} clauses; "
            f"{len(clauses)} were read"
        )

    return variable_count, clauses


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="DIMACS CNF file to read")
    args = parser.parse_args()

    variable_count, clauses = read_dimacs(args.path)
    print(f"{variable_count} variables; {len(clauses)} clauses")
    print(f"First clauses: {clauses[:3]}")


if __name__ == "__main__":
    main()
