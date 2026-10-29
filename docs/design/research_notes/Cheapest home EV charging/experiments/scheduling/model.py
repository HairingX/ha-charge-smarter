"""Experimental model: one car, slots with prices, targets with floors, caps and consumption.

Conventions
- Slot t covers [t*L, (t+1)*L) hours. Target k has deadline slot d: SoC is checked at the
  start of slot d, then consumption c is removed (car leaves). Absence slots are unavailable.
- power(soc_kwh) -> kW (car taper). ramp: (ramp_hours, ramp_kw) power cap at session start.
- Efficiency 1 (it scales every algorithm's cost equally).
"""
import math

SUB = 10  # simulation sub-steps per slot


class Inst:
    def __init__(self, prices, L, avail, s0, targets, power, ramp=None):
        self.p = prices
        self.T = len(prices)
        self.L = L
        self.avail = avail
        self.s0 = s0
        # targets: list of dict(d, own, cap, cons), sorted by d
        self.tg = sorted(targets, key=lambda x: x["d"])
        self.power = power
        self.ramp = ramp
        # cap that applies to a slot = cap of the next target (or last cap after the last one)
        self.cap_at = []
        k = 0
        for t in range(self.T):
            while k < len(self.tg) and self.tg[k]["d"] <= t:
                k += 1
            self.cap_at.append(self.tg[k]["cap"] if k < len(self.tg) else self.tg[-1]["cap"])
        self.deadline_at = {x["d"]: i for i, x in enumerate(self.tg)}


def charge(inst, soc, hours, limit, age):
    """Charge for `hours` from `soc`, never above `limit`; `age` = hours into session.

    Returns (energy, new_soc, new_age)."""
    if hours <= 0 or soc >= limit:
        return 0.0, soc, age
    n = max(1, int(round(SUB * hours / inst.L)))
    h = hours / n
    e0 = soc
    for _ in range(n):
        kw = inst.power(soc)
        if inst.ramp is not None and age < inst.ramp[0]:
            kw = min(kw, inst.ramp[1])
        soc = min(limit, soc + kw * h)
        age += h
        if soc >= limit:
            break
    return soc - e0, soc, age


def simulate(inst, frac, stop=None):
    """frac: dict slot -> fraction of the slot charged (charging at the slot's start).

    stop: optional list, per slot, of a SoC level the charge stops at (a charge limit).
    Returns (cost, soc_at_targets list, ok)."""
    soc = inst.s0
    cost = 0.0
    at = [None] * len(inst.tg)
    ok = True
    age = 0.0
    prev = False
    for t in range(inst.T):
        k = inst.deadline_at.get(t)
        if k is not None:
            at[k] = soc
            if soc < inst.tg[k]["own"] - 1e-6:
                ok = False
            soc -= inst.tg[k]["cons"]
            if soc < -1e-9:
                ok = False
            prev = False
        f = frac.get(t, 0.0)
        if f > 0 and inst.avail[t]:
            lim = inst.cap_at[t] if stop is None else min(inst.cap_at[t], stop[t])
            if not prev:
                age = 0.0
            e, soc, age = charge(inst, soc, f * inst.L, lim, age)
            cost += e * inst.p[t]
            prev = e > 0 and f >= 1.0
            if e <= 0:
                prev = False
        else:
            prev = False
    return cost, at, ok


def pass1_floors(inst):
    """D22 pass 1: floor per target; a later need is pushed earlier when the available hours
    between the two targets cannot deliver it (simulated with the taper, no session ramp)."""
    K = len(inst.tg)
    req = [0.0] * K
    for k in range(K - 1, -1, -1):
        own = min(inst.tg[k]["own"], inst.tg[k]["cap"])
        if k == K - 1:
            req[k] = own
            continue
        d0, d1 = inst.tg[k]["d"], inst.tg[k + 1]["d"]
        hours = sum(inst.L for t in range(d0, d1) if inst.avail[t])
        lim = inst.cap_at[d0]

        def reaches(r):
            s = r - inst.tg[k]["cons"]
            if s < 0:
                return False
            _, s_end, _ = charge(inst, s, hours, lim, 1e9)
            return s_end >= req[k + 1] - 1e-9

        if reaches(own):
            req[k] = own
            continue
        lo, hi = own, inst.tg[k]["cap"]
        if not reaches(hi):
            req[k] = hi
            continue
        for _ in range(40):
            mid = (lo + hi) / 2
            if reaches(mid):
                hi = mid
            else:
                lo = mid
        req[k] = hi
    return req


