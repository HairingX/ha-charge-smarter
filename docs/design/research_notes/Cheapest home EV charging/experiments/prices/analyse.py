import json, sys, glob, os, statistics as st
from collections import defaultdict
D = sys.argv[1]
recs = json.load(open(os.path.join(D, "dap.json")))["records"]
# hourly mean (local DK hour) of 15-min prices, DKK/MWh
hourly = defaultdict(list)
for r in recs:
    key = (r["PriceArea"], r["TimeDK"][:13])
    hourly[key].append(r["DayAheadPriceDKK"])
act = {k: sum(v)/len(v) for k, v in hourly.items()}

# ---- price distribution, last 12 months
for area in ("DK1", "DK2"):
    q = [r["DayAheadPriceDKK"] for r in recs if r["PriceArea"] == area]
    h = [v for (a, _), v in act.items() if a == area]
    n = len(h)
    print(area, "quarter-hours", len(q), "hours", n,
          "mean %.0f median %.0f sd %.0f" % (st.mean(h), st.median(h), st.pstdev(h)),
          "| hours <=0: %.1f%%" % (100*sum(x <= 0 for x in h)/n),
          "| |p|<75 DKK/MWh (~10 EUR): %.1f%%" % (100*sum(abs(x) < 75 for x in h)/n),
          "| min %.0f max %.0f" % (min(h), max(h)))
    # by month: share <=0
    bym = defaultdict(list)
    for (a, t), v in act.items():
        if a == area: bym[t[:7]].append(v)
    print("  month: share<=0 / mean:", " ".join("%s:%.0f%%/%.0f" % (m[2:], 100*sum(x<=0 for x in v)/len(v), st.mean(v)) for m, v in sorted(bym.items())))

# ---- forecast archive errors by days-ahead
import datetime as dt
for area in ("DK1", "DK2"):
    errs = defaultdict(list); cov = defaultdict(list); bias = defaultdict(list); lvl = defaultdict(list)
    pairs = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(D, f"arch_{area}_*.json"))):
        d = json.load(open(f)); issued = dt.date.fromisoformat(d["issued"])
        for day in d["days"]:
            if day["type"] != "forecast": continue
            k = (dt.date.fromisoformat(day["date"]) - issued).days
            for p in day["prices"]:
                key = (area, "%sT%02d" % (day["date"], p["hour"]))
                if key not in act: continue
                y = act[key]; f50 = p["spot_dkk_mwh"]
                errs[k].append(abs(y - f50)); bias[k].append(f50 - y); lvl[k].append(y)
                cov[k].append(p["spot_min_dkk_mwh"] <= y <= p["spot_max_dkk_mwh"])
                pairs[k].append((f50, y))
    print(area, "forecast archive (elpriser.org v3), MAE by days ahead of issue date")
    for k in sorted(errs):
        e = errs[k]; mean_y = st.mean(lvl[k])
        print("  D+%d n=%4d MAE %.0f  bias %+.0f  mean actual %.0f  MAE/mean %.0f%%  P10-P90 cover %.0f%%" % (
            k, len(e), st.mean(e), st.mean(bias[k]), mean_y, 100*st.mean(e)/mean_y, 100*st.mean(cov[k])))
    # does abs error scale with forecast level? bin by forecast level
    allp = [pp for k in pairs for pp in pairs[k]]
    allp.sort()
    nb = 4; size = len(allp)//nb
    print("  |err| by forecast-level quartile:", " ".join(
        "[%.0f..%.0f] MAE %.0f rel %.0f%%" % (b[0][0], b[-1][0], st.mean(abs(f-y) for f,y in b), 100*st.mean(abs(f-y) for f,y in b)/max(1,abs(st.mean(f for f,_ in b))))
        for b in (allp[i*size:(i+1)*size] for i in range(nb))))
