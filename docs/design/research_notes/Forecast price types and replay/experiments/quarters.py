"""How far quarter-hour prices stray from their hour's mean, and how much of that is systematic.

Usage: python quarters.py <data folder>
For every hour with four quarters in dap.json: deviation of each quarter from the hour mean.
'Systematic' is the mean deviation per (local hour, quarter position) over all days; the rest
is what a step mapping (one hourly value for all four quarters) cannot know.
"""
import json
import os
import statistics as st
import sys
from collections import defaultdict

recs = json.load(open(os.path.join(sys.argv[1], "dap.json")))["records"]
for area in ("DK1", "DK2"):
    q = defaultdict(dict)
    for r in recs:
        if r["PriceArea"] == area:
            t = r["TimeUTC"]
            q[t[:13]][int(t[14:16]) // 15] = (r["DayAheadPriceDKK"], int(r["TimeDK"][11:13]))
    dev, sysd = [], defaultdict(list)
    for v in q.values():
        if len(v) != 4:
            continue
        m = st.mean(p for p, _ in v.values())
        for i, (p, h) in v.items():
            dev.append((h, i, p - m))
            sysd[(h, i)].append(p - m)
    mean_sys = {k: st.mean(x) for k, x in sysd.items()}
    resid = [abs(d - mean_sys[(h, i)]) for h, i, d in dev]
    print(f"{area}: {len(dev)//4} hours; mean |quarter - hour mean| {st.mean(abs(d) for *_, d in dev):.0f} DKK/MWh; "
          f"after removing the mean pattern per (hour, quarter) {st.mean(resid):.0f}; "
          f"largest systematic pattern {max(abs(x) for x in mean_sys.values()):.0f} at {max(mean_sys, key=lambda k: abs(mean_sys[k]))}")
    for h in (6, 7, 8, 16, 17, 21, 22):
        print("   hour %02d quarters: %s" % (h, " ".join(f"{mean_sys[(h, i)]:+.0f}" for i in range(4))))
