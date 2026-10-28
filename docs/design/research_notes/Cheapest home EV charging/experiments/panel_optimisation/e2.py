"""E2: validate fulldp against model.dp_energy_fast, check backtracking, time it."""
import sys, time, random
sys.argv = ['x', '0']
exec(open('e1.py').read().split('N = int')[0])
import fulldp as F

def convert(inst):
    slots = [(inst.L, inst.p[t], inst.avail[t], inst.cap_at[t]) for t in range(inst.T)]
    ev = {}
    for x in inst.tg:
        ev.setdefault(x["d"], []).extend([("hard", x["own"], None), ("cons", x["cons"], None)])
    return slots, ev

def resim(inst, energy, g):
    """Re-simulate energy per slot: cost at raw price, floors respected."""
    s = inst.s0; cost = 0.0; ok = True
    for t in range(inst.T):
        k = inst.deadline_at.get(t)
        if k is not None:
            if s < inst.tg[k]["own"] - 1e-6: ok = False
            s -= inst.tg[k]["cons"]
        e = energy[t] if t < len(energy) else 0.0
        if e > 0 and not inst.avail[t]: ok = False
        s += e; cost += e * inst.p[t]
        if s > 75 + 1e-6: ok = False
    return cost, ok

if __name__ == '__main__':
    rng = random.Random(7); mx = 0.0; bad = 0
    for n in range(25):
        L = 0.25 if n % 2 else 1.0
        ser, ts = (P.total, P.times) if L == 0.25 else P.hourly(P.total)
        inst = make(rng, ser, ts, L, taper)
        ref = dp_energy_fast(inst, 0.25)
        S, W, tops = F.precompute(0.25, 75.0, [L], taper, 11.0, 1.0, 0.0)
        slots, ev = convert(inst)
        c, en = F.plan(slots, ev, inst.s0, False, 0.25, S, W, tops)
        rc, ok = resim(inst, en, 0.25)
        mx = max(mx, abs(c - ref)); bad += (not ok) or abs(rc - c) > 1e-6
    print("max |fulldp - dp_energy_fast| over 25 real weeks: %.2e; backtrack mismatches: %d" % (mx, bad))

    def bench(f, r=3):
        b = 1e9
        for _ in range(r):
            t0 = time.perf_counter(); f(); b = min(b, time.perf_counter() - t0)
        return b * 1000

    # timing: 672 x 15 min and 168 x 1 h, every term switched on
    def aux_case(L):
        rng = random.Random(3)
        ser, ts = (P.total, P.times) if L == 0.25 else P.hourly(P.total)
        inst = make(rng, ser, ts, L, taper)
        return inst
    print("T     L     g    S   plain(ms)  full(ms)  [full = ramp first slot, eff 0.9 + 0.3 kW aux, start 0.2 kWh, eps tie-break, wear above 45 kWh, soft floors, terminal value, backtrack]")
    for L in (1.0, 0.25):
        inst = aux_case(L)
        slots, ev = convert(inst)
        ev2 = {k: list(v) for k, v in ev.items()}
        for x in inst.tg:  # add a soft expected-use floor 12 h after every target
            ev2.setdefault(min(inst.T - 1, x["d"] + int(12 / L)), []).append(("soft", 40.0, 2.0))
        for g in (1.0, 0.5, 0.25):
            S, W, tops = F.precompute(g, 75.0, [L], taper, 11.0, 1.0, 0.0)
            tp = bench(lambda: F.plan(slots, ev, inst.s0, False, g, S, W, tops))
            S2, W2, tops2 = F.precompute(g, 75.0, [L], taper, 11.0, 0.9, 0.3, ramp=(5, 3.3))
            term = [min(b * g, 20.0) * 1.0 for b in range(S2 + 1)]
            tf = bench(lambda: F.plan(slots, ev2, inst.s0, True, g, S2, W2, tops2, start_kwh=0.2, eps=1e-7,
                                      wear=(45.0, 0.001), terminal=term))
            tpre = bench(lambda: F.precompute(g, 75.0, [L], taper, 11.0, 0.9, 0.3, ramp=(5, 3.3)))
            print("%-5d %-5.2f %-4.2f %-4d %8.1f %9.1f   (precompute %.1f ms)" % (inst.T, L, g, S, tp, tf, tpre))
