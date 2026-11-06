"""Tables from the JSON lines that run.py writes.

    python3 summarise.py RESULTS.jsonl [more.jsonl ...]

Costs are DKK incl. VAT. "adj" values the difference between the start and end SoC at the
perfect-foresight policy's (P7) average price per battery kWh in the same run group, so that
policies ending with more or less energy in the car compare fairly.
"""
import json
import statistics as st
import sys
from collections import defaultdict

rows = []
for f in sys.argv[1:]:
    rows += [json.loads(line) for line in open(f)]

VARIANT_KEYS = ("taper", "replan", "idle", "buffer", "pub")


def variant(r):
    return ",".join("%s=%s" % (k, r[k]) for k in VARIANT_KEYS if k in r) or "base"


def group(r):
    return (r["area"], r["billing"], r["win"], r["sched"], r["seed"], variant(r))


ref = {}
for r in rows:
    if r["pol"] == "P7":
        ref[group(r)] = r["cost"] / r["batt"]
for r in rows:
    g = group(r)
    v = ref.get(g) or ref.get(g[:5] + ("base",))
    if v is None:
        v = r["cost"] / r["batt"]
    r["adj"] = r["cost"] + (r["soc_start"] - r["soc_end"]) * v

by = defaultdict(dict)
for r in rows:
    by[group(r)][r["pol"]] = r


def table(area, billing, win, var, pols, base="P2", refp="P7"):
    print("\n### %s, %s billing, window %s, %s" % (area, billing, win, var))
    for sched in (1, 2, 3):
        gs = [g for g in by if g[0] == area and g[1] == billing and g[2] == win and g[3] == sched and g[5] == var]
        if not gs:
            continue
        n = len(gs)
        print("\nSchedule %d (%d seeds). Adjusted cost; deltas are paired means over seeds (sd); worse = seeds above %s" % (sched, n, base))
        print("| Policy | DKK | DKK/kWh wall | vs %s | worse | vs %s (regret) | misses | short kWh | arr<20%% | h>55%% | h>60%% | starts | plan ms mean/p95/max |" % (base, refp))
        print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for p in pols:
            rs = [by[g][p] for g in gs if p in by[g]]
            if not rs:
                continue
            d_base = [by[g][p]["adj"] - by[g][base]["adj"] for g in gs if p in by[g] and base in by[g]]
            d_ref = [by[g][p]["adj"] - by[g][refp]["adj"] for g in gs if p in by[g] and refp in by[g]]
            m = lambda k: st.mean(r[k] for r in rs)
            sd = lambda v: st.stdev(v) if len(v) > 1 else 0.0
            print("| %s | %.0f | %.3f | %+.1f (%.1f) | %d/%d | %+.1f (%.1f) | %.1f | %.1f | %.1f | %.0f | %.0f | %.1f | %.1f/%.1f/%.1f |" % (
                p, m("adj"), st.mean(r["cost"] / r["wall"] for r in rs),
                st.mean(d_base) if d_base else float("nan"), sd(d_base),
                sum(1 for d in d_base if d > 0.5), len(d_base),
                st.mean(d_ref) if d_ref else float("nan"), sd(d_ref),
                m("misses"), m("short_kwh"), m("low_arrivals"), m("h55"), m("h60"), m("starts"),
                m("plan_mean"), m("plan_p95"), max(r["plan_max"] for r in rs)))


def periods(area, billing, win, var, pols):
    print("\n#### Energy share by tariff period (%s, %s, %s, %s), all schedules and seeds" % (area, billing, win, var))
    print("| Policy | low 00-06 | high | peak 17-21 | DST-day kWh |")
    print("|---|---|---|---|---|")
    for p in pols:
        rs = [by[g][p] for g in by if g[0] == area and g[1] == billing and g[2] == win and g[5] == var and p in by[g]]
        if not rs:
            continue
        tot = sum(r["wall"] for r in rs)
        sh = {k: sum(r["per_period"].get(k, [0, 0])[1] for r in rs) / tot * 100 for k in ("low", "high", "peak")}
        print("| %s | %.1f %% | %.1f %% | %.1f %% | %.1f |" % (p, sh["low"], sh["high"], sh["peak"],
                                                         st.mean(r["dst_wall"] for r in rs)))


if __name__ == "__main__":
    combos = sorted({(g[0], g[1], g[2], g[5]) for g in by})
    for area, billing, win, var in combos:
        pols = sorted({p for g in by if (g[0], g[1], g[2], g[5]) == (area, billing, win, var) for p in by[g]},
                      key=lambda p: (p[:2], p))
        base = "P2" if "P2" in pols else pols[0]
        refp = "P7" if "P7" in pols else base
        table(area, billing, win, var, pols, base, refp)
        periods(area, billing, win, var, pols)