def stop_levels(inst, req):
    """Charge limit per slot: the floor of the next target (the plan's SET_CHARGE_LIMIT)."""
    out = []
    k = 0
    for t in range(inst.T):
        while k < len(inst.tg) and inst.tg[k]["d"] <= t:
            k += 1
        out.append(req[k] if k < len(req) else 0.0)
    return out


def greedy_d22(inst, trim="price", incremental=False):
    """Pass 2 of D22: cheapest available slot first, given (whole) to the earliest target
    still short whose deadline it precedes; the plan is energy per slot, not charge limits.

    incremental=False: 'short' = simulated SoC at the target below its floor (D22 as written).
    incremental=True: 'short' = energy assigned to the target below its own increment over
    the previous floor (unit-job / matroid greedy with earliest-deadline matching).
    trim: 'price' shrinks the most expensive selected slots first while floors hold;
    'chrono' shrinks the latest slots first (charging in time order until the floor is met)."""
    req = pass1_floors(inst)
    need = []
    prev_after = inst.s0
    for k, tg in enumerate(inst.tg):
        need.append(max(0.0, req[k] - prev_after))
        prev_after = max(req[k], prev_after) - tg["cons"]
    slots = sorted((t for t in range(inst.T) if inst.avail[t]), key=lambda t: (inst.p[t], -t))
    sel = {}
    got = [0.0] * len(inst.tg)
    for t in slots:
        _, at, _ = simulate(inst, sel)
        if incremental:
            short = [k for k in range(len(inst.tg)) if got[k] < need[k] - 1e-6]
        else:
            short = [k for k in range(len(inst.tg)) if at[k] < req[k] - 1e-6]
        if not short:
            break
        for k in short:
            if inst.tg[k]["d"] <= t:
                continue
            sel2 = dict(sel)
            sel2[t] = 1.0
            _, at1, _ = simulate(inst, sel2)
            gain = at1[k] - at[k]
            if gain > 1e-9:
                sel = sel2
                got[k] += gain
                break
    sel = trim_slots(inst, sel, req, trim)
    cost, at, ok = simulate(inst, sel)
    ok = ok and all(at[k] >= req[k] - 1e-6 for k in range(len(req)))
    return cost, ok, sel


def feasible_floors(inst, frac, req):
    _, at, ok = simulate(inst, frac)
    return all(at[k] >= req[k] - 1e-6 for k in range(len(req))) and ok


def trim_slots(inst, sel, req, order):
    """Reverse delete: shrink selected slots (most expensive or latest first) while floors hold."""
    sel = dict(sel)
    keyf = (lambda t: (-inst.p[t], t)) if order == "price" else (lambda t: -t)
    for t in sorted(sel, key=keyf):
        sel[t] = 0.0
        if feasible_floors(inst, sel, req):
            del sel[t]
            continue
        lo, hi = 0.0, 1.0
        for _ in range(30):
            mid = (lo + hi) / 2
            sel[t] = mid
            if feasible_floors(inst, sel, req):
                hi = mid
            else:
                lo = mid
        sel[t] = hi
    return sel


def dp_exact(inst, grid=0.01, fsteps=20):
    """DP over (slot, SoC on a grid, charging continued from the previous slot).

    Each slot chooses a fraction in {0, 1/fsteps, ..., 1}. Exact up to the grid and fractions."""
    def key(s):
        return int(round(s / grid))

    states = {(key(inst.s0), False): (0.0, inst.s0)}
    fr = [i / fsteps for i in range(fsteps + 1)]
    for t in range(inst.T):
        k = inst.deadline_at.get(t)
        if k is not None:
            ns = {}
            for (sk, pv), (c, s) in states.items():
                if s < inst.tg[k]["own"] - 1e-6:
                    continue
                s2 = s - inst.tg[k]["cons"]
                if s2 < -1e-9:
                    continue
                kk = (key(s2), False)
                if kk not in ns or ns[kk][0] > c:
                    ns[kk] = (c, s2)
            states = ns
        ns = {}
        choices = fr if inst.avail[t] else [0.0]
        for (sk, pv), (c, s) in states.items():
            for f in choices:
                if f == 0:
                    e, s2, cont = 0.0, s, False
                else:
                    age = (inst.ramp[0] + 1) if (inst.ramp and pv) else 0.0
                    e, s2, _ = charge(inst, s, f * inst.L, inst.cap_at[t], age)
                    cont = bool(inst.ramp) and f >= 1.0 and e > 0
                kk = (key(s2), cont)
                c2 = c + e * inst.p[t]
                if kk not in ns or ns[kk][0] > c2:
                    ns[kk] = (c2, s2)
        states = ns
    if not states:
        return math.inf
    return min(c for c, _ in states.values())


