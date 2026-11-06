"""Ways to use a biased forecast, compared on the elpriser.org archive.

Usage: python methods.py <data folder> [area ...]
Each decision day D is the moment after the day-ahead auction (about 13:00 CET): prices are known
through D+1, and the run issued on D forecasts D+2.. Only information available at that moment
is used (errors of earlier runs on days up to D+1). Every method turns the run into an expected
spot price per hour; the total price (tariffs, Energinet, elafgift, VAT) is added afterwards.

Methods (spot, DKK/MWh; f = forecast median of run D, y = actual):
  raw         f
  a+m         f + m (m given on the total price, DKK/kWh incl. VAT)
  b_mean      f - mean error at the same horizon over the last 14 realised target days
  b_lin       a + b f, least squares on the last 14 realised target days, all horizons
  c_shift     f + delta, delta = actual mean of D+1 - run(D-1)'s forecast mean of D+1
  c_decay     f + w_k delta, w = 1, .75, .5, .25, 0, 0 for D+2..D+7 ("c_decay+1/0.5" sets w)
  c_same      run(D-1) + delta: the anchoring run itself, shifted
  c_scale     f x (actual mean D+1 / run(D-1) mean D+1)
  d_day       actual mean of D+1 + (f - mean of f that day): within-day shape only
  d_horizon   actual mean of D+1 + (f - mean of f over D+2..D+7): shape and trend, known level
  d_cont      actual mean of D+1 + (f - mean of f on D+2): trend kept, D+2 continues D+1's level
  e_qmap      rank of f within D+2..D+7 mapped onto the distribution of the known hours D, D+1
  persist     actual of D+1, same hour
Evaluations: level error; ranking inside the forecast horizon; the charge-now-or-wait choice of
the 4 cheapest hours before a deadline; and a rolling replanning simulation (linear program).
"""
import datetime as dt
import statistics as st
import sys
from collections import defaultdict

import numpy as np
from scipy.optimize import linprog

from common import VAT, day_hours, load_actual, load_runs, spearman, total

H = range(24)
ONE = dt.timedelta(1)
KMAX = 7


def fmean(fc, d):
    v = day_hours({k: v[0] for k, v in fc.items()}, d)
    return st.mean(v) if v else None


def realised(runs, A, D, window=14):
    """(k, f, y) pairs of runs issued before D for target days in (D+1-window, D+1]."""
    out = []
    for iss, fc in runs.items():
        if iss >= D:
            continue
        for (d, h), (f, _, _) in fc.items():
            if D + ONE - dt.timedelta(window) < d <= D + ONE and (d, h) in A:
                out.append(((d - iss).days, f, A[(d, h)]))
    return out


def expected(method, D, runs, A, area):
    """{(date, hour): expected spot} for D+2..D+KMAX, or None when the method lacks data."""
    fc = runs.get(D)
    if fc is None:
        return None
    hours = [(D + dt.timedelta(k), h) for k in range(2, KMAX + 1) for h in H]
    if any(x not in fc for x in hours):
        return None
    f = {x: fc[x][0] for x in hours}
    k_of = {x: (x[0] - D).days for x in hours}
    known_d1 = day_hours(A, D + ONE)
    prev = runs.get(D - ONE)
    anchor = None
    if prev is not None and known_d1 and fmean(prev, D + ONE) is not None:
        anchor = (st.mean(known_d1), fmean(prev, D + ONE))
    name, _, arg = method.partition("+")
    if name == "raw":
        return f
    if name == "a":
        m = float(arg) / VAT * 1000
        return {x: v + m for x, v in f.items()}
    if name == "b_mean":
        r = realised(runs, A, D)
        byk = defaultdict(list)
        for k, ff, y in r:
            byk[k].append(ff - y)
        return {x: v - (st.mean(byk[k_of[x]]) if byk[k_of[x]] else 0.0) for x, v in f.items()}
    if name == "b_lin":
        r = realised(runs, A, D)
        if len(r) < 48:
            return f
        X = np.array([ff for _, ff, _ in r])
        Y = np.array([y for *_, y in r])
        b, a = np.polyfit(X, Y, 1)
        return {x: a + b * v for x, v in f.items()}
    if name in ("c_shift", "c_decay", "c_same", "c_scale"):
        if anchor is None:
            return None
        delta = anchor[0] - anchor[1]
        if name == "c_shift":
            return {x: v + delta for x, v in f.items()}
        if name == "c_decay":
            ws = [float(v) for v in arg.split("/")] if arg else [1, .75, .5, .25]
            w = {k + 2: v for k, v in enumerate(ws)}
            return {x: v + w.get(k_of[x], 0) * delta for x, v in f.items()}
        if name == "c_same":
            if any(x not in prev for x in hours):
                return None
            return {x: prev[x][0] + delta for x in hours}
        ratio = anchor[0] / anchor[1] if anchor[1] > 50 else 1.0
        return {x: v * ratio for x, v in f.items()}
    if name in ("d_day", "d_horizon", "d_cont", "persist", "e_qmap"):
        if not known_d1:
            return None
        lvl = st.mean(known_d1)
        if name == "persist":
            return {x: known_d1[x[1]] for x in hours}
        if name == "d_day":
            dm = {d: st.mean(f[(d, h)] for h in H) for d in {x[0] for x in hours}}
            return {x: lvl + v - dm[x[0]] for x, v in f.items()}
        if name == "d_cont":
            m = st.mean(f[(D + 2 * ONE, h)] for h in H)
            return {x: lvl + v - m for x, v in f.items()}
        if name == "d_horizon":
            m = st.mean(f.values())
            return {x: lvl + v - m for x, v in f.items()}
        ref = sorted((day_hours(A, D) or []) + known_d1)
        order = sorted(hours, key=lambda x: f[x])
        return {x: ref[int(i * (len(ref) - 1) / (len(order) - 1))] for i, x in enumerate(order)}
    raise ValueError(method)


