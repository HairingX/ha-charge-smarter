"""Shared loading for the forecast-bias experiments.

Reads a data folder (see README.md) holding:
  dap.json                 Energi Data Service DayAheadPrices, DK1 and DK2 (quarter-hours)
  arch_<AREA>_<date>.json  elpriser.org forecast archive runs
Prices are DKK/MWh spot excl. VAT unless a name says total. The total price is hourly billing:
(hourly mean of the four quarter spot prices + grid tariff + Energinet tariffs + elafgift) x VAT.
"""
import datetime as dt
import glob
import json
import os
from collections import defaultdict

# DatahubPricelist rows valid 2026-10-01..2027-01-01, DKK/kWh excl. VAT, index = local hour.
# N1 A/S - 131 "Nettarif C" (CD), Radius Elnet A/S "Nettarif C" (DT_C_01).
_LO_HI_PEAK = {"DK1": (0.087854, 0.263563, 0.79069), "DK2": (0.106175, 0.318524, 0.955573)}
GRID_COMPANY = {"DK1": "N1 (area 131)", "DK2": "Radius"}
# Energinet: Transmissions nettarif 40000 (0.043) + Systemtarif 41000 (0.072); elafgift EA-001 0.008.
FLAT = 0.043 + 0.072 + 0.008
VAT = 1.25


def tariff(area, hour):
    lo, hi, pk = _LO_HI_PEAK[area]
    return lo if hour < 6 else (pk if 17 <= hour < 21 else hi)


def total(area, hour, spot_mwh):
    """All-in household price, DKK/kWh incl. VAT, for a spot price in DKK/MWh."""
    return VAT * (spot_mwh / 1000 + tariff(area, hour) + FLAT)


def load_actual(folder):
    """{area: {(date, hour): spot DKK/MWh}}, the hourly mean of the quarter-hour prices."""
    q = defaultdict(list)
    for r in json.load(open(os.path.join(folder, "dap.json")))["records"]:
        t = r["TimeDK"]
        q[(r["PriceArea"], dt.date.fromisoformat(t[:10]), int(t[11:13]))].append(r["DayAheadPriceDKK"])
    out = defaultdict(dict)
    for (a, d, h), v in q.items():
        out[a][(d, h)] = sum(v) / len(v)
    return out


def load_runs(folder, area):
    """{issued date: {(date, hour): (p50, p10, p90)}} for the forecast days of each run.

    A run generated before the day-ahead auction published lists the next day as a forecast with
    no values; those entries are skipped.
    """
    runs = {}
    for f in sorted(glob.glob(os.path.join(folder, f"arch_{area}_*.json"))):
        d = json.load(open(f))
        issued = dt.date.fromisoformat(d["issued"])
        fc = {}
        for day in d["days"]:
            if day["type"] != "forecast":
                continue
            date = dt.date.fromisoformat(day["date"])
            for p in day["prices"]:
                if p.get("spot_dkk_mwh") is not None:
                    fc[(date, p["hour"])] = (p["spot_dkk_mwh"], p["spot_min_dkk_mwh"], p["spot_max_dkk_mwh"])
        runs[issued] = fc
    return runs


def day_hours(prices, date):
    """The 24 values of one day, or None when any hour is missing."""
    v = [prices.get((date, h)) for h in range(24)]
    return None if any(x is None for x in v) else v


def spearman(x, y):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")
