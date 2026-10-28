"""E1: greedy (D22 corrected: cum + price-ordered trim) vs exact DP on DK1 2025-10..2026-10,
spot only vs Danish total price with time-of-use tariff, hourly vs quarter-hour slots.
Schedules and car as in exp3.py of the scheduling note (75 kWh, 11 kW, taper 7 kW from 60 kWh,
3.5 kW from 67.5 kWh; weekday commute 07-17, 6-20 kWh; one long trip 07-20, 30-50 kWh)."""
import random, sys, time
from model import Inst, greedy_d22, dp_energy_fast
import prices as P

def taper(s): return 11.0 if s < 60 else (7.0 if s < 67.5 else 3.5)
def const(s): return 11.0

def make(rng, series, ts, L, power):
    per_h = int(round(1 / L)); T = 168 * per_h
    while True:
        i = rng.randrange(0, len(series) - T - 10)
        if ts[i].hour == 16 and ts[i].minute == 0: break
    p = series[i:i + T]; h = ts[i:i + T]
    avail = [True] * T; tg = []
    long_day = rng.randrange(1, 7)
    for t in range(T):
        if h[t].hour == 7 and h[t].minute == 0 and t > 0:
            day = (h[t].date() - h[0].date()).days
            wd = h[t].weekday()
            if day == long_day:
                use = rng.uniform(30, 50); back = 13; own = min(75.0, max(60.0, 11.25 + use))
            elif wd < 5:
                use = rng.uniform(6, 20); back = 10; own = max(30.0, 11.25 + use)
            else: continue
            for u in range(t, min(T, t + back * per_h)): avail[u] = False
            tg.append(dict(d=t, own=own, cap=75.0, cons=use))
    if not tg: return make(rng, series, ts, L, power)
    q = lambda x: round(x * 4) / 4
    for x in tg: x["own"] = q(x["own"]); x["cons"] = q(x["cons"])
    return Inst(p + [0.0], L, avail + [False], q(rng.uniform(15, 45)), tg, power)

N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
hs, hts = P.hourly(P.spot); ht, _ = P.hourly(P.total)
cases = [("spot, hourly", hs, hts, 1.0), ("total, hourly", ht, hts, 1.0),
         ("spot, 15 min", P.spot, P.times, 0.25), ("total, 15 min", P.total, P.times, 0.25)]
for pname, power in (("taper", taper), ("const 11 kW", const)):
    for name, ser, ts, L in cases:
        rng = random.Random(2026)
        gaps, absg, opts, tg_, td_ = [], [], [], 0.0, 0.0
        for n in range(N):
            inst = make(rng, ser, ts, L, power)
            t0 = time.perf_counter(); opt = dp_energy_fast(inst, 0.25); td_ += time.perf_counter() - t0
            t0 = time.perf_counter(); c, ok, _ = greedy_d22(inst, trim="price"); tg_ += time.perf_counter() - t0
            if not ok: c = float("inf")
            gaps.append((c - opt) / opt * 100); absg.append(c - opt); opts.append(opt)
        gaps.sort(); absg.sort()
        print("%-11s %-14s N=%d gap%%: median %.2f p90 %.2f max %.2f | abs DKK/wk: median %.2f p90 %.2f max %.2f | mean opt %.1f DKK/wk | worse>1%% in %d" % (
            pname, name, N, gaps[N // 2], gaps[int(N * .9)], gaps[-1], absg[N // 2], absg[int(N * .9)], absg[-1],
            sum(opts) / N, sum(1 for g in gaps if g > 1)), flush=True)
