"""Question 4: check the heuristics on the 11 small instances of the teachers.

Output: results/Q4_validation.txt. The measurements on the benchmark instances are
those of Question 5.
"""

import json
import os
from pathlib import Path

from benchmark import run_once
from sat import HEURISTIC_NAMES

os.chdir(Path(__file__).resolve().parent)
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

expected = json.loads(Path("public-instances/expected.json").read_text())
small = sorted(name for name in expected if not name.startswith("public"))

lines = [f"{len(small)} small instances x {len(HEURISTIC_NAMES)} heuristics",
         "instance" + "".join(f"{h:>6s}" for h in HEURISTIC_NAMES) + "   (ok = right status and valid model)"]
wrong = 0
for name in small:
    row = []
    for heuristic in HEURISTIC_NAMES:
        result = run_once(heuristic, f"public-instances/instances/{name}")
        ok = result["status"] == expected[name] and result["valid"]
        wrong += not ok
        row.append("ok" if ok else "WRONG")
    lines.append(f"{name:36s}" + "".join(f"{cell:>6s}" for cell in row))
lines.append(f"wrong answers: {wrong} of {len(small) * len(HEURISTIC_NAMES)} runs")

print("\n".join(lines))
(RESULTS / "Q4_validation.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
