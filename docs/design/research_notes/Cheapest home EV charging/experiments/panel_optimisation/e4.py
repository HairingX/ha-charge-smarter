"""E4: plan churn under rolling re-planning. Nights 17:00 -> 07:00, DK1 total quarter prices,
re-plan every 15 min. Truth: delivered energy = planned x U(0.90, 1.00); the engine sees SoC
rounded down to whole % of 75 kWh. Floor 45 kWh at 07:00 (buffer folded in), start 22-35 kWh.
Counts executed session starts per night and cost, vs the starts in the first plan alone."""
import random, statistics as st
import prices as P, fulldp as F
def taper(s): return 11.0 if s < 60 else (7.0 if s < 67.5 else 3.5)
g = 0.25
S, W, tops = F.precompute(g, 75.0, [0.25], taper, 11.0, 1.0, 0.0)
starts17 = [i for i, t in enumerate(P.times) if t.hour == 17 and t.minute == 0 and i + 60 < len(P.times)]
def night(i0, s0, floor, start_kwh, eps, rng, use_on):
    true = s0; on = False; starts = 0; cost = 0.0; first_plan_starts = None
    for k in range(56):
        seen = int(true / 0.75) * 0.75
        T = 56 - k
        slots = [(0.25, P.total[i0 + k + j], True, 75.0) for j in range(T)] + [(0.25, 0.0, False, 75.0)]
        ev = {T: [("hard", floor, None)]}
        c, en = F.plan(slots, ev, min(seen, 75.0), on and use_on, g, S, W, tops, start_kwh=start_kwh, eps=eps)
        if en is None: en = [11 * 0.25] * T  # infeasible: charge
        if first_plan_starts is None:
            first_plan_starts = sum(1 for j in range(T) if en[j] > 0 and (j == 0 or en[j - 1] == 0))
        e = en[0]
        if e > 0:
            d = e * rng.uniform(0.90, 1.00)
            true += d; cost += d * P.total[i0 + k]
            if not on: starts += 1
            on = True
        else:
            on = False
    return starts, first_plan_starts, cost, true >= floor - 1e-9
for label, sk, eps, use_on in (("no start cost, no tie-break", 0.0, 0.0, False),
                               ("tie-break later only", 0.0, 1e-6, False),
                               ("start cost 0.3 kWh + on-state", 0.3, 1e-6, True),
                               ("start cost 1.0 kWh + on-state", 1.0, 1e-6, True)):
    rng = random.Random(5); R = random.Random(9)
    S_, F_, C_, OK = [], [], [], 0
    for n in range(120):
        i0 = R.choice(starts17); s0 = R.uniform(22, 35)
        s, f, c, ok = night(i0, s0, 45.0, sk, eps, rng, use_on)
        S_.append(s); F_.append(f); C_.append(c); OK += ok
    print("%-32s starts/night executed mean %.2f (max %d) | in first plan mean %.2f | mean cost %.3f DKK | floor met %d/120" % (
        label, st.mean(S_), max(S_), st.mean(F_), st.mean(C_), OK), flush=True)
