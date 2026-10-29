"""Exp 2: fractional needs (partial slots), SoC taper, session ramp. Greedy vs DP."""
import random, sys
from model import *

def taper(s):  # capacity 10: 2 kW below 6, 1 kW from 6, 0.5 kW from 8.5
    return 2.0 if s < 6 else (1.0 if s < 8.5 else 0.5)

def rand_inst(rng, power, ramp=None):
    T = rng.randint(4, 8)
    prices = [round(rng.uniform(1, 9), 1) for _ in range(T)]
    K = rng.randint(1, 3)
    ds = sorted(rng.sample(range(1, T + 1), K))
    tg = []
    for d in ds:
        cons = round(rng.uniform(0, 3), 1)
        own = max(round(rng.uniform(1, 9), 1), cons)
        tg.append(dict(d=d, own=own, cap=10.0, cons=cons))
    avail = [True] * T + [False]
    prices.append(0)
    return Inst(prices, 1.0, avail, round(rng.uniform(0, 4), 1), tg, power, ramp)

cases = [("const 2kW, partial", lambda s: 2.0, None),
         ("taper", taper, None),
         ("const 2kW + ramp 0.5h@0.5kW", lambda s: 2.0, (0.5, 0.5))]
V = [("cum+chrono", False, "chrono"), ("cum+price", False, "price"), ("inc+price", True, "price")]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 800
for title, pw, ramp in cases:
    rng = random.Random(11)
    n = 0
    stat = {v[0]: [0, 0.0, 0.0, None] for v in V}  # count worse, sum gap, max gap, example
    while n < N:
        inst = rand_inst(rng, pw, ramp)
        opt = dp_exact(inst, grid=0.01, fsteps=20)
        if opt == float("inf") or opt <= 0:
            continue
        n += 1
        for name, inc, tr in V:
            c, ok, s = greedy_d22(inst, trim=tr, incremental=inc)
            if not ok:
                stat[name][0] += 1
                continue
            g = (c - opt) / opt
            if g > 0.005:
                stat[name][0] += 1
                stat[name][1] += g
                if g > stat[name][2]:
                    stat[name][2] = g
                    stat[name][3] = (inst, opt, c, s)
    print(title, "instances", n)
    for name, *_ in V:
        w, sg, mg, ex = stat[name]
        print("  %-10s worse(>0.5%%) %4d (%.1f%%), mean gap when worse %.1f%%, max %.1f%%" % (
            name, w, 100 * w / n, 100 * sg / max(w, 1), 100 * mg))
        if ex and name == "cum+price":
            i, o, c, s = ex
            print("     example: prices %s s0 %s targets %s opt %.2f got %.2f sel %s" % (
                i.p[:-1], i.s0, [(x['d'], x['own'], x['cons']) for x in i.tg], o, c,
                {k: round(v, 2) for k, v in sorted(s.items())}))
