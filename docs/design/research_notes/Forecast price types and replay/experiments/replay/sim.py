"""Rolling replay of one EV at home: the car, its trips, the planners and the bookkeeping.

The replay re-plans at every hour boundary and at every plug-in, with only what the integration
would know then: published prices up to the end of the last published day, the newest forecast
run already issued, trips already announced, and consumption already observed. The first part
of each plan is executed (late start inside a partly used slot, N4), then the clock moves on.
"""
import datetime as dt
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "Cheapest home EV charging", "experiments",
                                "panel_optimisation"))
import fulldp as F  # noqa: E402
import data as D    # noqa: E402

INF = float("inf")


class Car:
    """Usable capacity, wall power with optional taper, constant efficiency."""

    def __init__(self, cap=77.0, wall_kw=11.0, eff=0.9, taper=None):
        self.cap, self.wall_kw, self.eff, self.taper = cap, wall_kw, eff, taper

    def wall(self, s):
        if self.taper and s >= self.taper[0] * self.cap:
            return min(self.wall_kw, self.taper[1])
        return self.wall_kw

    def batt(self, s):
        return self.eff * self.wall(s)


class Params:
    def __init__(self, **kw):
        self.target = 0.80      # default_target_soc, used by P0 and P1
        self.arrival = 0.20     # default_arrival_soc
        self.safety = 0.15      # min_safety_soc
        self.idle = 0.40        # min_idle_soc, a floor at every departure (N13)
        self.buffer = 20        # completion buffer, minutes
        self.ceiling = 0.60     # surplus_max_soc for soft stock (N11)
        self.markup = 0.08      # additive DKK/kWh on forecast slots: a number or [(lead_h, amount)]
        self.pub_hour = 13      # local hour at which tomorrow's prices become known
        self.pub_skip = set()   # dates D whose D+1 prices are only known at 00:00 of D+1 (stress)
        self.grid = 0.25
        self.soft_pen = 10.0
        self.start_kwh = 0.0
        self.__dict__.update(kw)


# ---------------------------------------------------------------- schedules

class Trip:
    __slots__ = ("dep", "ret", "energy", "kind", "announce")

    def __init__(self, dep, ret, energy, kind, announce):
        self.dep, self.ret, self.energy, self.kind, self.announce = dep, ret, energy, kind, announce


def at(d, h, m=0):
    return D.minute_of(dt.datetime(d.year, d.month, d.day, h, m, tzinfo=D.TZ))


def schedule(kind, start_date, end_date, seed):
    """kind 1: weekday commute; 2: commute plus one long weekend trip a week; 3: irregular."""
    rnd = random.Random(seed)
    trips = []
    d = start_date - dt.timedelta(days=30)
    last_ret = -10 ** 9
    week_long = {}
    while d <= end_date + dt.timedelta(days=15):
        wd = d.weekday()
        if kind in (1, 2) and wd < 5:
            trips.append(Trip(at(d, 7, 30), at(d, 16, 30), rnd.uniform(15, 25), "commute", -10 ** 9))
        if kind == 2 and wd == 5:
            day = d + dt.timedelta(days=rnd.choice((0, 1)))
            dep = at(day, 9)
            trips.append(Trip(dep, at(day, 19), rnd.uniform(50, 60), "long", dep - 5 * 1440))
        if kind == 3 and rnd.random() < 0.6:
            dep = at(d, 6) + 15 * rnd.randrange(0, 57)
            dur = 15 * rnd.randrange(4, 41)
            if dep >= last_ret + 60:
                trips.append(Trip(dep, dep + dur, rnd.uniform(5, 45), "irregular", dep - 1440))
                last_ret = dep + dur
        d += dt.timedelta(days=1)
    trips.sort(key=lambda t: t.dep)
    return trips


