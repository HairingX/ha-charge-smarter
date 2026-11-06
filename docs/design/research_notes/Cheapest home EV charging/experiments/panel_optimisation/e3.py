"""E3: cost of speed-ups vs the exact quarter-hour DP at g = 0.25 kWh (Danish total price,
taper). (a) coarser SoC grids, including grids aligned to 11 kW x 15 min = 2.75 kWh;
(b) hourly DP on hourly-mean prices, each hour's energy then placed in that hour's cheapest
quarters; (c) mixed resolution: quarters for the first 35 h, hours after, the tail priced at the
hourly mean of the true quarters. 'inf' = the plan, re-simulated on the true (unrounded) values,
misses a floor: start SoC and consumption are rounded to the grid, not conservatively."""
import sys, time, random
sys.argv = ['x', '0']
exec(open('e1.py').read().split('N = int')[0])
import fulldp as F
from e2 import convert

def ev_cost(inst, energy):
    s = inst.s0; c = 0.0; ok = True; bought = 0.0
    for t in range(inst.T):
        k = inst.deadline_at.get(t)
        if k is not None:
            if s < inst.tg[k]["own"] - 1e-6: ok = False
            s -= inst.tg[k]["cons"]
        c += energy[t] * inst.p[t]; s += energy[t]; bought += energy[t]
    return c, ok, bought

pre = {}
def P_(g, Ls):
    k = (g, tuple(sorted(set(Ls))))
    if k not in pre: pre[k] = F.precompute(g, 75.0, list(set(Ls)), taper, 11.0, 1.0, 0.0)
    return pre[k]

N = 60
rng = random.Random(11)
keys = ("g0.275", "g0.5", "g0.55", "g1.0", "g1.1", "hour+refine", "mixed35h")
res = {k: [] for k in keys}; resn = {k: [] for k in keys}
tim = {k: [] for k in list(keys) + ["exact"]}
for n in range(N):
    inst = make(rng, P.total, P.times, 0.25, taper)
    slots, ev = convert(inst)
    S, W, tops = P_(0.25, [0.25])
    t0 = time.perf_counter(); c0, e0 = F.plan(slots, ev, inst.s0, False, 0.25, S, W, tops); tim["exact"].append(time.perf_counter() - t0)
    _, _, b0 = ev_cost(inst, e0); unit0 = c0 / b0
    def rec(k, energy, dt_):
        c, ok, b = ev_cost(inst, energy)
        res[k].append((c - c0) / c0 * 100 if ok else float('inf'))
        resn[k].append((c - (b - b0) * unit0 - c0) / c0 * 100 if ok else float('inf'))
        tim[k].append(dt_)
    for g in (0.275, 0.5, 0.55, 1.0, 1.1):
        S, W, tops = P_(g, [0.25])
        t0 = time.perf_counter(); c, e = F.plan(slots, ev, inst.s0, False, g, S, W, tops); rec("g%s" % g, e, time.perf_counter() - t0)
    T4 = inst.T // 4
    hs = [(1.0, sum(inst.p[4*h:4*h+4]) / 4, all(inst.avail[4*h:4*h+4]), 75.0) for h in range(T4)] + [(1.0, 0.0, False, 75.0)]
    hev = {}
    for x in inst.tg: hev.setdefault(x["d"] // 4, []).extend([("hard", x["own"], None), ("cons", x["cons"], None)])
    S, W, tops = P_(0.25, [1.0])
    t0 = time.perf_counter()
    ch, eh = F.plan(hs, hev, inst.s0, False, 0.25, S, W, tops)
    en = [0.0] * inst.T; s = inst.s0
    for h in range(T4):
        k = inst.deadline_at.get(4*h)
        if k is not None: s -= inst.tg[k]["cons"]
        need = eh[h]
        for q in sorted(range(4*h, 4*h+4), key=lambda q: (inst.p[q], -q)):
            if need <= 1e-9: break
            e = min(need, taper(s) * 0.25); en[q] = e; need -= e
        s += eh[h] - need
    rec("hour+refine", en, time.perf_counter() - t0)
    ms = slots[:140]; mev = {t: v for t, v in ev.items() if t < 140}
    for h in range(35, T4):
        ms.append((1.0, sum(inst.p[4*h:4*h+4]) / 4, all(inst.avail[4*h:4*h+4]), 75.0))
        if 4*h in ev: mev[len(ms) - 1] = ev[4*h]
    ms.append((1.0, 0.0, False, 75.0))
    S, W, tops = P_(0.25, [0.25, 1.0])
    t0 = time.perf_counter(); cm, em = F.plan(ms, mev, inst.s0, False, 0.25, S, W, tops); dt_ = time.perf_counter() - t0
    res["mixed35h"].append((cm - c0) / c0 * 100); resn["mixed35h"].append((cm - c0) / c0 * 100); tim["mixed35h"].append(dt_)
    S, W, tops = P_(0.55, [0.25, 1.0])
    t0 = time.perf_counter(); F.plan(ms, mev, inst.s0, False, 0.55, S, W, tops); tim.setdefault("mixed35h g0.55", []).append(time.perf_counter() - t0)
for k in keys:
    v = sorted(res[k]); w = sorted(resn[k])
    print("%-12s raw gap median %.2f%% p90 %.2f%% max %.2f%% | carried-energy-adjusted median %.2f%% p90 %.2f%% max %.2f%%" % (k, v[len(v)//2], v[int(len(v)*.9)], v[-1], w[len(w)//2], w[int(len(w)*.9)], w[-1]))
for k, v in tim.items():
    v = sorted(v); print("%-16s time median %.1f ms" % (k, v[len(v)//2] * 1000))
