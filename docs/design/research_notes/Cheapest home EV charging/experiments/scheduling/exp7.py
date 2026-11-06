"""Smallest counterexamples by random search."""
import random
from model import *
def taper(s): return 2.0 if s < 6 else (1.0 if s < 8.5 else 0.5)
def inst_of(prices, s0, tg, power, ramp=None, cap=10.0):
    T = len(prices)
    return Inst(prices + [0.0], 1.0, [True] * T + [False], s0, [dict(d=d, own=o, cap=cap, cons=c) for d, o, c in tg], power, ramp)
def search(power, K, T, variant, seed, ramp=None, integer=False, tries=20000):
    rng = random.Random(seed)
    best = None
    for _ in range(tries):
        prices = [float(rng.randint(1, 9)) for _ in range(T)]
        ds = sorted(rng.sample(range(1, T + 1), K))
        tg = []
        for d in ds:
            c = float(rng.randint(0, 2)) if integer else round(rng.uniform(0, 2), 1)
            o = float(rng.randint(1, 8)) if integer else round(rng.uniform(1, 9), 1)
            tg.append((d, max(o, c), c))
        s0 = float(rng.randint(0, 3)) if integer else round(rng.uniform(0, 4), 1)
        I = inst_of(prices, s0, tg, power, ramp)
        opt = dp_exact(I, grid=0.01, fsteps=20)
        if opt == float("inf"): continue
        c, ok, sel = greedy_d22(I, trim=variant[1], incremental=variant[0])
        if ok and c > opt * 1.02 + 1e-6:
            return prices, s0, tg, opt, c, {k: round(v, 3) for k, v in sorted(sel.items())}
    return None
print("CE-A cum+chrono, const 1 kW, integer:", search(lambda s: 1.0, 2, 4, (False, "chrono"), 1, integer=True))
print("CE-B any partial, const 2 kW, 1 target, cum+chrono:", search(lambda s: 2.0, 1, 3, (False, "chrono"), 2))
print("CE-C taper, 1 target, cum+price:", search(taper, 1, 4, (False, "price"), 3))
print("CE-C2 taper, 2 targets, cum+price:", search(taper, 2, 4, (False, "price"), 4))
print("CE-D ramp 0.5h@0.5kW, 1 target, cum+price:", search(lambda s: 2.0, 1, 4, (False, "price"), 5, ramp=(0.5, 0.5)))
