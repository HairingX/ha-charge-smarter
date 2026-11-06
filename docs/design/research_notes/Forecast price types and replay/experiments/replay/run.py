"""Run a named experiment of the replay in parallel and append one JSON line per run.

    python3 run.py DATA_DIR OUT.jsonl EXPERIMENT [processes]

EXPERIMENT is one of the keys of EXPERIMENTS below.
"""
import datetime as dt
import json
import multiprocessing as mp
import sys
import time

import data as D
import sim as S

FC_WINDOW = (dt.date(2026, 10, 7), dt.date(2026, 11, 7))
YEAR = (dt.date(2025, 11, 7), dt.date(2026, 11, 7))

POL = {
    "P0": dict(kind="now"),
    "P1": dict(kind="timer"),
    "P2": dict(kind="greedy"),
    "P2n": dict(kind="greedy", proxy=False),
    "P3_m0": dict(kind="greedy", info="forecast", soft=True, ceiling=True, markup=0.0),
    "P3_m005": dict(kind="greedy", info="forecast", soft=True, ceiling=True, markup=0.05),
    "P3_m008": dict(kind="greedy", info="forecast", soft=True, ceiling=True, markup=0.08),
    "P3_m010": dict(kind="greedy", info="forecast", soft=True, ceiling=True, markup=0.10),
    "P3_step": dict(kind="greedy", info="forecast", soft=True, ceiling=True, markup=[(0, 0.08), (48, 0.10)]),
    "P3_c55": dict(kind="greedy", info="forecast", soft=True, ceiling=True, markup=0.08, ceil=0.55),
    "P3_noceil": dict(kind="greedy", info="forecast", soft=True, ceiling=False, markup=0.08),
    "P3_noceil_m0": dict(kind="greedy", info="forecast", soft=True, ceiling=False, markup=0.0),
    "P3_noceil_m020": dict(kind="greedy", info="forecast", soft=True, ceiling=False, markup=0.20),
    "P4_noceil": dict(kind="greedy", info="forecast", soft=True, ceiling=False, markup=0.0, bias="rolling"),
    "P5_noceil": dict(kind="greedy", info="forecast", soft=True, ceiling=False, markup=0.0, bias="anchor"),
    "P4_m0": dict(kind="greedy", info="forecast", soft=True, ceiling=True, markup=0.0, bias="rolling"),
    "P4_m008": dict(kind="greedy", info="forecast", soft=True, ceiling=True, markup=0.08, bias="rolling"),
    "P5_m0": dict(kind="greedy", info="forecast", soft=True, ceiling=True, markup=0.0, bias="anchor"),
    "P5_m008": dict(kind="greedy", info="forecast", soft=True, ceiling=True, markup=0.08, bias="anchor"),
    "P6a": dict(kind="dp"),
    "P6b": dict(kind="dp", info="forecast", soft=True, ceiling=True, markup=0.08),
    "P6b_start": dict(kind="dp", info="forecast", soft=True, ceiling=True, markup=0.08, start_kwh=0.3),
    "P6a_start": dict(kind="dp", start_kwh=0.3),
    "P7": dict(kind="oracle"),
    "P7c": dict(kind="oracle", ceiling=True),
    # deliberate composition faults, executed with correct billing
    "P2_tariff_utc": dict(kind="greedy", tariff_bug="utc"),
    "P2_tariff_position": dict(kind="greedy", tariff_bug="position"),
    "P2_tariff_frozen": dict(kind="greedy", tariff_bug="frozen"),
    "P2_rank_quarters": dict(kind="greedy", quarter_rank=True),
    "P2_hour_first_quarter": dict(kind="greedy", hour_bug="first"),
}

MAIN_FC = ["P0", "P1", "P2", "P2n", "P3_m0", "P3_m005", "P3_m008", "P3_m010", "P3_step", "P3_c55",
           "P3_noceil", "P4_m0", "P4_m008", "P5_m0", "P5_m008", "P6a", "P6b", "P7", "P7c"]
SEEDS = list(range(1, 11))