METHODS = ["raw", "a+0.05", "a+0.1", "a+0.2", "a+0.3", "a+0.4", "b_mean", "b_lin", "c_shift", "c_decay",
           "c_same", "c_scale", "d_day", "d_horizon", "d_cont", "e_qmap", "persist"]


def evaluate(folder, area):
    A = load_actual(folder)[area]
    runs = load_runs(folder, area)
    decisions = sorted(D for D in runs if D - ONE in runs)
    print(f"===== {area}: decision days {decisions[0]}..{decisions[-1]} ({len(decisions)})")
    T = lambda x, s: total(area, x[1], s)  # noqa: E731

    print(" -- level: bias and MAE of the expected spot price, DKK/MWh, D+2..D+7, all hours with an actual")
    print("    method      n   bias   MAE | D+2 bias/MAE | D+5 bias/MAE")
    for m in METHODS:
        e = defaultdict(list)
        for D in decisions:
            E = expected(m, D, runs, A, area)
            if E is None:
                continue
            for x, v in E.items():
                if x in A:
                    e[(x[0] - D).days].append(v - A[x])
        allv = [v for k in e for v in e[k]]
        if not allv:
            continue
        s = lambda k: f"{st.mean(e[k]):+5.0f}/{st.mean(abs(v) for v in e[k]):4.0f}" if e[k] else "   -"  # noqa: E731
        print(f"    {m:9s} {len(allv):5d} {st.mean(allv):+6.0f} {st.mean(abs(v) for v in allv):5.0f} | {s(2)} | {s(5)}")

    print(" -- ranking inside D+2..D+7 (decisions whose six days are all settled), total price:")
    print("    method     n  hourSpearman daySpearman cheapestDay  regret4h(DKK/kWh) | day = mean of its 4 cheapest hours")
    for m in METHODS:
        rs, ds, hit, reg = [], [], [], []
        for D in decisions:
            E = expected(m, D, runs, A, area)
            if E is None or any(x not in A for x in E):
                continue
            xs = sorted(E)
            et = [T(x, E[x]) for x in xs]
            yt = [T(x, A[x]) for x in xs]
            rs.append(spearman(et, yt))
            days = sorted({x[0] for x in xs})
            de = [st.mean(sorted(T((d, h), E[(d, h)]) for h in H)[:4]) for d in days]
            dy = [st.mean(sorted(T((d, h), A[(d, h)]) for h in H)[:4]) for d in days]
            ds.append(spearman(de, dy))
            hit.append(int(np.argmin(de)) == int(np.argmin(dy)))
            pick = sorted(range(len(xs)), key=lambda i: et[i])[:4]
            reg.append(st.mean(yt[i] for i in pick) - st.mean(sorted(yt)[:4]))
        if rs:
            print(f"    {m:9s} {len(rs):3d}  {st.mean(rs):.2f}        {st.mean(ds):.2f}        {100*st.mean(hit):3.0f}%       {st.mean(reg):.3f}")

    for horizon in (3, 5):
        print(f" -- charge now or wait: 4 cheapest hours before the end of D+{horizon}; known D 14:00..D+1 23:00, "
              "forecast after. Regret vs perfect foresight, total DKK/kWh; wait = share choosing any forecast hour")
        known_only = None
        for m in ["known_only"] + METHODS:
            reg, wait, waitgood = [], [], []
            for D in decisions:
                kh = [(D, h) for h in range(14, 24)] + [(D + ONE, h) for h in H]
                fh = [(D + dt.timedelta(k), h) for k in range(2, horizon + 1) for h in H]
                if any(x not in A for x in kh + fh):
                    continue
                if m == "known_only":
                    price = {x: T(x, A[x]) for x in kh}
                else:
                    E = expected(m, D, runs, A, area)
                    if E is None:
                        continue
                    price = {x: T(x, A[x]) for x in kh}
                    price.update({x: T(x, E[x]) for x in fh})
                pick = sorted(price, key=price.get)[:4]
                act = sorted(T(x, A[x]) for x in kh + fh)
                cost = st.mean(T(x, A[x]) for x in pick)
                reg.append(cost - st.mean(act[:4]))
                w = any(x in fh for x in pick)
                wait.append(w)
                if w:
                    best_known = st.mean(sorted(T(x, A[x]) for x in kh)[:4])
                    waitgood.append(cost < best_known)
            if not reg:
                continue
            if m == "known_only":
                known_only = st.mean(reg)
            gain = known_only - st.mean(reg)
            wg = f"{100*st.mean(waitgood):3.0f}%" if waitgood else "  - "
            print(f"    {m:10s} n={len(reg):2d} regret {st.mean(reg):.3f} (median {st.median(reg):.3f}, max {max(reg):.3f})"
                  f"  gain vs known-only {gain:+.3f}  wait {100*st.mean(wait):3.0f}%  waits that paid {wg}")
    simulate(A, runs, area, decisions)


