"""Branching heuristics for DPLL: H1, and H3, H5 and H7 in static and dynamic form.

A heuristic is built from the initial formula and returns a function that,
given the current formula, chooses the literal to try first: a positive literal
p means "p <- 1" and a negative literal -p means "p <- 0".
"""

from collections import Counter


def literal_scores(clauses, only_minimum_size=False, weighted=False):
    """Return {literal: score} for the literals of the formula.

    The score is the number of occurrences of the literal, counted only in
    the clauses of minimum size if only_minimum_size is set, and with weight
    2 ** -size for each clause if weighted is set.
    """
    size = min((len(clause) for clause in clauses), default=None) if only_minimum_size else None
    scores = Counter()
    for clause in clauses:
        counted = size is None or len(clause) == size
        weight = 2.0 ** -len(clause) if weighted else 1
        for literal in clause:
            scores[literal] += weight if counted else 0
    return scores


def ranking_key(scores):
    """Order literals by decreasing score, then smaller variable, then positive."""
    return lambda literal: (-scores[literal], abs(literal), literal < 0)


def first_variable(initial_clauses):
    """H1: the first variable of the formula, with value 1."""
    return lambda clauses: min(abs(l) for clause in clauses for l in clause)


def dynamic(only_minimum_size, weighted):
    """Heuristic that scores the literals of the current formula at each choice."""
    def build(initial_clauses):
        def choose(clauses):
            scores = literal_scores(clauses, only_minimum_size, weighted)
            return min(scores, key=ranking_key(scores))
        return choose
    return build


def static(only_minimum_size, weighted):
    """Heuristic that ranks the literals once, on the initial formula."""
    def build(initial_clauses):
        scores = literal_scores(initial_clauses, only_minimum_size, weighted)
        ranking = sorted(scores, key=ranking_key(scores))

        def choose(clauses):
            present = {abs(l) for clause in clauses for l in clause}
            return next(l for l in ranking if abs(l) in present)
        return choose
    return build


# Name -> function that builds the heuristic from the initial formula.
FACTORIES = {
    "H1": first_variable,
    "H3s": static(False, False),   # most frequent literal
    "H3d": dynamic(False, False),
    "H5s": static(True, False),    # most frequent literal in the smallest clauses
    "H5d": dynamic(True, False),
    "H7s": static(False, True),    # best weighted literal (Jeroslow-Wang)
    "H7d": dynamic(False, True),
}
