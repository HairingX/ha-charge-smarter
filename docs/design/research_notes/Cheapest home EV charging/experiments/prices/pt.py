import json, sys, glob, os, statistics as st, datetime as dt, math
from collections import defaultdict
D = sys.argv[1]
recs = json.load(open(os.path.join(D, "dap.json")))["records"]
qd = defaultdict(list)
for r in recs: qd[(r["PriceArea"], r["TimeDK"][:10])].append(r["DayAheadPriceDKK"])
am = {k: st.mean(v) for k, v in qd.items()}
def pt(f, a):  # Pesaran-Timmermann 1992, signs as booleans "up"
    n = len(f); P = sum(x == y for x, y in zip(f, a)) / n
    py = sum(a) / n; px = sum(f) / n
    ps = py * px + (1 - py) * (1 - px)
    vp = ps * (1 - ps) / n
    vps = ((2*py-1)**2 * px*(1-px) + (2*px-1)**2 * py*(1-py)) / n + 4*py*px*(1-py)*(1-px)/n**2
    return P, (P - ps) / math.sqrt(vp - vps) if vp - vps > 0 else float('nan')
for area in ("DK1", "DK2"):
    runs = {}
    for f in sorted(glob.glob(os.path.join(D, f"arch_{area}_*.json"))):
        d = json.load(open(f)); I = dt.date.fromisoformat(d["issued"])
        runs[I] = {dt.date.fromisoformat(x["date"]): st.mean(p["spot_dkk_mwh"] for p in x["prices"]) for x in d["days"] if x["type"] == "forecast"}
    out = []
    for k in range(2, 8):
        F, A = [], []
        for I, fc in runs.items():
            t = I + dt.timedelta(k); ref = am.get((area, (I + dt.timedelta(1)).isoformat())); a = am.get((area, t.isoformat()))
            if t in fc and ref is not None and a is not None and a != ref and fc[t] != ref:
                F.append(fc[t] > ref); A.append(a > ref)
        P, S = pt(F, A); out.append("D+%d n=%d hit %.0f%% PT %.2f" % (k, len(F), 100*P, S))
    F, A = [], []
    for I, fc in runs.items():
        days = [I + dt.timedelta(k) for k in range(2, 8)]; ref = am.get((area, (I + dt.timedelta(1)).isoformat()))
        if ref is None or any(t not in fc or (area, t.isoformat()) not in am for t in days): continue
        F.append(st.mean(fc[t] for t in days) > ref); A.append(st.mean(am[(area, t.isoformat())] for t in days) > ref)
    P, S = pt(F, A); out.append("mean D+2..D+7 n=%d hit %.0f%% PT %.2f" % (len(F), 100*P, S))
    print(area, " | ".join(out))
