# MLSF 2026-27 – Projet partie I : solveur SAT (DPLL) et Meowdoku

Rapport : `rapport.pdf` (sources LaTeX dans `rapport/`). Python 3 (testé 3.14 ; syntaxe vérifiée pour 3.12), bibliothèque standard uniquement ;
`make_figures.py` demande `matplotlib`.

## Solveur (Question 6)

    python3 sat.py instance.cnf                              # mode dpll (par défaut)
    python3 sat.py instance.cnf --mode optimized --output-model

Sortie : `s SATISFIABLE` (puis `v ... 0` avec `--output-model`) ou `s UNSATISFIABLE`.

## Meowdoku (Questions 1 et 3)

    python3 meowdoku_to_dimacs.py image_grid.txt grille.cnf       # grille -> DIMACS
    python3 generate_grid.py 8 grille8.txt --seed 1               # grille avec solution plantée
    python3 solve_meowdoku.py image_grid.txt solution.txt         # grille -> fichier solution

## Fichiers

| Fichier | Rôle |
|---|---|
| `sat.py` | DPLL (algorithmes 1 et 2), DPLL_H (algorithme 3), interface en ligne de commande |
| `heuristics.py` | heuristiques H1, H3, H5, H7 (statiques et dynamiques) |
| `dimacs_to_pylist.py` | lecteur DIMACS |
| `meowdoku_to_dimacs.py`, `generate_grid.py`, `solve_meowdoku.py` | Meowdoku |
| `benchmark.py` | mesures des questions 5 et 6 |
| `Q1_script.py` … `Q6_script.py` | un script par question ; sorties dans `results/` |
| `make_figures.py` | figure du rapport à partir de `results/Q5_runs.json` |
| `image_grid.txt` | grille de la figure du rapport |
| `meowdoku-instances/` | 18 formules Meowdoku (9 SAT, 9 UNSAT) + `expected.json` |
| `public-instances/` | instances des enseignants |
| `results/` | sorties brutes des scripts |

Les scripts `Q*_script.py` relancent les mesures (plusieurs centaines d'exécutions de 60 s au plus) ; les résultats du rapport sont dans `results/`.
