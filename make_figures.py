"""Draw the cactus plot of Question 5 from results/Q5_runs.json.

Output: rapport/figures/cactus.pdf
"""

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

os.chdir(Path(__file__).resolve().parent)
runs = json.loads(Path("results/Q5_runs.json").read_text())
heuristics = ["H0", "H1", "H3s", "H3d", "H5s", "H5d", "H7s", "H7d"]
styles = {
    "H0": ("black", ":"), "H1": ("gray", "-"),
    "H3s": ("tab:blue", "--"), "H3d": ("tab:blue", "-"),
    "H5s": ("tab:red", "--"), "H5d": ("tab:red", "-"),
    "H7s": ("tab:green", "--"), "H7d": ("tab:green", "-"),
}
panels = [("public", "Instances publiques (30)"), ("meowdoku", "Instances Meowdoku (18)")]

fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
for axis, (folder, title) in zip(axes, panels):
    for name in heuristics:
        times = sorted(r["cpu"] for r in runs
                       if r["heuristic"] == name and r["folder"] == folder
                       and r["status"] != "TIMEOUT")
        color, line = styles[name]
        axis.plot(range(1, len(times) + 1), times, color=color, linestyle=line,
                  linewidth=1.5, label=name)
    axis.set_yscale("log")
    axis.xaxis.set_major_locator(MaxNLocator(integer=True))
    axis.set_xlabel("nombre d'instances résolues")
    axis.set_title(title, fontsize=10)
    axis.grid(True, which="both", alpha=0.3)
axes[0].set_ylabel("temps CPU (s), échelle log")
axes[1].legend(ncol=2, fontsize=8, loc="upper left")
fig.tight_layout()
fig.savefig("rapport/figures/cactus.pdf")
