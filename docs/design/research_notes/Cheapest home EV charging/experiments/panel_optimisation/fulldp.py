"""A full-featured planning DP in standard-library Python, with backtracking.

State: (slot boundary t, SoC on a grid of g kWh, on = charged in the previous slot).
Per available slot of length L, from SoC b the car can reach any nb with b < nb <= top(b),
where top is a full-power simulation over the slot (taper, first-slot ramp when the session
starts, charging overhead). Cost of b -> nb is price * (W[nb] - W[b]), W = cumulative wall
energy at full power, so a partial slot is charged at full power for part of the slot.
A session start pays start_kwh * price (a per-start energy overhead, D3-friendly).
Deadlines: hard floor (V = inf below), soft floor (linear shortfall penalty per kWh), then the
absence's consumption shifts SoC. Caps: nb <= cap of the slot. Wear: hold cost per kWh above a
step per hour. Terminal value: subtracted at the end. Tie-break: price + eps * (T - t) favours
later slots. O(T * S) per on-state source with a monotone queue.
"""
INF = float("inf")


def precompute(g, smax_kwh, slot_lengths, car_kw, charger_kw, eff, aux_kw, ramp=None, sub=10):
    """top[L][first][b] and W[b]. ramp = (minutes, kw) cap at the start of a session."""
    S = int(round(smax_kwh / g))
    # wall energy per battery kWh at SoC s, full power
    def batt_kw(s, wall_cap):
        wall = min(car_kw(s), wall_cap)
        return max(0.0, eff * wall - aux_kw), wall
    W = [0.0] * (S + 1)
    for b in range(S):
        s = (b + 0.5) * g
        bk, wk = batt_kw(s, charger_kw)
        W[b + 1] = W[b] + (g * wk / bk if bk > 0 else 1e9)
    tops = {}
    for L in set(slot_lengths):
        tops[L] = []
        for first in (0, 1):
            top = [0] * (S + 1)
            for b in range(S + 1):
                s = b * g; h = L / sub; age = 0.0
                for _ in range(sub):
                    cap = charger_kw
                    if first and ramp and age < ramp[0] / 60.0:
                        cap = min(cap, ramp[1])
                    bk, _ = batt_kw(s, cap)
                    s = min(smax_kwh, s + bk * h); age += h
                top[b] = min(S, int(s / g + 1e-9))
            for b in range(1, S + 1):          # enforce monotone b + emax(b)
                if top[b] < top[b - 1]: top[b] = top[b - 1]
            tops[L].append(top)
    return S, W, tops


def plan(slots, events, s0_kwh, on0, g, S, W, tops, start_kwh=0.0, eps=0.0,
         wear=None, terminal=None):
    """slots: list of (L, price, available, cap_kwh). events: dict t -> list of
    (kind, value, extra) applied at the start of slot t: ('hard', floor_kwh, None),
    ('soft', floor_kwh, penalty_per_kwh), ('cons', kwh, None).
    wear = (step_kwh, cost_per_kwh_hour). terminal = list of value per state (subtracted).
    Returns (cost, energy per slot in kWh battery)."""
    T = len(slots)
    V0 = [INF] * (S + 1); V1 = [INF] * (S + 1)
    b0 = int(round(s0_kwh / g))
    (V1 if on0 else V0)[b0] = 0.0
    bp = [None] * T
    evsrc = {}
    for t in range(T):
        for kind, val, extra in events.get(t, ()):
            if kind == "hard":
                f = int(-(-val // g))
                for b in range(min(f, S + 1)): V0[b] = INF; V1[b] = INF
            elif kind == "soft":
                f = int(-(-val // g))
                for b in range(min(f, S + 1)):
                    pen = (f - b) * g * extra
                    if V0[b] < INF: V0[b] += pen
                    if V1[b] < INF: V1[b] += pen
            else:
                c = int(round(val / g))
                evsrc[t] = [1 if d < a else 0 for a, d in zip(V0, V1)]
                V0 = [min(a, d) for a, d in zip(V0, V1)]
                V0 = V0[c:] + [INF] * c
                V1 = [INF] * (S + 1)
        L, price, avail, capk = slots[t]
        if not avail:
            src = [1 if d < a else 0 for a, d in zip(V0, V1)]
            V0 = [d if d < a else a for a, d in zip(V0, V1)]
            V1 = [INF] * (S + 1)
            bp[t] = ("idle", src)
        else:
            p = price + eps * (T - t)
            cap = min(S, int(capk / g + 1e-9))
            idle_src = [1 if d < a else 0 for a, d in zip(V0, V1)]
            N0 = [d if d < a else a for a, d in zip(V0, V1)]
            N1 = [INF] * (S + 1); arg = [-1] * (S + 1); asrc = [0] * (S + 1)
            pW = [p * w for w in W]
            sc = start_kwh * p
            for srcflag, Vs, top, add in ((0, V0, tops[L][1], sc), (1, V1, tops[L][0], 0.0)):
                # sliding-window min of Vs[b] - pW[b] over b < nb <= top[b]
                q = []; qh = 0
                lo = 0
                for nb in range(1, cap + 1):
                    b = nb - 1
                    v = Vs[b]
                    if v < INF:
                        val = v - pW[b]
                        while len(q) > qh and Vs[q[-1]] - pW[q[-1]] >= val: q.pop()
                        q.append(b)
                    while len(q) > qh and top[q[qh]] < nb: qh += 1
                    if len(q) > qh:
                        bb = q[qh]
                        c = Vs[bb] - pW[bb] + pW[nb] + add
                        if c < N1[nb]:
                            N1[nb] = c; arg[nb] = bb; asrc[nb] = srcflag
            V0, V1 = N0, N1
            bp[t] = ("slot", idle_src, arg, asrc)
        if wear:
            step, cph = wear
            fs = int(step / g)
            hc = cph * L * g
            for b in range(fs + 1, S + 1):
                k = (b - fs) * hc
                if V0[b] < INF: V0[b] += k
                if V1[b] < INF: V1[b] += k
    # terminal
    best, bs, bo = INF, -1, 0
    for b in range(S + 1):
        tv = terminal[b] if terminal else 0.0
        for o, V in ((0, V0), (1, V1)):
            if V[b] - tv < best: best, bs, bo = V[b] - tv, b, o
    if bs < 0: return INF, None
    # backtrack
    energy = [0.0] * T
    b, o = bs, bo
    for t in range(T - 1, -1, -1):
        rec = bp[t]
        if rec[0] == "idle":
            o = rec[1][b]
        elif o == 1:
            pb = rec[2][b]; energy[t] = (b - pb) * g; o = rec[3][b]; b = pb
        else:
            o = rec[1][b]
        # undo events at slot start: consumption shift (reverse), on-state reset
        for kind, val, extra in reversed(events.get(t, ())):
            if kind == "cons":
                b += int(round(val / g)); o = evsrc[t][b]
    return best, energy
