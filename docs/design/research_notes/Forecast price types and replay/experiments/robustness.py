"""Split-sample check of the replanning simulation and of the c_decay weights.

Usage: python robustness.py <data folder>
Runs methods.simulate on the first and the second half of the decision days separately, for a
short list of methods, in both areas.
"""
import sys

import methods
from common import load_actual, load_runs

methods.METHODS = ["raw", "a+0.1", "a+0.3", "b_mean", "c_shift", "c_scale", "c_decay", "c_decay+1/0.5",
                   "c_decay+0.5/0.25", "c_decay+1/1/1/1/1/1", "d_horizon"]
folder = sys.argv[1]
act = load_actual(folder)
for area in ("DK1", "DK2"):
    runs = load_runs(folder, area)
    dec = sorted(D for D in runs if D - methods.ONE in runs)
    half = len(dec) // 2
    for label, part in (("first half", dec[:half]), ("second half", dec[half:])):
        print(f"===== {area} {label}: {part[0]}..{part[-1]}")
        methods.simulate(act[area], runs, area, part)