def tasks(name):
    out = []
    if name == "fc_dk1":
        for k in (1, 2, 3):
            for s in SEEDS:
                for p in MAIN_FC:
                    out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol=p, win="fc"))
    elif name == "fc_dk2":
        for k in (1, 2, 3):
            for s in SEEDS[:5]:
                for p in ["P0", "P1", "P2", "P3_m008", "P4_m008", "P5_m008", "P6a", "P6b", "P7", "P7c"]:
                    out.append(dict(area="DK2", billing="hour", sched=k, seed=s, pol=p, win="fc"))
    elif name == "fc_quarter":
        for area in ("DK1", "DK2"):
            for k in (1, 2, 3):
                for s in SEEDS[:5]:
                    for p in ["P1", "P2", "P3_m008", "P6a", "P6b", "P7", "P7c"]:
                        out.append(dict(area=area, billing="quarter", sched=k, seed=s, pol=p, win="fc"))
    elif name == "year":
        for area in ("DK1", "DK2", "SE3"):
            for billing in ("hour", "quarter"):
                for k in (1, 2, 3):
                    for s in SEEDS[:3]:
                        for p in ["P0", "P1", "P2", "P2n", "P6a", "P7"]:
                            out.append(dict(area=area, billing=billing, sched=k, seed=s, pol=p, win="year"))
    elif name == "faults":
        for k in (1, 2, 3):
            for s in SEEDS[:3]:
                for p in ["P2", "P2_tariff_utc", "P2_tariff_position", "P2_tariff_frozen",
                          "P2_rank_quarters", "P2_hour_first_quarter"]:
                    out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol=p, win="year"))
    elif name == "publication":
        for k in (1, 2, 3):
            for s in SEEDS[:3]:
                for p in ["P2", "P2n", "P6a"]:
                    for pub in ("14", "18", "skip"):
                        out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol=p, win="year", pub=pub))
                for p in ["P3_m008"]:
                    for pub in ("13", "18", "skip"):
                        out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol=p, win="fc", pub=pub))
    elif name == "sensitivity":
        for k in (1, 2, 3):
            for s in SEEDS[:5]:
                for p in ["P2", "P3_m008", "P6a", "P6b", "P7", "P7c"]:
                    out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol=p, win="fc", taper=1))
                for p in ["P2", "P3_m008"]:
                    out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol=p, win="fc", replan=15))
                    out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol=p, win="fc", idle=0.3))
                    out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol=p, win="fc", idle=0.5))
                    out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol=p, win="fc", buffer=60))
                out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol="P6b_start", win="fc"))
                for p in ["P1", "P2", "P7"]:
                    out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol=p, win="fc", idle=0.3))
                    out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol=p, win="fc", idle=0.5))
                    out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol=p, win="fc", buffer=60))
                    out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol=p, win="fc", replan=15))
    elif name == "extra":
        for area in ("DK1",):
            for k in (1, 2, 3):
                for s in SEEDS[:5]:
                    for p in ["P6a_start", "P6b_start"]:
                        out.append(dict(area=area, billing="quarter", sched=k, seed=s, pol=p, win="fc"))
                    out.append(dict(area=area, billing="hour", sched=k, seed=s, pol="P6a_start", win="fc"))
                    for p in ["P6b", "P6a"]:
                        out.append(dict(area=area, billing="hour", sched=k, seed=s, pol=p, win="fc", grid=0.33))
                    for p in ["P3_noceil_m0", "P3_noceil_m020", "P4_noceil", "P5_noceil"]:
                        out.append(dict(area=area, billing="hour", sched=k, seed=s, pol=p, win="fc"))
                        out.append(dict(area="DK2", billing="hour", sched=k, seed=s, pol=p, win="fc"))
                    out.append(dict(area="DK2", billing="hour", sched=k, seed=s, pol="P3_noceil", win="fc"))
    elif name == "grid":
        # SoC grid 9.9/40 kWh: a whole number of steps per quarter at full power
        for k in (1, 2, 3):
            for s in SEEDS[:5]:
                for p in ["P6a", "P6b", "P7"]:
                    out.append(dict(area="DK1", billing="quarter", sched=k, seed=s, pol=p, win="fc", grid=0.2475))
                for p in ["P6a", "P7"]:
                    out.append(dict(area="DK1", billing="hour", sched=k, seed=s, pol=p, win="fc", grid=0.2475))
    elif name == "starts":
        # charge starts with a partly used slot continuing a running session
        for billing in ("hour", "quarter"):
            for k in (1, 2, 3):
                for s in SEEDS[:5]:
                    for p in ["P1", "P2", "P3_m008", "P6a", "P6a_start", "P6b", "P6b_start", "P7"]:
                        out.append(dict(area="DK1", billing=billing, sched=k, seed=s, pol=p, win="fc"))
                for s in SEEDS[:3]:
                    for area in ("DK1", "DK2", "SE3"):
                        out.append(dict(area=area, billing=billing, sched=k, seed=s, pol="P2", win="year"))
    return out


_CACHE = {}


def area_of(folder, name):
    if name not in _CACHE:
        _CACHE[name] = (D.Area(folder, name), D.load_runs(folder, name) if name != "SE3" else [])
    return _CACHE[name]


def work(arg):
    folder, t = arg
    A, runs = area_of(folder, t["area"])
    pol = dict(POL[t["pol"]])
    kw = {}
    for k in ("markup", "start_kwh"):
        if k in pol:
            kw[k] = pol[k]
    if "ceil" in pol:
        kw["ceiling"] = pol["ceil"]
    for k in ("idle", "buffer", "replan", "grid"):
        if k in t:
            kw[k] = t[k]
    if t.get("pub") == "skip":
        kw["pub_skip"] = {FC_WINDOW[0] - dt.timedelta(days=400) + dt.timedelta(days=i) for i in range(800)}
    elif t.get("pub"):
        kw["pub_hour"] = int(t["pub"])
    P = S.Params(**kw)
    car = S.Car(taper=(0.65, 7.5) if t.get("taper") else None)
    st, en = FC_WINDOW if t["win"] == "fc" else YEAR
    t0 = time.time()
    r = S.replay(A, runs, t["sched"], t["seed"], pol, st, en, car=car, P=P, billing=t["billing"])
    pm = sorted(r.pop("plan_ms"))
    r["plan_n"] = len(pm)
    r["plan_mean"] = sum(pm) / len(pm) if pm else 0.0
    r["plan_p95"] = pm[int(0.95 * (len(pm) - 1))] if pm else 0.0
    r["plan_max"] = pm[-1] if pm else 0.0
    r["wall_s"] = time.time() - t0
    r.update(t)
    return r


if __name__ == "__main__":
    folder, out, name = sys.argv[1], sys.argv[2], sys.argv[3]
    procs = int(sys.argv[4]) if len(sys.argv) > 4 else mp.cpu_count()
    ts = tasks(name)
    # slow tasks first
    ts.sort(key=lambda t: (t["pol"] not in ("P6b", "P6b_start", "P6a"), t["win"] != "year"))
    with mp.Pool(procs) as pool, open(out, "a") as f:
        for i, r in enumerate(pool.imap_unordered(work, [(folder, t) for t in ts])):
            r["experiment"] = name
            f.write(json.dumps(r) + "\n")
            f.flush()
            if i % 20 == 0:
                print(name, i + 1, "/", len(ts), flush=True)