def dp_energy(inst, g=0.25):
    """Exact DP for energies on a grid g (all data assumed on the grid, no session ramp).

    State: SoC in units of g. Slot t may add any multiple of g up to what one slot delivers
    from that SoC (taper), never above the slot's cap."""
    import math as _m
    T = inst.T
    smax = int(round(max(x["cap"] for x in inst.tg) / g))
    emax = []
    for b in range(smax + 1):
        _, s2, _ = charge(inst, b * g, inst.L, smax * g, 1e9)
        emax.append(int(_m.floor((s2 - b * g) / g + 1e-9)))
    INF = float("inf")
    V = [INF] * (smax + 1)
    V[int(round(inst.s0 / g))] = 0.0
    for t in range(T):
        k = inst.deadline_at.get(t)
        if k is not None:
            own = int(_m.ceil(inst.tg[k]["own"] / g - 1e-9))
            cons = int(round(inst.tg[k]["cons"] / g))
            W = [INF] * (smax + 1)
            for b in range(own, smax + 1):
                if V[b] < INF and b - cons >= 0:
                    W[b - cons] = min(W[b - cons], V[b])
            V = W
        if not inst.avail[t]:
            continue
        cap = int(round(inst.cap_at[t] / g))
        pg = inst.p[t] * g
        W = V[:]
        for b in range(smax + 1):
            v = V[b]
            if v == INF:
                continue
            top = min(cap, b + emax[b])
            c = v
            for nb in range(b + 1, top + 1):
                c += pg
                if c < W[nb]:
                    W[nb] = c
        V = W
    return min(V)


def dp_energy_fast(inst, g=0.25, start_penalty=0.0):
    """dp_energy in O(T * S): within a slot the cost is linear in energy, so the best
    predecessor of each SoC is a sliding-window minimum of V[b] - p*g*b (monotone deque).
    Requires b + emax[b] to be non-decreasing in b (true for a physical taper).
    start_penalty > 0 adds a second state (charging in the previous slot) and charges a
    fixed cost for every session start (a soft minimum-session / anti-chattering term)."""
    from collections import deque
    import math as _m
    smax = int(round(max(x["cap"] for x in inst.tg) / g))
    top = []
    for b in range(smax + 1):
        _, s2, _ = charge(inst, b * g, inst.L, smax * g, 1e9)
        top.append(b + int(_m.floor((s2 - b * g) / g + 1e-9)))
    INF = float("inf")
    n_states = 2 if start_penalty else 1
    V = [[INF] * (smax + 1) for _ in range(n_states)]
    V[0][int(round(inst.s0 / g))] = 0.0
    for t in range(inst.T):
        k = inst.deadline_at.get(t)
        if k is not None:
            own = int(_m.ceil(inst.tg[k]["own"] / g - 1e-9))
            cons = int(round(inst.tg[k]["cons"] / g))
            for f in range(n_states):
                W = [INF] * (smax + 1)
                for b in range(own, smax + 1):
                    if b - cons >= 0 and V[f][b] < W[b - cons]:
                        W[b - cons] = V[f][b]
                V[f] = W
            if n_states == 2:
                V[0] = [min(a, c) for a, c in zip(V[0], V[1])]
                V[1] = [INF] * (smax + 1)
        if not inst.avail[t]:
            if n_states == 2:
                V[0] = [min(a, c) for a, c in zip(V[0], V[1])]
                V[1] = [INF] * (smax + 1)
            continue
        cap = int(round(inst.cap_at[t] / g))
        pg = inst.p[t] * g
        idle = [min(col) for col in zip(*V)] if n_states == 2 else V[0]
        W_on = [INF] * (smax + 1)
        # sources for charging in this slot: from state f, paying the start penalty if f == 0
        srcs = [(V[0], start_penalty)] + ([(V[1], 0.0)] if n_states == 2 else [])
        for Vf, pen in srcs:
            dq = deque()  # indices b with increasing V[b] - pg*b
            b = 0
            for nb in range(smax + 1):
                while b <= nb:
                    if Vf[b] < INF:
                        val = Vf[b] - pg * b
                        while dq and Vf[dq[-1]] - pg * dq[-1] >= val:
                            dq.pop()
                        dq.append(b)
                    b += 1
                while dq and top[dq[0]] < nb:
                    dq.popleft()
                if dq and nb <= cap:
                    b0 = dq[0]
                    if b0 < nb:
                        c = Vf[b0] + pg * (nb - b0) + pen
                        if c < W_on[nb]:
                            W_on[nb] = c
        if n_states == 2:
            V = [idle, W_on]
        else:
            V = [[a if a < c else c for a, c in zip(idle, W_on)]]
    return min(min(v) for v in V)