class Caller:
    """What the integration knows about trips and consumption at a given minute."""

    def __init__(self, trips, car, P):
        self.trips, self.car, self.P = trips, car, P

    def commute_estimate(self, t):
        past = [x.energy for x in self.trips if x.kind == "commute" and x.ret <= t][-20:]
        if len(past) < 5:
            return 25.0
        past.sort()
        return past[int(0.9 * (len(past) - 1))]

    def daily_use(self, t):
        e = sum(x.energy for x in self.trips if t - 14 * 1440 <= x.ret <= t)
        return e / 14.0 if any(x.ret <= t for x in self.trips) else 18.0

    def planned_energy(self, trip, t):
        return self.commute_estimate(t) if trip.kind == "commute" else trip.energy

    def floor(self, energy):
        c = self.car.cap
        return min(c, max(self.P.idle * c, self.P.arrival * c + energy))

    def known(self, t, foresight=False):
        return [x for x in self.trips if x.ret > t and (foresight or x.announce <= t)]


# ---------------------------------------------------------------- price information at time t

class Info:
    """Published prices, forecast runs and how a policy turns them into decision prices."""

    def __init__(self, area, runs, billing, P, mode="known", bias=None, quarter_rank=False,
                 tariff_bug=None, hour_bug=None):
        self.A, self.runs, self.billing, self.P, self.mode = area, runs, billing, P, mode
        self.bias = bias              # None, "rolling" (P4) or "anchor" (P5)
        self.quarter_rank = quarter_rank
        self.tariff_bug = tariff_bug  # None, "utc", "position", "frozen"
        self.hour_bug = hour_bug      # None or "first": hourly price = first quarter's
        self.data_end = 15 * area.nq
        self._fc_cache = {}

    def known_end(self, t):
        lt = D.local(t)
        d = lt.date()
        if lt.hour >= self.P.pub_hour and d not in self.P.pub_skip:
            end = D.local_midnight(d + dt.timedelta(days=2))
        else:
            end = D.local_midnight(d + dt.timedelta(days=1))
        return min(end, self.data_end)

    def decision_known(self, q, t):
        """Decision price of a published quarter as the policy composes it."""
        A = self.A
        if self.tariff_bug or self.hour_bug:
            h0 = q - q % 4 if self.billing == "hour" else q
            if self.billing == "hour" and not self.quarter_rank:
                spot = A.spot[h0] if self.hour_bug == "first" else sum(A.spot[h0:h0 + 4]) / 4
            else:
                spot = A.spot[q]
            lt = A.loc[q]
            if self.tariff_bug == "frozen":
                tar = A.tariff_on(lt, D.local(t).date())
            elif self.tariff_bug:
                tar = A.grid_tariff(lt, self.tariff_bug)
            else:
                tar = A.tariff[q]
            return (spot + tar + A.flat[q]) * D.VAT
        if self.quarter_rank or self.billing == "quarter":
            return A.total_q[q]
        return A.total_h[q]

    def run_at(self, t):
        best = None
        for r in self.runs:
            if r[0] <= t:
                best = r
        return best

    def _correction(self, t, run, kend):
        """Additive spot correction for P4 (rolling mean error by lead day) or P5 (anchor)."""
        key = (self.bias, run[3], kend)
        if key in self._fc_cache:
            return self._fc_cache[key]
        A = self.A
        corr = {}
        if self.bias == "rolling":
            errs = {}
            for r in self.runs:
                if r[0] > t:
                    continue
                for m, f in r[2].items():
                    if m + 60 > kend or m < kend - 15 * 1440 or m < 0:
                        continue
                    q = m // 15
                    act = sum(A.spot[q:q + 4]) / 4
                    lead = (m - D.local_midnight(r[1] + dt.timedelta(days=1))) // 1440
                    errs.setdefault(lead, []).append(act - f)
            pooled = [e for v in errs.values() for e in v]
            for lead in range(0, 10):
                v = errs.get(lead, [])
                corr[lead] = (sum(v) / len(v) if len(v) >= 72 else
                              (sum(pooled) / len(pooled) if len(pooled) >= 72 else 0.0))
        elif self.bias == "anchor":
            last_day_start = kend - 1440
            for r in reversed(self.runs):
                hs = [m for m in r[2] if last_day_start <= m < kend]
                if r[0] <= t and len(hs) >= 20:
                    err = sum(sum(A.spot[m // 15:m // 15 + 4]) / 4 - r[2][m] for m in hs) / len(hs)
                    corr = {lead: err for lead in range(10)}
                    break
        self._fc_cache[key] = corr
        return corr

    def markup(self, lead_h):
        m = self.P.markup
        if isinstance(m, (int, float)):
            return m
        v = 0.0
        for h, a in m:
            if lead_h >= h:
                v = a
        return v

    def forecast_prices(self, t, kend):
        """{hour start minute: decision price} for forecast hours beyond kend, or {}."""
        run = self.run_at(t)
        if run is None or self.mode != "forecast":
            return {}
        corr = self._correction(t, run, kend) if self.bias else {}
        rd = D.local_midnight(run[1] + dt.timedelta(days=1))
        out = {}
        for m, f in run[2].items():
            if m < kend:
                continue
            lead_day = (m - rd) // 1440
            spot = f + corr.get(lead_day, 0.0)
            out[m] = self.A.compose(spot, D.local(m)) + self.markup((m - kend) / 60.0)
        return out

    def proxy(self, m, kend):
        """N8: tariff plus a pessimistic spot proxy for unpublished hours."""
        A = self.A
        q0 = (kend - 1440) // 15
        day = A.spot[q0:kend // 15]
        lt = D.local(m)
        hq = q0 + 4 * lt.hour
        same = sum(A.spot[hq:hq + 4]) / 4 if hq + 4 <= kend // 15 else max(day)
        spot = max(same, sum(day) / len(day))
        return A.compose(spot, lt) + 0.10


# ---------------------------------------------------------------- planning problem

def build(t, info, caller, car, P, policy, foresight_end=None):
    """Slots, targets and caps for a plan at minute t."""
    A = info.A
    kend = info.known_end(t) if foresight_end is None else foresight_end
    soft_on = policy.get("soft", False)
    fc = info.forecast_prices(t, kend) if foresight_end is None else {}
    trips = caller.known(t, foresight=foresight_end is not None)
    trips = [x for x in trips if x.dep > t]
    if foresight_end is not None:
        hend = foresight_end
    elif fc:
        hend = max(fc) + 60
    else:
        hend = kend
    hend = min(hend, info.data_end) if foresight_end is not None else hend
    # targets
    targets = []
    first = True
    for x in trips:
        dl = x.dep - P.buffer
        if dl <= t:
            continue
        e_plan = x.energy if foresight_end is not None else caller.planned_energy(x, t)
        # The floor is the caller's, from its own estimate, for every policy; foresight knows the use.
        R = caller.floor(caller.planned_energy(x, x.dep if foresight_end is not None else t))
        hard = first or x.kind != "commute" or not soft_on or foresight_end is not None
        if dl > hend:
            if first and foresight_end is None and policy.get("proxy", True):
                hend = dl          # N8: plan up to the next departure on proxy prices
            elif first and foresight_end is None:
                dl = hend          # no proxy: the deadline is clipped to the published prices
            else:
                break
        targets.append([dl, R, x.energy if foresight_end is not None else e_plan, hard, x])
        first = False
    if not targets and caller.trips and policy.get("idle_target", True) and foresight_end is None:
        lt = D.local(t)
        nd = at(lt.date() + dt.timedelta(days=1 if lt.hour >= 7 else 0), 7)
        targets.append([nd, P.idle * car.cap, 0.0, True, None])
        if nd > hend and policy.get("proxy", True):
            hend = nd
    if soft_on and caller_irregular(caller) and foresight_end is None and fc:
        # expected daily use beyond the announcement horizon, as soft demands at 08:00
        use = caller.daily_use(t)
        d = D.local(t + 1440).date() + dt.timedelta(days=1)
        while at(d, 8) < hend:
            targets.append([at(d, 8), caller.floor(use), use, False, None])
            d += dt.timedelta(days=1)
        targets.sort(key=lambda z: z[0])
    # boundaries
    unavail = [(x.dep - P.buffer, x.ret) for x in trips]
    bset = set()
    step_known = 15 if info.billing == "quarter" or info.quarter_rank else 60
    m = t - t % 60 + 60
    while m < hend:
        bset.add(m)
        m += 60
    m = t - t % 15 + 15
    while step_known == 15 and m < min(kend, hend):
        bset.add(m)
        m += 15
    for a, b in unavail:
        if t < a < hend:
            bset.add(a)
        if t < b < hend:
            bset.add(b)
    for tg in targets:
        if t < tg[0] < hend:
            bset.add(tg[0])
    bounds = [t] + sorted(bset) + [hend, hend + 5]
    slots = []
    for s, e in zip(bounds, bounds[1:]):
        if e <= s:
            continue
        avail = s < hend and not any(a <= s < b for a, b in unavail)
        if s >= hend:
            price, isfc = 0.0, True
        elif s < kend:
            price = info.decision_known(s // 15, t) if foresight_end is None else A.billed(s // 15, info.billing)
            isfc = False
        else:
            hm = s - s % 60
            price = fc.get(hm)
            if price is None:
                price = info.proxy(s, kend)
            isfc = True
        slots.append([s, e, price, avail, isfc])
    starts = [z[0] for z in slots]
    tg_idx = []
    for tg in targets:
        i = _bisect(starts, tg[0])
        tg_idx.append((i, tg[1], tg[2], tg[3]))
    # caps: soft stock below the ceiling, except what the next hard target needs
    caps = []
    ceil = (P.ceiling * car.cap) if policy.get("ceiling", False) else car.cap
    for i in range(len(slots)):
        nxt = next((R for (j, R, E, h) in tg_idx if j > i and h), 0.0)
        caps.append(max(ceil, nxt) if ceil < car.cap else car.cap)
    return slots, tg_idx, caps


def caller_irregular(caller):
    return any(x.kind == "irregular" for x in caller.trips[:5])


def _bisect(a, x):
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


# ---------------------------------------------------------------- planners

def greedy(slots, targets, caps, s0, car):
    """Cheapest first, each slot to the earliest unmet target (D22 with N4's partial slot).

    Capacity per slot is taken at the lowest power the car may draw (conservative under taper).
    """
    T = len(slots)
    if not targets:
        return [0.0] * T
    pmin = min(car.batt(0.0), car.batt(car.cap - 1e-6))
    capa = [(z[1] - z[0]) / 60.0 * pmin if z[3] else 0.0 for z in slots]
    cons = [0.0] * (T + 1)
    for (j, R, E, h) in targets:
        cons[j] += E
    soc_end = [0.0] * T
    s = s0
    for i in range(T):
        s -= cons[i]
        soc_end[i] = s
    e = [0.0] * T

    def before(j):
        return s0 if j == 0 else soc_end[j - 1]

    order = sorted((i for i in range(T) if capa[i] > 0), key=lambda i: (slots[i][2], -i))
    for i in order:
        for (j, R, E, hard) in targets:
            if j <= i:
                continue
            short = R - before(j)
            if short <= 1e-9:
                continue
            head = INF
            for k in range(i, T):
                c = car.cap if hard else caps[k]
                head = min(head, c - soc_end[k])
            x = min(capa[i] - e[i], short, head)
            if x <= 1e-9:
                continue
            e[i] += x
            for k in range(i, T):
                soc_end[k] += x
            if capa[i] - e[i] <= 1e-9:
                break
    return e


_PRE = {}


def dp(slots, targets, caps, s0, car, P, on0=False):
    key = (car.cap, car.wall_kw, car.eff, car.taper, P.grid)
    if key not in _PRE:
        lens = [k / 12.0 for k in range(1, 13)]
        _PRE[key] = F.precompute(P.grid, car.cap, lens, car.wall, car.wall_kw, car.eff, 0.0)
    S, W, tops = _PRE[key]
    T = len(slots)
    fs = []
    for i, z in enumerate(slots):
        L = round((z[1] - z[0]) / 5) / 12.0
        fs.append((L, z[2], z[3], caps[i]))
    ev = {}
    for (j, R, E, hard) in targets:
        if j >= T:
            continue
        lst = ev.setdefault(j, [])
        lst.append(("hard", R, None) if hard else ("soft", R, P.soft_pen))
        lst.append(("cons", E, None))
    s0g = math.floor(s0 / P.grid + 1e-9) * P.grid
    cost, en = F.plan(fs, ev, s0g, on0, P.grid, S, W, tops, start_kwh=P.start_kwh, eps=1e-6)
    if en is None:     # infeasible hard chain: relax hard floors to soft ones
        ev2 = {j: [("soft", v, P.soft_pen * 10) if k == "hard" else (k, v, x) for (k, v, x) in l]
               for j, l in ev.items()}
        cost, en = F.plan(fs, ev2, s0g, on0, P.grid, S, W, tops, start_kwh=P.start_kwh, eps=1e-6)
    return en


# ---------------------------------------------------------------- replay

def period(lt):
    h = lt.hour
    return "low" if h < 6 else ("peak" if 17 <= h < 21 else "high")


def replay(area, runs, sched_kind, seed, policy, start, end, car=None, P=None, billing="hour",
           s_init=0.5):
    """Run one policy over [start, end) local dates; return a dict of metrics."""
    car = car or Car()
    P = P or Params()
    t0, t1 = D.local_midnight(start), D.local_midnight(end)
    trips = schedule(sched_kind, start, end, seed)
    caller = Caller(trips, car, P)
    info = Info(area, runs, billing, P, mode=policy.get("info", "known"), bias=policy.get("bias"),
                quarter_rank=policy.get("quarter_rank", False), tariff_bug=policy.get("tariff_bug"),
                hour_bug=policy.get("hour_bug"))
    kind = policy["kind"]
    soc = s_init * car.cap
    stats = dict(cost=0.0, wall=0.0, batt=0.0, misses=0, short_kwh=0.0, short_min=0.0, deps=0,
                 low_arrivals=0, h55=0.0, h60=0.0, starts=0, plan_ms=[], per_period={},
                 per_month={}, dst_cost=0.0, dst_wall=0.0)
    cps = set(range(t0, t1, 60))
    for x in trips:
        for m in (x.dep, x.ret):
            if t0 <= m < t1:
                cps.add(m)
    if kind == "oracle":
        cps |= set(D.local_midnight(start + dt.timedelta(days=k)) for k in range((end - start).days))
    cps = sorted(cps) + [t1]
    deps = {x.dep: x for x in trips}
    rets = {x.ret: x for x in trips}
    home = True
    for x in trips:
        if x.dep < t0 < x.ret:
            home = False
    plan = {}
    last_on = -10
    dst_days = {dt.date(2025, 10, 26), dt.date(2026, 3, 29), dt.date(2026, 10, 25)}
    oracle_plan_until = -1

    def charge(a, b, x, limit=None):
        """Deliver x battery kWh in [a, b), starting as late as possible (all of it if x is None)."""
        nonlocal soc, last_on
        if b <= a:
            return
        need = car.cap - soc if x is None else x
        if limit is not None:
            need = min(need, max(0.0, limit - soc))
        if need <= 1e-6:
            return
        s, n, mins = soc, need, 0
        while n > 1e-9 and mins < b - a:
            d = min(car.batt(s) / 60.0, n)
            s += d
            n -= d
            mins += 1
        st = a if x is None else b - mins
        for m in range(st, b):
            if need <= 1e-9 or soc >= car.cap - 1e-9:
                break
            d = min(car.batt(soc) / 60.0, need, car.cap - soc)
            if d <= 0:
                break
            if m != last_on + 1:
                stats["starts"] += 1
            last_on = m
            q = m // 15
            w = d / car.eff
            price = area.billed(q, billing)
            stats["cost"] += w * price
            stats["wall"] += w
            stats["batt"] += d
            lt = area.loc[q]
            pk = period(lt)
            pp = stats["per_period"].setdefault(pk, [0.0, 0.0])
            pp[0] += w * price
            pp[1] += w
            mk = lt.strftime("%Y-%m")
            pm = stats["per_month"].setdefault(mk, [0.0, 0.0])
            pm[0] += w * price
            pm[1] += w
            if lt.date() in dst_days or (lt - dt.timedelta(hours=7)).date() in dst_days:
                stats["dst_cost"] += w * price
                stats["dst_wall"] += w
            soc += d
            need -= d

    for a, b in zip(cps, cps[1:]):
        if a in deps:
            x = deps[a]
            R = caller.floor(caller.planned_energy(x, a))
            stats["deps"] += 1
            if soc < R - 0.05:
                if os.environ.get("REPLAY_DEBUG"):
                    print("miss", D.local(a), x.kind, round(R, 1), round(soc, 1))
                stats["misses"] += 1
                stats["short_kwh"] += R - soc
                stats["short_min"] += (R - soc) / car.batt(soc) * 60
            soc -= x.energy
            if soc < P.arrival * car.cap - 1e-6:
                stats["low_arrivals"] += 1
            soc = max(soc, 0.0)
            home = False
        if a in rets:
            home = True
        if home:
            nxt = next((x for x in caller.known(a) if x.dep > a), None)
            if soc < P.safety * car.cap:
                charge(a, b, None, P.safety * car.cap)
            if kind == "now":
                lim = max(P.target * car.cap, caller.floor(caller.planned_energy(nxt, a)) if nxt else 0)
                charge(a, min(b, nxt.dep - P.buffer) if nxt else b, None, lim)
            elif kind == "timer":
                lim = max(P.target * car.cap, caller.floor(caller.planned_energy(nxt, a)) if nxt else 0)
                lt = D.local(a)
                urgent = nxt and nxt.dep - a < 24 * 60 and \
                    D.local(nxt.dep).date() == lt.date() and lt.hour >= 7
                if lt.hour < 7 or urgent:
                    charge(a, min(b, nxt.dep - P.buffer) if nxt else b, None, lim)
            else:
                if kind == "oracle":
                    if a >= oracle_plan_until:
                        hz = min(a + 10 * 1440, info.data_end)
                        slots, tg, caps = build(a, info, caller, car, P, policy, foresight_end=hz)
                        tt = time.perf_counter()
                        en = dp(slots, tg, caps, soc, car, P, on0=(last_on == a - 1))
                        stats["plan_ms"].append((time.perf_counter() - tt) * 1000)
                        plan = {z[0]: (z[1], en[i]) for i, z in enumerate(slots) if en[i] > 1e-9}
                        oracle_plan_until = D.local_midnight(D.local(a).date() + dt.timedelta(days=1))
                else:
                    slots, tg, caps = build(a, info, caller, car, P, policy)
                    tt = time.perf_counter()
                    if kind == "greedy":
                        en = greedy(slots, tg, caps, soc, car)
                    else:
                        en = dp(slots, tg, caps, soc, car, P, on0=(last_on == a - 1))
                    stats["plan_ms"].append((time.perf_counter() - tt) * 1000)
                    plan = {z[0]: (z[1], en[i]) for i, z in enumerate(slots) if en[i] > 1e-9}
                for s in sorted(plan):
                    e, x = plan[s]
                    if s >= a and s < b:
                        charge(s, min(e, b), x if e <= b else x * (min(e, b) - s) / (e - s))
        dur = (b - a) / 60.0
        if soc > 0.55 * car.cap:
            stats["h55"] += dur
        if soc > 0.60 * car.cap:
            stats["h60"] += dur
    stats["soc_end"] = soc
    stats["soc_start"] = s_init * car.cap
    return stats
