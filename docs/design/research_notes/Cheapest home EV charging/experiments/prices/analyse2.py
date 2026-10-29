import json, sys, glob, os, statistics as st, datetime as dt
from collections import defaultdict
D = sys.argv[1]
recs = json.load(open(os.path.join(D, "dap.json")))["records"]
hourly = defaultdict(list)
for r in recs: hourly[(r["PriceArea"], r["TimeDK"][:13])].append(r["DayAheadPriceDKK"])
act = {k: sum(v)/len(v) for k, v in hourly.items()}
N = 4
for area in ("DK1", "DK2"):
    lvl = defaultdict(list); shape = defaultdict(list); sel = defaultdict(list); selq = defaultdict(list); selp90 = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(D, f"arch_{area}_*.json"))):
        d = json.load(open(f)); issued = dt.date.fromisoformat(d["issued"])
        for day in d["days"]:
            if day["type"] != "forecast": continue
            k = (dt.date.fromisoformat(day["date"]) - issued).days
            rows = []
            for p in day["prices"]:
                key = (area, "%sT%02d" % (day["date"], p["hour"]))
                if key in act: rows.append((p["spot_dkk_mwh"], act[key], p["spot_max_dkk_mwh"]))
            if len(rows) < 23: continue
            fm = st.mean(r[0] for r in rows); ym = st.mean(r[1] for r in rows)
            lvl[k].append(abs(fm - ym))
            shape[k].append(st.mean(abs((f - fm) - (y - ym)) for f, y, _ in rows))
            cheap = sorted(rows)[:N]
            sel[k].append(st.mean(y for _, y, _ in cheap) - st.mean(f for f, _, _ in cheap))
            # true cheapest N actual vs chosen
            selq[k].append(st.mean(y for _, y, _ in cheap) - st.mean(sorted(y for _, y, _ in rows)[:N]))
            selp90[k].append(st.mean(y for _, y, _ in cheap) - st.mean(p9 for _, _, p9 in cheap))
    print(area, "per forecast-day: |daily-mean error|, within-day shape MAE, cheapest-%d-hours: actual-minus-forecast (optimizer's curse), regret vs true cheapest %d, actual-minus-P90" % (N, N))
    for k in sorted(lvl):
        print("  D+%d days=%2d  level %.0f  shape %.0f  sel.bias %+.0f  regret %.0f  vsP90 %+.0f" % (k, len(lvl[k]), st.mean(lvl[k]), st.mean(shape[k]), st.mean(sel[k]), st.mean(selq[k]), st.mean(selp90[k])))
