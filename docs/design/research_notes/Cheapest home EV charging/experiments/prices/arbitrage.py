"""Value of charging beyond each night's need (inter-day arbitrage) on Danish total prices.

Args: path to dap.json (Energi Data Service DayAheadPrices), kWh used per day (default 7.5).
Hourly billing (mean of the quarters); tariffs as in price_composition_denmark.md section 1;
2026 flat parts throughout. Compares floor-only, a perfect-foresight oracle with limited
headroom, and a percentile fill rule (O1 c)."""
import json, sys, statistics as st, datetime as dt
from collections import defaultdict
recs = json.load(open(sys.argv[1]))["records"]
TAR = {"DK1": {"w": (0.088, 0.264, 0.791), "s": (0.088, 0.132, 0.343)},
       "DK2": {"w": (0.106, 0.319, 0.956), "s": (0.106, 0.159, 0.414)}}
def tariff(area, t):
    lo, hi, pk = TAR[area]["w" if t.month in (10, 11, 12, 1, 2, 3) else "s"][0:3]
    h = t.hour
    return lo if h < 6 else (pk if 17 <= h < 21 else hi)
def flat(t):  # Energinet + elafgift, excl VAT
    return 0.115 + 0.008  # 2026 flat parts throughout, to remove the 1 Jan elafgift step
P = 11.0; C = float(sys.argv[2]) if len(sys.argv) > 2 else 7.5
for area in ("DK1", "DK2"):
    q = defaultdict(list); qq = {}
    for r in recs:
        if r["PriceArea"] != area: continue
        utc = dt.datetime.fromisoformat(r["TimeUTC"]).replace(tzinfo=dt.timezone.utc)
        loc = dt.datetime.fromisoformat(r["TimeDK"])
        key = utc.replace(minute=0)
        q[key].append((loc, r["DayAheadPriceDKK"] / 1000))
    hourly = {}
    for k, v in q.items():
        loc = v[0][0].replace(minute=0)
        spot = st.mean(x[1] for x in v)
        hourly[k] = (loc, spot, 1.25 * (spot + tariff(area, loc) + flat(loc)))
    # nights: local 17:00 .. 07:00 next day
    bynight = defaultdict(list)
    for k, (loc, spot, tot) in hourly.items():
        d = loc.date() if loc.hour >= 17 else (loc.date() - dt.timedelta(1) if loc.hour < 7 else None)
        if d is not None: bynight[d].append((k, tot))
    nights = sorted(d for d, v in bynight.items() if len(v) >= 13 and d >= dt.date(2025, 10, 1) and d <= dt.date(2026, 10, 27))
    prices = {d: sorted(p for _, p in bynight[d]) for d in nights}
    def cost_buy(d, e):  # cheapest hours, 11 kWh each
        c = 0.0; i = 0; ps = prices[d]
        while e > 1e-9 and i < len(ps):
            x = min(P, e); c += x * ps[i]; e -= x; i += 1
        return c if e < 1e-9 else float("inf")
    N = len(nights)
    floor = sum(cost_buy(d, C) for d in nights)
    allp = sorted(p for d in nights for p in prices[d])
    neg = sum(1 for d in nights for p in prices[d] if p < 0)
    print(f"== {area}: {N} nights, C={C} kWh/night, energy {N*C:.0f} kWh; floor cost {floor:.0f} DKK, avg {floor/(N*C):.3f} DKK/kWh; hours total<0 in window: {neg}")
    # spread of night-cheapest prices across nights
    nc = [cost_buy(d, C) / C for d in nights]
    dif = [abs(nc[i+1]-nc[i]) for i in range(N-1)]
    print(f"   night avg price for C: mean {st.mean(nc):.3f} sd {st.pstdev(nc):.3f}; mean |night-to-night change| {st.mean(dif):.3f} DKK/kWh")
    G = 0.5
    for H in (7.5, 15, 30):
        S = int(round(H / G))
        # DP: inventory above floor h in [0,S] after each night's charge; day uses C.
        # marginal cost of buying C + delta at night d
        INF = float("inf"); V = [0.0] + [INF] * S  # start with 0 extra
        held = 0.0
        pol = []
        for d in nights:
            cb = [cost_buy(d, max(0.0, C + j * G)) if C + j * G >= 0 else 0 for j in range(-S, S + 1)]
            NV = [INF] * (S + 1); arg = [0] * (S + 1)
            for h0 in range(S + 1):
                if V[h0] == INF: continue
                for h1 in range(S + 1):
                    buy = (h1 - h0)  # extra relative to C, in grid units
                    e = C + buy * G
                    if e < 0: continue
                    v = V[h0] + cb[buy + S]
                    if v < NV[h1]: NV[h1] = v; arg[h1] = h0
            V = NV; pol.append(arg)
        best = V[0]
        # backtrack inventory path
        h = 0; path = []
        for arg in reversed(pol):
            path.append(h); h = arg[h]
        path.reverse()
        avg_extra = st.mean(path) * G
        print(f"   oracle headroom {H:>4} kWh: cost {best:.0f}, saving vs floor {floor-best:.0f} DKK ({100*(floor-best)/floor:.1f} %), "
              f"{(floor-best)/N*365:.0f} DKK/yr; mean extra stored {avg_extra:.1f} kWh; nights with extra>0: {100*sum(1 for x in path if x>0)/N:.0f} %")
    # O1(c) percentile rule on the known horizon at 17:00 (tonight + tomorrow 07-24), fill to headroom H
    for H in (15, 30):
        for pct in (10, 25):
            inv = 0.0; cost = 0.0; ext = []
            for i, d in enumerate(nights):
                known = [p for _, p in bynight[d]] + [hourly[k][2] for k in hourly if hourly[k][0].date() == d + dt.timedelta(1) and 7 <= hourly[k][0].hour]
                thr = sorted(known)[int(len(known) * pct / 100)]
                need = max(0.0, C - inv)
                # buy need in cheapest hours; then fill extra in hours <= thr not already used
                ps = prices[d]; e = need; c = 0.0; j = 0
                while e > 1e-9: x = min(P, e); c += x * ps[j]; e -= x; rem = P - x; j += 1
                # remaining capacity: partial of last hour + further hours below thr
                room = C + H - (inv + need); extra = 0.0
                avail = ([(rem, ps[j-1])] if need > 0 and rem > 0 else []) + [(P, p) for p in ps[j:]]
                for cap_, p in avail:
                    if p > thr or room <= 1e-9: continue
                    x = min(cap_, room); extra += x; c += x * p; room -= x
                inv = inv + need + extra - C; cost += c; ext.append(inv)
            cost += -inv * st.mean(nc)  # credit leftover at mean night price
            print(f"   O1(c) pct {pct:>2} headroom {H}: cost {cost:.0f} vs floor {floor:.0f} ({cost-floor:+.0f} DKK, {(cost-floor)/N*365:+.0f}/yr); mean extra stored {st.mean(ext):.1f} kWh; nights extra>0 {100*sum(1 for x in ext if x>1e-6)/N:.0f} %")
