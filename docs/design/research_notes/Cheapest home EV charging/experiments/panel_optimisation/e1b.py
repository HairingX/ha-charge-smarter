import sys
sys.argv = ['x', '0']
exec(open('e1.py').read().split('N = int')[0])
N = 150
hs, hts = P.hourly(P.spot); ht, _ = P.hourly(P.total)
hsc = [max(0.0, x) for x in hs]; sc = [max(0.0, x) for x in P.spot]
cases = [("spot, hourly", hs, hts, 1.0), ("spot>=0, hourly", hsc, hts, 1.0), ("total, hourly", ht, hts, 1.0),
         ("spot, 15 min", P.spot, P.times, 0.25), ("spot>=0, 15 min", sc, P.times, 0.25), ("total, 15 min", P.total, P.times, 0.25)]
for pname, power in (("taper", taper), ("const 11 kW", const)):
    for name, ser, ts, L in cases:
        rng = random.Random(2026)
        gaps, absg, opts = [], [], []
        for n in range(N):
            inst = make(rng, ser, ts, L, power)
            opt = dp_energy_fast(inst, 0.25)
            c, ok, _ = greedy_d22(inst, trim="price")
            if not ok: c = float("inf")
            gaps.append((c - opt) / opt * 100); absg.append(c - opt); opts.append(opt)
        gaps.sort(); absg.sort()
        print("%-11s %-16s N=%d gap%%: median %.2f p90 %.2f p95 %.2f max %.2f | abs DKK/wk: median %.2f p90 %.2f max %.2f | mean opt %.1f | worse>1%% in %d" % (
            pname, name, N, gaps[N // 2], gaps[int(N * .9)], gaps[int(N * .95)], gaps[-1], absg[N // 2], absg[int(N * .9)], absg[-1],
            sum(opts) / N, sum(1 for g in gaps if g > 1)), flush=True)
