"""Exp 3: real DK1 hourly day-ahead prices (Energi Data Service, Jan-Sep 2025).

A 75 kWh car, 11 kW, taper 11 kW to 60 kWh (80 %), 7 kW to 67.5 kWh, 3.5 kW above.
Each instance: a 168 h horizon starting 16:00 local on a random day. Weekday commute: away
07:00-17:00, 6-20 kWh used; target at 07:00 = max(30 kWh, 11.25 + use). One random day has a long
trip instead: 07:00-20:00, 30-50 kWh used, target max(60, 11.25 + use) capped at 75.
Start SoC 15-45 kWh. Buffer folded into the 07:00 deadline (charging must end by 07:00)."""
import os
import json, random, sys, datetime as dt
from model import *

recs = json.load(open(sys.argv[1]))["records"]
prices = [r["SpotPriceEUR"] for r in recs]
if os.environ.get("NONNEG"):
    prices = [max(0.0, x) for x in prices]
print("hours with negative price: %d of %d" % (sum(1 for x in [r["SpotPriceEUR"] for r in recs] if x < 0), len(recs)))
hours_dk = [dt.datetime.fromisoformat(r["HourDK"]) for r in recs]

def taper_real(s):
    return 11.0 if s < 60 else (7.0 if s < 67.5 else 3.5)

import os
taper = (lambda s: 11.0) if os.environ.get("CONST") else taper_real

def make(rng):
    while True:
        i = rng.randrange(0, len(prices) - 200)
        if hours_dk[i].hour == 16:
            break
    p = prices[i:i + 168]
    h = hours_dk[i:i + 168]
    avail = [True] * 168
    tg = []
    long_day = rng.randrange(1, 7)
    for t in range(168):
        if h[t].hour == 7 and t > 0:
            day = (h[t] - h[0]).days + (1 if h[0].hour > 7 else 0)
            wd = h[t].weekday()
            if day == long_day:
                use = rng.uniform(30, 50); back = 13
                own = min(75.0, max(60.0, 11.25 + use))
            elif wd < 5:
                use = rng.uniform(6, 20); back = 10
                own = max(30.0, 11.25 + use)
            else:
                continue
            for u in range(t, min(168, t + back)):
                avail[u] = False
            tg.append(dict(d=t, own=own, cap=(400.0 if os.environ.get("NOCAP") else 75.0), cons=use))
    if not tg:
        return make(rng)
    p = p + [0.0]
    avail = avail + [False]
    q = lambda x: round(x * 4) / 4
    for x in tg:
        x["own"] = q(x["own"]); x["cons"] = q(x["cons"])
    return Inst(p, 1.0, avail, q(rng.uniform(15, 45)), tg, taper)

def asap(inst):
    sel = {t: 1.0 for t in range(inst.T) if inst.avail[t]}
    req = [x["own"] for x in inst.tg]
    sel = trim_slots(inst, sel, req, "chrono")
    c, at, ok = simulate(inst, sel)
    return c, ok

N = int(sys.argv[2]) if len(sys.argv) > 2 else 40
rng = random.Random(2025)
rows = []
for n in range(N):
    inst = make(rng)
    opt = dp_energy(inst, 0.25)
    if opt == float("inf"):
        continue
    r = dict(opt=opt)
    for name, inc, tr in [("cum+chrono", False, "chrono"), ("cum+price", False, "price"), ("inc+price", True, "price")]:
        c, ok, s = greedy_d22(inst, trim=tr, incremental=inc)
        r[name] = c if ok else float("inf")
    r["asap"] = asap(inst)[0]
    r["kwh"] = None
    rows.append(r)
print("instances", len(rows))
for name in ["cum+chrono", "cum+price", "inc+price", "asap"]:
    gaps = sorted((r[name] - r["opt"]) / abs(r["opt"]) * 100 for r in rows if abs(r["opt"]) > 1000)
    absg = sorted((r[name] - r["opt"]) for r in rows)
    inf = sum(1 for r in rows if r[name] == float("inf"))
    fin = [g for g in gaps if g != float("inf")]
    print("%-10s infeasible %d | rel gap %%: median %.2f p90 %.2f max %.2f | abs gap EUR: median %.3f p90 %.3f max %.3f; worse than opt by >1%% in %d of %d" % (
        name, inf, fin[len(fin)//2], fin[int(len(fin)*0.9)], fin[-1], absg[len(absg)//2]/1000, absg[int(len(absg)*0.9)]/1000, max(a for a in absg if a != float('inf'))/1000, sum(1 for r in rows if r[name] > r["opt"] + max(0.01*abs(r["opt"]), 1)), len(rows)))
print("mean opt cost (EUR/MWh x kWh -> /1000 = EUR): %.2f EUR" % (sum(r['opt'] for r in rows) / len(rows) / 1000))