def solve(price, plugged, deps, s0, cap, pmax):
    """Cheapest charging per hour meeting each departure's energy and the battery cap (LP)."""
    n = len(price)
    idx = [i for i in range(n) if plugged[i]]
    if not idx:
        return [0.0] * n
    c = np.array([price[i] for i in idx])
    A_ub, b_ub = [], []
    for t, need in deps:  # stock before departure at hour t must cover the cumulative use
        A_ub.append([-1.0 if i < t else 0.0 for i in idx])
        b_ub.append(s0 - need)
    used = [0.0] * n
    for t, need in deps:
        for i in range(t, n):
            used[i] = need
    for t in idx:
        A_ub.append([1.0 if i <= t else 0.0 for i in idx])
        b_ub.append(cap - s0 + used[t])
    r = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub), bounds=[(0, pmax)] * len(idx), method="highs")
    x = [0.0] * n
    if r.status != 0:
        return None
    for j, i in enumerate(idx):
        x[i] = float(r.x[j])
    return x


def simulate(A, runs, area, decisions, use=10.0, pmax=11.0):
    """Daily replanning at 14:00; the car is away 07-17 and uses `use` kWh per day at 07:00."""
    T = lambda x, s: total(area, x[1], s)  # noqa: E731
    D0, D1 = decisions[0], decisions[-1]
    for cap in (30.0, 50.0):
        for basis in ("total", "spot"):
            P = (lambda x, s: T(x, s)) if basis == "total" else (lambda x, s: s / 1000)
            res = {}
            for m in ["oracle", "known_only"] + METHODS:
                stock, cost, energy, ok = 20.0, 0.0, 0.0, True
                for D in decisions:
                    end = D + dt.timedelta(KMAX if m not in ("known_only",) else 1)
                    if m == "oracle":
                        end = min(D1 + ONE, D + dt.timedelta(KMAX))
                    hours = [(D, h) for h in range(14, 24)]
                    d = D + ONE
                    while d <= end:
                        hours += [(d, h) for h in H]
                        d += ONE
                    E = None if m in ("oracle", "known_only") else expected(m, D, runs, A, area)
                    if m not in ("oracle", "known_only") and E is None:
                        ok = False
                        break
                    price = []
                    for x in hours:
                        if x[0] <= D + ONE or m == "oracle":
                            price.append(P(x, A[x]) if x in A else None)
                        else:
                            price.append(P(x, E[x]) if x in E else None)
                    keep = [i for i, p in enumerate(price) if p is not None]
                    hours = [hours[i] for i in keep]
                    price = [price[i] for i in keep]
                    plugged = [not (7 <= x[1] < 17) for x in hours]
                    deps, k = [], 0
                    for i, x in enumerate(hours):
                        if x[1] == 7:
                            k += 1
                            deps.append((i, k * use))
                    x = solve(price, plugged, deps, stock, cap, pmax)
                    if x is None:
                        ok = False
                        break
                    for i, xx in enumerate(hours):
                        if xx[0] == D or (xx[0] == D + ONE and xx[1] < 14):
                            if xx[1] == 7:
                                stock -= use
                            stock += x[i]
                            cost += x[i] * P(xx, A[xx])
                            energy += x[i]
                if ok:
                    res[m] = (cost, energy, stock)
            # leftover stock is valued at the period's mean night (00-06) price
            night = st.mean(P((d, h), A[(d, h)]) for (d, h) in A if D0 <= d <= D1 + ONE and h < 6)
            used = use * len(decisions)
            per = {m: (c - (s - 20.0) * night) / used for m, (c, e, s) in res.items()}
            o, k = per["oracle"], per["known_only"]
            print(f" -- rolling replanning, {basis} price, battery headroom {cap:.0f} kWh, {use:.0f} kWh/day, "
                  f"{len(decisions)} days: DKK/kWh used, share of the oracle's saving over known-only")
            print("    " + "  ".join(f"{m} {v:.3f} ({100*(k-v)/(k-o) if k != o else 0:.0f}%)" for m, v in per.items()))


if __name__ == "__main__":
    folder = sys.argv[1]
    for area in sys.argv[2:] or ["DK1", "DK2"]:
        evaluate(folder, area)
