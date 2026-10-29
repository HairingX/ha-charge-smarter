"""Exp 1: constant power, whole-unit slots. Greedy variants vs exact DP."""
import random
from model import *

def rand_inst(rng, caps):
    T = rng.randint(4, 9)
    prices = [rng.randint(1, 9) for _ in range(T)]
    K = rng.randint(1, 3)
    ds = sorted(rng.sample(range(1, T + 1), K))
    tg = []
    C = 6
    for d in ds:
        own = rng.randint(0, 4)
        cons = rng.randint(0, 2)
        own = max(own, cons)
        cap = rng.randint(max(own, 2), C) if caps else C
        tg.append(dict(d=d, own=float(own), cap=float(cap), cons=float(cons)))
    avail = [True] * T + [False]
    prices.append(0)
    return Inst(prices, 1.0, avail, float(rng.randint(0, 2)), tg, lambda s: 1.0)

V = [("cum+chrono", False, "chrono"), ("cum+price", False, "price"),
     ("inc+chrono", True, "chrono"), ("inc+price", True, "price")]
for caps in (False, True):
    rng = random.Random(7 if not caps else 8)
    n = 0
    worse = {v[0]: 0 for v in V}
    gapsum = {v[0]: 0.0 for v in V}
    worst = {v[0]: (0.0, None) for v in V}
    while n < 4000:
        inst = rand_inst(rng, caps)
        opt = dp_exact(inst, grid=0.001, fsteps=4)
        if opt == float("inf"):
            continue
        n += 1
        for name, inc, tr in V:
            c, ok, s = greedy_d22(inst, trim=tr, incremental=inc)
            if not ok:
                c = float("inf")
            if c > opt + 1e-4:
                worse[name] += 1
                g = (c - opt) / max(opt, 1e-9)
                gapsum[name] += min(g, 10)
                if g > worst[name][0] or worst[name][1] is None or (g == worst[name][0] and inst.T < worst[name][1][0].T):
                    worst[name] = (g, (inst, opt, c, s))
    print("caps" if caps else "nocaps", "instances", n)
    for name, *_ in V:
        print("  %-11s suboptimal %4d (%.1f%%)" % (name, worse[name], 100 * worse[name] / n))
        g, w = worst[name]
        if w:
            i, o, c, s = w
            print("     worst rel gap %.2f: prices %s s0 %s targets %s opt %.2f got %.2f sel %s" % (
                g, i.p[:-1], i.s0, [(x['d'], x['own'], x['cap'], x['cons']) for x in i.tg], o, c,
                {k: round(v, 2) for k, v in sorted(s.items())}))
