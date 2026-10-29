"""DK1 quarter-hour spot (Energi Data Service DayAheadPrices) and the N1 area 131 'Nettarif C'
total price, per price_composition_denmark.md section 1: total = (spot + grid tariff + 0.115
Energinet + 0.008 elafgift) x 1.25, DKK/kWh, supplier markup 0. 2026 flat parts used for the
whole period (flat parts do not change rankings or absolute gaps)."""
import json, datetime as dt, os
D = os.environ.get("DK1_JSON", os.path.join(os.path.dirname(__file__), "..", "data", "dk1.json"))
recs = json.load(open(D))["records"]
recs.sort(key=lambda r: r["TimeUTC"])
times = [dt.datetime.fromisoformat(r["TimeDK"]) for r in recs]
spot = [r["DayAheadPriceDKK"] / 1000.0 for r in recs]
def tariff(t):
    winter = t.month >= 10 or t.month <= 3
    low, high, peak = (0.088, 0.264, 0.791) if winter else (0.088, 0.132, 0.343)
    h = t.hour
    if h < 6: return low
    if 17 <= h < 21: return peak
    return high
total = [(s + tariff(t) + 0.123) * 1.25 for s, t in zip(spot, times)]
def hourly(series):
    """Simple mean of the four quarters, as on the default hourly product."""
    out, ts = [], []
    for i in range(0, len(series) - 3, 4):
        if times[i].minute == 0:
            out.append(sum(series[i:i + 4]) / 4); ts.append(times[i])
    return out, ts
