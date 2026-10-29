"""Exp 4: timing in CPython of candidate algorithms on 168 hourly and 672 quarter-hour slots."""
import time, random, sys, platform
from model import *

def taper(s):
    return 11.0 if s < 60 else (7.0 if s < 67.5 else 3.5)

def make(T, L, K, seed=1):
    rng = random.Random(seed)
    prices = [rng.uniform(0, 300) for _ in range(T)] + [0.0]
    avail = [True] * T + [False]
    ds = sorted(rng.sample(range(T // (K + 1), T), K))
    tg = [dict(d=d, own=float(rng.choice([30, 40, 50])), cap=75.0, cons=float(rng.choice([4, 8, 12]))) for d in ds]
    for x in tg:
        for u in range(x["d"], min(T, x["d"] + int(2 / L))):
            avail[u] = False
    return Inst(prices, L, avail, 20.0, tg, taper)

def dp_binary(inst, buckets=200, session=False, cap_kwh=75.0):
    """Backward DP over (slot, SoC bucket[, charging in previous slot]); per slot: off or on
    for the whole slot, the charge stopping at the bucket of the target cap. Returns cost."""
    g = cap_kwh / buckets
    B = buckets
    # precompute per bucket the bucket after one full slot, and the energy
    nxt = [0] * (B + 1)
    en = [0.0] * (B + 1)
    for b in range(B + 1):
        _, s2, _ = charge(inst, b * g, inst.L, cap_kwh, 1e9)
        nb = min(B, int(round(s2 / g)))
        nxt[b] = nb
        en[b] = (nb - b) * g
    INF = float("inf")
    T = inst.T
    V = [0.0] * (B + 1)  # after the horizon nothing is needed
    for t in range(T - 1, -1, -1):
        if inst.avail[t]:
            p = inst.p[t]
            W = [0.0] * (B + 1)
            for b in range(B + 1):
                a = V[b]
                c = p * en[b] + V[nxt[b]]
                W[b] = a if a < c else c
            V = W
        k = inst.deadline_at.get(t)
        if k is not None:
            own = int(-(-inst.tg[k]["own"] // g))
            cons = int(round(inst.tg[k]["cons"] / g))
            W = [INF] * (B + 1)
            for b in range(own, B + 1):
                if b - cons >= 0:
                    W[b] = V[b - cons]
            V = W
    return V[int(round(inst.s0 / g))]

def bench(fn, reps=5):
    best = 1e9
    for _ in range(reps):
        t0 = time.perf_counter(); fn(); best = min(best, time.perf_counter() - t0)
    return best * 1000

if __name__ == "__main__":
  print(platform.python_implementation(), platform.python_version(), platform.machine())
  for T, L in [(168, 1.0), (672, 0.25)]:
      for K in (6, 20):
          inst = make(T, L, K)
          print("T=%d L=%.2fh K=%d" % (T, L, K))
          print("  greedy (experimental O(T^2) sims, cum+price) %.0f ms" % bench(lambda: greedy_d22(inst, trim="price"), 1))
          for B in (100, 200, 400):
              print("  dp_binary %d buckets: %.1f ms" % (B, bench(lambda: dp_binary(inst, B))))
          if L == 1.0:
              print("  dp_energy g=0.25 kWh: %.0f ms" % bench(lambda: dp_energy(inst, 0.25), 1))
