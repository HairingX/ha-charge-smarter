import json, sys, glob, os, statistics as st, datetime as dt
from collections import defaultdict
D = sys.argv[1]
recs = json.load(open(os.path.join(D, "dap.json")))["records"]
qd = defaultdict(list); qh = defaultdict(list)
for r in recs:
    qd[(r["PriceArea"], r["TimeDK"][:10])].append(r["DayAheadPriceDKK"])
    qh[(r["PriceArea"], r["TimeDK"][:13])].append(r["DayAheadPriceDKK"])
amean = {k: st.mean(v) for k, v in qd.items()}            # actual daily mean
ahour = {k: st.mean(v) for k, v in qh.items()}
def day(d): return d.isoformat()
def sgn(x): return (x > 0) - (x < 0)
def spearman(a, b):
    def rk(x):
        o = sorted(range(len(x)), key=lambda i: x[i]); r = [0]*len(x)
        for p, i in enumerate(o): r[i] = p
        return r
    ra, rb = rk(a), rk(b); n = len(a)
    return 1 - 6*sum((x-y)**2 for x, y in zip(ra, rb))/(n*(n*n-1))
for area in ("DK1", "DK2"):
    runs = {}
    for f in sorted(glob.glob(os.path.join(D, f"arch_{area}_*.json"))):
        d = json.load(open(f)); I = dt.date.fromisoformat(d["issued"])
        fc = {}
        for dd in d["days"]:
            if dd["type"] == "forecast" and len(dd["prices"]) >= 23:
                fc[dt.date.fromisoformat(dd["date"])] = st.mean(p["spot_dkk_mwh"] for p in dd["prices"])
        runs[I] = fc
    print("=" * 20, area, "runs", len(runs), "first forecast offsets:", sorted({min((k - I).days for k in fc) for I, fc in runs.items() if fc}))
    for ref_off, refname in ((0, "ref=today D"), (1, "ref=D+1 (last known day)")):
        print(" --", refname)
        hits = defaultdict(list); hp = defaultdict(list); hw = defaultdict(list); hm = defaultdict(list); up = defaultdict(list)
        mag = defaultdict(list)
        for I, fc in runs.items():
            ref = amean.get((area, day(I + dt.timedelta(ref_off))))
            if ref is None: continue
            a1, a0 = amean.get((area, day(I + dt.timedelta(1)))), amean.get((area, day(I)))
            if a1 is None or a0 is None: continue
            mom = a1 - a0
            for k in range(ref_off + 1, 10):
                t = I + dt.timedelta(k); a = amean.get((area, day(t)))
                if a is None: continue
                f = fc.get(t)
                if f is None and k == 1: f = a     # D+1 known exactly
                if f is None: continue
                da, df = a - ref, f - ref
                hits[k].append(sgn(df) == sgn(da)); up[k].append(da > 0)
                lw = amean.get((area, day(t - dt.timedelta(7))))
                if lw is not None: hw[k].append(sgn(lw - ref) == sgn(da))
                if ref_off == 0: hm[k].append(sgn(mom) == sgn(da))  # momentum: continue last known change
                if k >= 2: mag[min(3, int(abs(df) // 100))].append(sgn(df) == sgn(da))
        for k in sorted(hits):
            s = "  D+%d n=%2d fc-hit %3.0f%%  weekday-last-week %3.0f%% (n=%d)" % (k, len(hits[k]), 100*st.mean(hits[k]), 100*st.mean(hw[k]) if hw[k] else float('nan'), len(hw[k]))
            if hm[k]: s += "  momentum %3.0f%%" % (100*st.mean(hm[k]))
            s += "  share actual rises %3.0f%%" % (100*st.mean(up[k]))
            print(s)
        print("  by |forecast move| (k>=2):", "  ".join("%s: %3.0f%% (n=%d)" % (["<100", "100-200", "200-300", ">=300"][b], 100*st.mean(v), len(v)) for b, v in sorted(mag.items())))
    # mean over D+2..D+6 vs today / vs D+1, cheapest day, spearman
    for lo, hi, ref_off in ((1, 6, 0), (2, 7, 1)):
        hit = []; hitw = []; ch = []; chw = []; within = defaultdict(list); sp = []; spw = []; regret = []; regw = []; mags = []
        for I, fc in runs.items():
            days = [I + dt.timedelta(k) for k in range(lo, hi + 1)]
            act = [amean.get((area, day(t))) for t in days]
            f = [fc.get(t, amean.get((area, day(t))) if (t - I).days == 1 else None) for t in days]
            lw = [amean.get((area, day(t - dt.timedelta(7)))) for t in days]
            ref = amean.get((area, day(I + dt.timedelta(ref_off))))
            if None in act or None in f or None in lw or ref is None: continue
            da, df, dw = st.mean(act) - ref, st.mean(f) - ref, st.mean(lw) - ref
            hit.append(sgn(da) == sgn(df)); hitw.append(sgn(da) == sgn(dw)); mags.append((abs(df), sgn(da) == sgn(df)))
            ia = min(range(len(act)), key=lambda i: act[i]); i_f = min(range(len(f)), key=lambda i: f[i]); iw = min(range(len(lw)), key=lambda i: lw[i])
            ch.append(ia == i_f); chw.append(ia == iw)
            regret.append(act[i_f] - act[ia]); regw.append(act[iw] - act[ia])
            for X in (50, 100, 200): within[X].append(act[i_f] - act[ia] <= X)
            sp.append(spearman(f, act)); spw.append(spearman(lw, act))
        n = len(hit)
        if not n: continue
        print("  window D+%d..D+%d (ref D+%d), runs n=%d" % (lo, hi, ref_off, n))
        print("    mean-move direction: forecast %.0f%%  weekday-last-week %.0f%%" % (100*st.mean(hit), 100*st.mean(hitw)))
        print("    by |fc move|: " + "  ".join("%s %.0f%%(n=%d)" % (lab, 100*st.mean([h for m, h in mags if c(m)]), sum(1 for m, _ in mags if c(m))) for lab, c in (("<100", lambda m: m < 100), (">=100", lambda m: m >= 100)) if any(c(m) for m, _ in mags)))
        print("    cheapest day exact: forecast %.0f%%  weekday-last-week %.0f%%  random %.0f%%" % (100*st.mean(ch), 100*st.mean(chw), 100/(hi-lo+1)))
        print("    cheapest-day regret (DKK/MWh, daily mean): forecast mean %.0f median %.0f; weekday-last-week mean %.0f" % (st.mean(regret), st.median(regret), st.mean(regw)))
        print("    within X of cheapest: " + " ".join("%d:%.0f%%" % (X, 100*st.mean(v)) for X, v in within.items()))
        print("    Spearman fc vs actual: mean %.2f median %.2f | weekday-last-week mean %.2f" % (st.mean(sp), st.median(sp), st.mean(spw)))
