"""Error of the elpriser.org runs against settled day-ahead prices, by lead day.

    python3 fcerr.py DATA_DIR

Lead day 1 is the first day after the last published day of the run. Error = actual - forecast
(hourly mean of the four quarters), DKK/MWh spot excl. VAT. Prints bias, MAE, the share of days
under-forecast, and how many distinct target days and runs the statistics rest on.
"""
import datetime as dt
import statistics as st
import sys

import data as D

folder = sys.argv[1]
for area in ("DK1", "DK2"):
    A = D.Area(folder, area)
    runs = D.load_runs(folder, area)
    by = {}
    days = set()
    for avail, last, fc, issued in runs:
        base = D.local_midnight(last + dt.timedelta(days=1))
        per_day = {}
        for m, f in fc.items():
            q = m // 15
            if q + 4 > A.nq:
                continue
            act = sum(A.spot[q:q + 4]) / 4
            per_day.setdefault((m - base) // 1440, []).append((act - f) * 1000)
        for lead, errs in per_day.items():
            if len(errs) < 20:
                continue
            by.setdefault(lead + 1, []).append((st.mean(errs), st.mean(abs(e) for e in errs), issued))
            days.add((issued, lead))
    print("\n%s: %d runs, issued %s to %s" % (area, len(runs), runs[0][3], runs[-1][3]))
    print("| Lead day | Days | Bias (mean actual - forecast) | Days under-forecast | Hourly MAE |")
    print("|---|---|---|---|---|")
    for lead in sorted(by):
        v = by[lead]
        print("| %d | %d | %+.0f | %d %% | %.0f |" % (lead, len(v), st.mean(x[0] for x in v),
                                                100 * sum(1 for x in v if x[0] > 0) / len(v),
                                                st.mean(x[1] for x in v)))
    targets = set()
    for avail, last, fc, issued in runs:
        for m in fc:
            if m // 15 + 4 <= A.nq:
                targets.add(D.local(m).date())
    print("Distinct target days with outcomes: %d (%s to %s)" % (len(targets), min(targets), max(targets)))
    late = [r[3] for r in runs if r[1] == dt.date.fromisoformat(r[3])]
    print("Runs whose next day was not yet published when the run was made: %s" % late)
