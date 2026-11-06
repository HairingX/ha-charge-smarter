"""Level bias of the elpriser.org forecast against settled day-ahead prices.

Usage: python bias.py <data folder>
Error e = forecast median - actual, DKK/MWh spot; on the total price e x VAT / 1000 DKK/kWh,
since every other part of the total is known in advance. Reports by days ahead of the issue
date, by hour of day, by price level, per target day and per run, and the persistence of the
error from one day to the next.
"""
import statistics as st
import sys
from collections import defaultdict

from common import GRID_COMPANY, VAT, day_hours, load_actual, load_runs, total


def ac1(v):
    m = st.mean(v)
    den = sum((x - m) ** 2 for x in v)
    return sum((v[i] - m) * (v[i + 1] - m) for i in range(len(v) - 1)) / den if den else float("nan")


def main(folder):
    act = load_actual(folder)
    for area in ("DK1", "DK2"):
        A = act[area]
        runs = load_runs(folder, area)
        rows = []  # (issued, k, date, hour, f, y)
        for iss, fc in runs.items():
            for (d, h), (f, _, _) in fc.items():
                if (d, h) in A:
                    rows.append((iss, (d - iss).days, d, h, f, A[(d, h)]))
        days = sorted({r[2] for r in rows})
        print(f"===== {area} ({GRID_COMPANY[area]}): {len(runs)} runs {min(runs)}..{max(runs)}; "
              f"{len(rows)} forecast-hours with an actual; {len(days)} target days {days[0]}..{days[-1]}")

        print(" -- by days ahead of issue (k): n hours, target days, bias mean/median, MAE, share e<0,"
              " mean actual, bias/mean actual; total price (incl. VAT): bias DKK/kWh, bias/mean total")
        byk = defaultdict(list)
        for r in rows:
            byk[r[1]].append(r)
        for k in sorted(byk):
            v = byk[k]
            e = [f - y for *_, f, y in v]
            ym = st.mean(y for *_, y in v)
            tm = st.mean(total(area, r[3], r[5]) for r in v)
            print(f"  D+{k}: n={len(v):4d} days={len({r[2] for r in v}):2d} bias {st.mean(e):+5.0f} med {st.median(e):+5.0f} "
                  f"MAE {st.mean(abs(x) for x in e):4.0f} neg {100*sum(x < 0 for x in e)/len(e):3.0f}% "
                  f"actual {ym:5.0f} rel {100*st.mean(e)/ym:+4.0f}% | total bias {VAT*st.mean(e)/1000:+.3f} "
                  f"of {tm:.3f} = {100*VAT*st.mean(e)/1000/tm:+.0f}%")
        core = [r for r in rows if 2 <= r[1] <= 7]

        night = [r[4] - r[5] for r in core if r[3] < 6]
        print(f" -- night hours 00-05, D+2..D+7: bias {st.mean(night):+.0f} DKK/MWh spot = {VAT*st.mean(night)/1000:+.3f} DKK/kWh total")
        cov = [r for r in rows if 2 <= r[1] <= 7]
        band = [runs[r[0]][(r[2], r[3])] for r in cov]
        above = sum(r[5] > b[2] for r, b in zip(cov, band)) / len(cov)
        below = sum(r[5] < b[1] for r, b in zip(cov, band)) / len(cov)
        print(f" -- P10-P90 band, D+2..D+7: actual above P90 {100*above:.0f}%, below P10 {100*below:.0f}% (10% each if calibrated)")
        import numpy as _np
        half_day = sorted({r[2] for r in core})[len({r[2] for r in core}) // 2]
        for label, sub in (("all", core), ("target days before " + str(half_day), [r for r in core if r[2] < half_day]),
                           ("target days from " + str(half_day), [r for r in core if r[2] >= half_day])):
            b, a = _np.polyfit([r[4] for r in sub], [r[5] for r in sub], 1)
            print(f" -- Mincer-Zarnowitz fit actual = a + b x forecast, D+2..D+7, {label}: a {a:+.0f}, b {b:.2f} (n={len(sub)})")
        print(" -- by local hour of day, D+2..D+7 pooled: bias, MAE")
        byh = defaultdict(list)
        for r in core:
            byh[r[3]].append(r[4] - r[5])
        print("   " + " ".join(f"{h:02d}:{st.mean(byh[h]):+.0f}" for h in range(24)))
        print("   MAE " + " ".join(f"{h:02d}:{st.mean(abs(x) for x in byh[h]):.0f}" for h in range(24)))

        def bins(key, label):
            s = sorted(core, key=key)
            n = len(s) // 5
            print(f" -- by quintile of {label}, D+2..D+7: [range] bias, MAE, share e<0")
            for i in range(5):
                b = s[i * n:(i + 1) * n] if i < 4 else s[4 * n:]
                e = [f - y for *_, f, y in b]
                print(f"   [{key(b[0]):6.0f}..{key(b[-1]):6.0f}] bias {st.mean(e):+5.0f} MAE {st.mean(abs(x) for x in e):4.0f}"
                      f" neg {100*sum(x < 0 for x in e)/len(e):3.0f}%")
        bins(lambda r: r[5], "actual price")
        bins(lambda r: r[4], "forecast price")
        # level known at issue: mean actual of the issue day and the day after (both published)
        known = {}
        for iss in runs:
            v = [A.get((iss + __import__("datetime").timedelta(j), h)) for j in (0, 1) for h in range(24)]
            if all(x is not None for x in v):
                known[iss] = st.mean(v)
        bins(lambda r: known.get(r[0], float("nan")), "known level at issue (mean of D, D+1)")

        print(" -- per target day: mean error over all runs D+2..D+7 (day-level), and actual daily mean")
        bd = defaultdict(list)
        for r in core:
            bd[r[2]].append(r[4] - r[5])
        ser = []
        for d in sorted(bd):
            y = day_hours(A, d)
            ser.append(st.mean(bd[d]))
            print(f"   {d} err {st.mean(bd[d]):+5.0f} actual mean {st.mean(y) if y else float('nan'):5.0f} (n={len(bd[d])})")
        rho = ac1(ser)
        n = len(ser)
        neff = n * (1 - rho) / (1 + rho) if rho < 1 else 1
        se = st.stdev(ser) / neff ** 0.5
        print(f"   target days {n}: mean {st.mean(ser):+.0f} sd {st.stdev(ser):.0f}, share <0 {100*sum(x < 0 for x in ser)/n:.0f}%,"
              f" lag-1 autocorr {rho:.2f}, effective n {neff:.1f}, mean/se {st.mean(ser)/se:.1f}")
        half = n // 2
        print(f"   first {half} days mean {st.mean(ser[:half]):+.0f}, last {n-half} days {st.mean(ser[half:]):+.0f}")

        print(" -- per run: mean error over its realised D+2..D+7 hours")
        pr = defaultdict(list)
        for r in core:
            pr[r[0]].append(r[4] - r[5])
        rs = [(i, st.mean(v), len(v)) for i, v in sorted(pr.items())]
        print("   " + " ".join(f"{i.strftime('%m-%d')}:{m:+.0f}" for i, m, _ in rs))
        print(f"   runs {len(rs)}, share with mean error < 0: {100*sum(m < 0 for _, m, _ in rs)/len(rs):.0f}%")

        print(" -- does the realised error predict the next one? (day-level, k=2)")
        # e2[d] = day-mean error of the run issued d-2 for day d (horizon 2)
        e2 = {}
        for iss, fc in runs.items():
            d = iss + __import__("datetime").timedelta(2)
            f = day_hours({k: v[0] for k, v in fc.items()}, d)
            y = day_hours(A, d)
            if f and y:
                e2[d] = st.mean(f) - st.mean(y)
        pairs = [(e2[d], e2[d + __import__("datetime").timedelta(1)]) for d in e2 if d + __import__("datetime").timedelta(1) in e2]
        x, y = zip(*pairs)
        mx, my = st.mean(x), st.mean(y)
        c = sum((a - mx) * (b - my) for a, b in pairs) / (sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)) ** 0.5
        print(f"   corr(error on day d, error on day d+1), horizon 2, n={len(pairs)}: {c:.2f}")
        # anchor: run(D-1)'s error on D+1 (its horizon 2) vs run(D)'s errors on D+2..D+7
        import datetime as _dt
        for k in range(2, 8):
            pr2 = []
            for D in runs:
                prev = runs.get(D - _dt.timedelta(1))
                if prev is None:
                    continue
                fa = day_hours({kk: v[0] for kk, v in prev.items()}, D + _dt.timedelta(1))
                ya = day_hours(A, D + _dt.timedelta(1))
                ft = day_hours({kk: v[0] for kk, v in runs[D].items()}, D + _dt.timedelta(k))
                yt = day_hours(A, D + _dt.timedelta(k))
                if fa and ya and ft and yt:
                    pr2.append((st.mean(fa) - st.mean(ya), st.mean(ft) - st.mean(yt)))
            if len(pr2) > 3:
                x, y = zip(*pr2)
                mx, my = st.mean(x), st.mean(y)
                den = (sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)) ** 0.5
                c = sum((a - mx) * (b - my) for a, b in pr2) / den
                print(f"   anchor error (run D-1 on D+1) vs latest-run error on D+{k}: corr {c:+.2f}, n={len(pr2)}")


if __name__ == "__main__":
    main(sys.argv[1])
