"""E5: charging beyond the floors (O1) in a rolling daily re-plan with real elpriser.org DK1
forecasts (23 runs issued 2026-10-06..28) and actual DK1 quarter prices, Danish total price.
Car 75 kWh, 11 kW + taper; away every day 07-17 using U kWh; hard floor 15 + U kWh at 07:00.
Decision at 13:00 on issue day D (actual prices known to the end of D+1); the first 24 h of each
plan are executed. Policies differ only in what the engine is given beyond the known prices."""
import json, glob, os, datetime as dt, statistics as st, sys
import prices as P, fulldp as F
U = float(sys.argv[1]) if len(sys.argv) > 1 else 12.0
RES = 15.0
def taper(s): return 11.0 if s < 60 else (7.0 if s < 67.5 else 3.5)
g = 0.25
S, W, tops = F.precompute(g, 75.0, [0.25, 1.0], taper, 11.0, 1.0, 0.0)
idx = {t: i for i, t in enumerate(P.times)}
def tot(spot_kwh, t): return (spot_kwh + P.tariff(t) + 0.123) * 1.25
runs = {}
for f in sorted(glob.glob(os.path.join(os.environ.get("ARCH_DIR", os.path.join("..", "data")), "arch_DK1_*.json"))):
    d = json.load(open(f)); D = dt.date.fromisoformat(d["issued"])
    fc = {}
    for dd in d["days"]:
        if dd["type"] == "forecast":
            day = dt.date.fromisoformat(dd["date"])
            for p in dd["prices"]: fc[dt.datetime.combine(day, dt.time(p["hour"]))] = p["spot_dkk_mwh"] / 1000
    runs[D] = fc
issues = [D for D in sorted(runs) if dt.datetime.combine(D + dt.timedelta(2), dt.time(13)) in idx]
def actual_hour(t):
    i = idx.get(t)
    if i is None: return None
    return sum(P.total[i:i + 4]) / 4

def build(D, s_seen, policy, m=0.0):
    t0 = dt.datetime.combine(D, dt.time(13)); i0 = idx[t0]
    end_known = dt.datetime.combine(D + dt.timedelta(2), dt.time(0))
    nq = int((end_known - t0).total_seconds() // 900)
    slots, times = [], []
    for k in range(nq):
        t = P.times[i0 + k]; slots.append((0.25, P.total[i0 + k], True, 75.0)); times.append(t)
    if policy in ("chain", "oracle"):
        fc = runs[D]
        for h in range(8 * 24):
            t = end_known + dt.timedelta(hours=h)
            if policy == "oracle":
                a = actual_hour(t); pr = a if a is not None else (tot(fc[t], t) if t in fc else None)
            else:
                pr = tot(fc[t], t) + m if t in fc else None
            if pr is None: break
            slots.append((1.0, pr, True, 75.0)); times.append(t)
    # absences and targets
    ev = {}; avail = [True] * len(slots)
    for j, t in enumerate(times):
        if t.hour == 7 and t.minute == 0:
            ev[j] = [("hard", RES + U, None), ("cons", U, None)]
        if 7 <= t.hour < 17: avail[j] = False
    slots = [(L, p, a and av, c) for (L, p, a, c), av in zip(slots, avail)] + [(1.0, 0.0, False, 75.0)]
    term = None
    known_prices = [s[1] for s in slots[:nq] if s[2]]
    if policy == "pctl":     # O1(c): soft floor at 60 kWh at the end of known prices, valued at the 30th percentile
        pi = sorted(known_prices)[int(0.3 * len(known_prices))]
        ev.setdefault(nq, []).insert(0, ("soft", 60.0, pi))
    if policy == "flatvalue":  # flat value of stored energy up to 60 kWh = median forecast total (evcc-optimizer style)
        fc = runs[D]
        v = st.median(tot(fc[t], t) for t in fc)
        term = [min(b * g, 60.0) * v for b in range(S + 1)]
    return slots, ev, term, nq

def simulate(policy, m=0.0):
    s = 40.0; cost = 0.0; bought = 0.0; hi_hours = 0.0; feas = True; socs = []
    for D in issues:
        slots, ev, term, nq = build(D, s, policy, m)
        c, en = F.plan(slots, ev, s, False, g, S, W, tops, eps=1e-7, terminal=term)
        if en is None: feas = False; break
        t0 = dt.datetime.combine(D, dt.time(13)); i0 = idx[t0]
        for k in range(96):
            t = P.times[i0 + k]
            if t.hour == 7 and t.minute == 0:
                if s < RES + U - 1e-6: feas = False
                s -= U
            e = en[k]; s += e; cost += e * P.total[i0 + k]; bought += e
            if s > 55.0: hi_hours += 0.25
            socs.append(s)
    return cost, bought, s, hi_hours, feas, st.mean(socs)

out = {}
pols = [("known-only (O1a)", "known", 0.0), ("chain+fc m=0", "chain", 0.0), ("chain+fc m=0.05", "chain", 0.05),
        ("chain+fc m=0.10", "chain", 0.10), ("chain+fc m=0.30", "chain", 0.30), ("pctl30 fill to 60 (O1c)", "pctl", 0.0),
        ("flat value to 60 (b-like)", "flatvalue", 0.0), ("oracle (actual prices)", "oracle", 0.0)]
for name, pol, m in pols:
    out[name] = simulate(pol, m)
ref_price = out["oracle (actual prices)"][0] / out["oracle (actual prices)"][1]
base = None
print("U=%.0f kWh/day, %d daily decisions, consumption %.0f kWh" % (U, len(issues), U * len(issues)))
for name, (c, b, s_end, hi, ok, ms) in out.items():
    adj = c - (s_end - 40.0) * ref_price          # energy left over valued at the oracle's average price
    per = adj / (U * len(issues))
    out[name] = out[name] + (per,)
for name, v in out.items():
    per = v[-1]
    k0 = out["known-only (O1a)"][-1]; ko = out["oracle (actual prices)"][-1]
    share = (k0 - per) / (k0 - ko) * 100 if k0 != ko else float('nan')
    print("%-26s DKK/kWh used %.3f | share of oracle saving %5.0f%% | bought %.0f kWh, end SoC %.1f | hours SoC>55 kWh %.0f, mean SoC %.1f | floors met %s" % (
        name, per, share, v[1], v[2], v[3], v[5], v[4]))
