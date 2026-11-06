import sys, time, random, os
os.environ.setdefault("X", "1")
sys.argv = [sys.argv[0], sys.argv[1], "0"]
exec(open("exp3.py").read().split("N = int")[0])
from model import dp_energy_fast, dp_energy
rng = random.Random(5)
mx = 0
for n in range(40):
    inst = make(rng)
    a = dp_energy(inst, 0.25); b = dp_energy_fast(inst, 0.25)
    mx = max(mx, abs(a - b))
print("max |dp_energy - dp_energy_fast| over 40 real-price weeks:", mx)
import exp4
for T, L in [(168, 1.0), (672, 0.25)]:
    inst = exp4.make(T, L, 20)
    for g in (0.5, 0.25, 0.1):
        print("T=%d g=%.2f kWh: fast DP %.1f ms; with session-start state %.1f ms" % (T, g, exp4.bench(lambda: dp_energy_fast(inst, g), 3), exp4.bench(lambda: dp_energy_fast(inst, g, start_penalty=1.0), 3)))
