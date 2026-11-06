import json, sys, glob, os, statistics as st, datetime as dt
from collections import defaultdict
D = sys.argv[1]; H = 2; C = 10.0; SMAX = float(sys.argv[2]) if len(sys.argv) > 2 else 50.0; W = 6
recs = json.load(open(os.path.join(D, "dap.json")))["records"]
qh = defaultdict(list); qd = defaultdict(list)
for r in recs:
    qh[(r["PriceArea"], r["TimeDK"][:10], int(r["TimeDK"][11:13]))].append(r["DayAheadPriceDKK"])
    qd[(r["PriceArea"], r["TimeDK"][:10])].append(r["DayAheadPriceDKK"])
def cheap(vals): return st.mean(sorted(vals)[:H])
for area in ("DK1", "DK2"):
    hours = defaultdict(list)
    for (a, d, h), v in qh.items():
        if a == area: hours[d].append(st.mean(v))
    actual = {dt.date.fromisoformat(d): cheap(v) for d, v in hours.items()}
    dmean = {dt.date.fromisoformat(d): st.mean(v) for (a, d), v in qd.items() if a == area}
    runs = {}
    for f in sorted(glob.glob(os.path.join(D, f"arch_{area}_*.json"))):
        d = json.load(open(f)); I = dt.date.fromisoformat(d["issued"])
        fc = {}; fm = {}
        for dd in d["days"]:
            if dd["type"] == "forecast":
                t = dt.date.fromisoformat(dd["date"])
                fc[t] = cheap([p["spot_dkk_mwh"] for p in dd["prices"]]); fm[t] = st.mean(p["spot_dkk_mwh"] for p in dd["prices"])
        runs[I] = (fc, fm)
    issues = sorted(I for I in runs if I + dt.timedelta(1) in actual)
    def next_cheaper_target(prices):  # prices[0] = today's known price, then future
        for j in range(1, len(prices)):
            if prices[j] < prices[0]: return min(SMAX, C * j)
        return min(SMAX, C * len(prices))
    def run(policy):
        s = C; cost = 0.0; bought = 0.0
        for I in issues:
            t = I + dt.timedelta(1); p = actual[t]
            s -= C  # drive one day before this opportunity
            target = max(C, policy(I, t))
            buy = max(0.0, min(SMAX, target) - s)
            cost += buy * p / 1000; bought += buy; s += buy
        return cost, bought, s
    period_mean = st.mean(actual[I + dt.timedelta(1)] for I in issues)
    def floor_(I, t): return C
    def oracle(I, t):
        pr = [actual[t]] + [actual[t + dt.timedelta(k)] for k in range(1, W + 1) if t + dt.timedelta(k) in actual]
        return next_cheaper_target(pr)
    def fcast(P):
        def pol(I, t):
            fc = runs[I][0]
            pr = [actual[t]] + [fc[t + dt.timedelta(k)] + P for k in range(1, W + 1) if t + dt.timedelta(k) in fc]
            return next_cheaper_target(pr)
        return pol
    def trend(T, use_mean=True):
        def pol(I, t):
            fc, fm = runs[I]
            fut = [(fm if use_mean else fc)[t + dt.timedelta(k)] for k in range(1, 6) if t + dt.timedelta(k) in fc]
            base = dmean[t] if use_mean else actual[t]
            return SMAX if st.mean(fut) - base > T else C
        return pol
    def trend_mid(T):  # rising: cover until forecast trend turns; here: charge 3 days' worth
        def pol(I, t):
            fc, fm = runs[I]
            fut = [fm[t + dt.timedelta(k)] for k in range(1, 6) if t + dt.timedelta(k) in fm]
            return 3 * C if st.mean(fut) - dmean[t] > T else C
        return pol
    pols = [("floor only (= charge each day's need)", floor_), ("oracle next-cheaper-day (actual prices)", oracle)]
    pols += [("forecast next-cheaper, premium %d" % P, fcast(P)) for P in (0, 50, 100, 150, 200, 300)]
    pols += [("trend: daily-mean fc D+2..D+6 vs D+1 > %d -> fill to max" % T, trend(T)) for T in (0, 100, 200, 300)]
    pols += [("trend: same, cheapest-%dh prices > %d -> fill" % (H, T), trend(T, False)) for T in (0, 100, 200)]
    pols += [("trend: daily-mean > %d -> 3 days' worth" % T, trend_mid(T)) for T in (100, 200)]
    print("=" * 10, area, "decisions:", len(issues), issues[0], "..", issues[-1], "C=%g kWh/day SMAX=%g H=%d; terminal SoC valued at period mean %.0f DKK/MWh" % (C, SMAX, H, period_mean))
    base = None
    for name, pol in pols:
        cost, bought, s = run(pol)
        adj = cost + (C - s) * period_mean / 1000  # bring terminal SoC back to C
        if base is None: base = adj
        print("  %-62s cost %7.1f DKK  adj %7.1f  avg %.0f DKK/MWh  vs floor %+6.1f DKK (%+.1f%%)" % (name, cost, adj, 1000 * adj / (len(issues) * C), adj - base, 100 * (adj - base) / base))
