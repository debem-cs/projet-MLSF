"""Solve DIMACS CNF formulas with the basic DPLL algorithm."""

import argparse
import random
import sys
import threading
import time

from dimacs_to_pylist import read_dimacs
from heuristics import FACTORIES


def simplify(clauses, true_literal):
    """Return the formula left after making true_literal true."""
    remaining = []
    for clause in clauses:
        if true_literal in clause:
            continue  # The whole clause is satisfied.
        remaining.append([
            literal for literal in clause if literal != -true_literal
        ])
    return remaining


def unit_literal(clauses):
    """Return a literal forced by a one-literal clause, if one exists."""
    for clause in clauses:
        if len(clause) == 1:
            return clause[0]
    return None


def pure_literal(clauses):
    """Return a literal whose opposite does not occur in the formula."""
    literals = {literal for clause in clauses for literal in clause}
    for literal in sorted(literals, key=lambda value: (abs(value), value < 0)):
        if -literal not in literals:
            return literal
    return None


def choose_literal(clauses):
    """Choose a variable and its first trial value at random."""
    variables = sorted({
        abs(literal) for clause in clauses for literal in clause
    })
    variable = random.choice(variables)
    return random.choice((variable, -variable))


def dpll_status(clauses):
    """Return True for SAT and False for UNSAT."""
    if any(len(clause) == 0 for clause in clauses):
        return False
    if not clauses:
        return True

    forced = unit_literal(clauses)
    if forced is None:
        forced = pure_literal(clauses)
    if forced is not None:
        return dpll_status(simplify(clauses, forced))

    trial = choose_literal(clauses)
    return (
        dpll_status(simplify(clauses, trial))
        or dpll_status(simplify(clauses, -trial))
    )


def dpll_model(clauses):
    """Return a satisfying {variable: Boolean} model, or None for UNSAT."""
    if any(len(clause) == 0 for clause in clauses):
        return None
    if not clauses:
        return {}

    forced = unit_literal(clauses)
    if forced is None:
        forced = pure_literal(clauses)
    if forced is not None:
        model = dpll_model(simplify(clauses, forced))
        if model is None:
            return None
        model[abs(forced)] = forced > 0
        return model

    first_trial = choose_literal(clauses)
    for trial in (first_trial, -first_trial):
        model = dpll_model(simplify(clauses, trial))
        if model is not None:
            model[abs(trial)] = trial > 0
            return model
    return None


class Stats:
    """Counters filled by dpll_h during one run."""

    def __init__(self):
        self.decisions = 0         # executions of the choice of a branch
        self.backtracks = 0        # executions of the second branch
        self.heuristic_time = 0.0  # seconds spent choosing the branches


HEURISTIC_NAMES = ["H0"] + list(FACTORIES)


def make_heuristic(name, clauses):
    """Return the function choosing a literal for heuristic name (H0 to H7)."""
    if name == "H0":
        return choose_literal
    return FACTORIES[name](clauses)


def dpll_h(clauses, choose, stats):
    """DPLL_H: return a satisfying {variable: Boolean} model, or None for UNSAT.

    choose(clauses) is the heuristic; stats receives the counters.
    """
    if any(len(clause) == 0 for clause in clauses):
        return None
    if not clauses:
        return {}

    forced = unit_literal(clauses)
    if forced is None:
        forced = pure_literal(clauses)
    if forced is not None:
        model = dpll_h(simplify(clauses, forced), choose, stats)
        if model is None:
            return None
        model[abs(forced)] = forced > 0
        return model

    start = time.perf_counter()
    first_trial = choose(clauses)
    stats.heuristic_time += time.perf_counter() - start
    stats.decisions += 1
    for attempt, trial in enumerate((first_trial, -first_trial)):
        if attempt == 1:
            stats.backtracks += 1
        model = dpll_h(simplify(clauses, trial), choose, stats)
        if model is not None:
            model[abs(trial)] = trial > 0
            return model
    return None


# Heuristic of the optimized mode, chosen from the measurements of Question 5.
OPTIMIZED_HEURISTIC = "H5d"


def solve_optimized(clauses):
    """Return a model, or None for UNSAT, with the heuristic of the optimized mode."""
    choose = make_heuristic(OPTIMIZED_HEURISTIC, clauses)
    return dpll_h(clauses, choose, Stats())


def run_deep(variable_count, function, *arguments):
    """Call function(*arguments) with room for a recursion as deep as DPLL's.

    Each recursive call assigns at least one variable, so the depth can reach
    the number of variables: raise Python's limit and give the search a thread
    with a large stack.
    """
    sys.setrecursionlimit(max(sys.getrecursionlimit(), variable_count + 1000))
    threading.stack_size(256 * 1024 * 1024)
    outcome = []

    def run():
        try:
            outcome.append((True, function(*arguments)))
        except BaseException as error:
            outcome.append((False, error))

    worker = threading.Thread(target=run)
    worker.start()
    worker.join()
    succeeded, value = outcome[0]
    if not succeeded:
        raise value
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="DIMACS CNF instance")
    parser.add_argument("--mode", choices=["dpll", "optimized"], default="dpll")
    parser.add_argument("--output-model", action="store_true")
    args = parser.parse_args()

    variable_count, clauses = read_dimacs(args.path)
    if args.mode == "dpll" and not args.output_model:
        satisfiable = run_deep(variable_count, dpll_status, clauses)
        model = None
    else:
        solver = dpll_model if args.mode == "dpll" else solve_optimized
        model = run_deep(variable_count, solver, clauses)
        satisfiable = model is not None

    print("s SATISFIABLE" if satisfiable else "s UNSATISFIABLE")
    if satisfiable and args.output_model:
        # Variables absent from the partial model can take either value.
        signed_values = [
            variable if model.get(variable, False) else -variable
            for variable in range(1, variable_count + 1)
        ]
        print("v " + " ".join(map(str, signed_values)) + " 0")


if __name__ == "__main__":
    main()
