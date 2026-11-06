"""Prices as the integration would compose them, on a quarter-hour grid in absolute time.

Time is counted in minutes from T0 (2025-10-01 00:00 Europe/Copenhagen). Quarter q covers minutes
[15q, 15q + 15). Every price is DKK per wall kWh incl. VAT, supplier markup 0:

    total = (spot + grid tariff + Energinet system + transmission tariff + elafgift) * 1.25

The grid tariff is the DataHub row valid on the quarter's local date, indexed by local clock hour
(Price1 = 00-01). Energinet's tariffs and the elafgift are taken per calendar year from DataHub.
SE3 has no Danish tariff: its total is spot * 1.25 (flat Swedish parts left out; they do not move
the ranking).
"""
import datetime as dt
import glob
import json
import os
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Copenhagen")
UTC = dt.timezone.utc
T0 = dt.datetime(2025, 10, 1, tzinfo=TZ).astimezone(UTC)
VAT = 1.25


def minute_of(t):
    """Minutes from T0 of an aware datetime."""
    return int((t.astimezone(UTC) - T0).total_seconds() // 60)


def local(m):
    """Local datetime of a minute index."""
    return (T0 + dt.timedelta(minutes=m)).astimezone(TZ)


def local_midnight(d):
    """Minute index of local midnight starting date d."""
    return minute_of(dt.datetime(d.year, d.month, d.day, tzinfo=TZ))


GRID_OWNER = {"DK1": ("tariff_N1.json", "CD", "Nettarif C"),
              "DK2": ("tariff_Radius.json", "DT_C_01", "Nettarif C")}


class Area:
    """Quarter-hour spot, tariff and billed prices of one price area."""

    def __init__(self, folder, area, tariff_mode="local"):
        self.area = area
        recs = json.load(open(os.path.join(folder, "dap_%s.json" % area)))["records"]
        recs.sort(key=lambda r: r["TimeUTC"])
        n = len(recs)
        self.nq = n
        self.spot = [0.0] * n
        for r in recs:
            t = dt.datetime.fromisoformat(r["TimeUTC"]).replace(tzinfo=UTC)
            q = minute_of(t) // 15
            self.spot[q] = r["DayAheadPriceDKK"] / 1000.0
        self.loc = [local(15 * q) for q in range(n)]
        flat = {}
        for r in json.load(open(os.path.join(folder, "tariff_state.json")))["records"]:
            y = int(r["ValidFrom"][:4])
            flat[y] = flat.get(y, 0.0) + r["Price1"]
        self.flat_by_year = flat
        rows = []
        if area in GRID_OWNER:
            fn, code, note = GRID_OWNER[area]
            for r in json.load(open(os.path.join(folder, fn)))["records"]:
                if r["ChargeTypeCode"] == code and r["Note"] == note:
                    rows.append((r["ValidFrom"][:10], (r["ValidTo"] or "9999")[:10],
                                 [r["Price%d" % i] or 0.0 for i in range(1, 25)]))
        self.rows = rows
        self.tariff = [self.grid_tariff(self.loc[q], tariff_mode, q) for q in range(n)]
        self.flat = [flat[self.loc[q].year] if area in GRID_OWNER else 0.0 for q in range(n)]
        self.total_q = [(self.spot[q] + self.tariff[q] + self.flat[q]) * VAT for q in range(n)]
        self.total_h = [0.0] * n
        for q in range(0, n - 3, 4):
            s = sum(self.spot[q:q + 4]) / 4
            for k in range(4):
                self.total_h[q + k] = (s + self.tariff[q + k] + self.flat[q + k]) * VAT

    def grid_tariff(self, lt, mode="local", q=None):
        """Grid tariff in force at local time lt. mode 'utc' and 'position' are deliberate bugs."""
        if not self.rows:
            return 0.0
        d = lt.date().isoformat()
        hour = lt.hour
        if mode == "utc":
            hour = lt.astimezone(UTC).hour
        elif mode == "position":       # hours counted from local midnight, ignoring DST
            mid = dt.datetime(lt.year, lt.month, lt.day, tzinfo=TZ)
            hour = min(23, int((lt - mid).total_seconds() // 3600))
        for a, b, p in self.rows:
            if a <= d < b:
                return p[hour]
        raise KeyError(d)

    def tariff_on(self, lt, frozen_date=None):
        """Tariff for local time lt; frozen_date applies that date's row instead (stale-tariff bug)."""
        if frozen_date is None:
            return self.grid_tariff(lt)
        d = frozen_date.isoformat()
        for a, b, p in self.rows:
            if a <= d < b:
                return p[lt.hour]
        return 0.0

    def compose(self, spot_kwh, lt):
        """Total incl. VAT for a spot price (DKK/kWh) at local time lt."""
        fl = self.flat_by_year[lt.year] if self.rows else 0.0
        return (spot_kwh + self.grid_tariff(lt) + fl) * VAT

    def billed(self, q, billing):
        return self.total_h[q] if billing == "hour" else self.total_q[q]


def load_runs(folder, area):
    """Forecast runs: list of (available_minute, last_actual_date, {local hour start minute: spot DKK/kWh})."""
    runs = []
    for f in sorted(glob.glob(os.path.join(folder, "arch_%s_*.json" % area))):
        d = json.load(open(f))
        avail = minute_of(dt.datetime.fromisoformat(d["model"]["generatedAt"]))
        last_actual = None
        fc = {}
        for day in d["days"]:
            date = dt.date.fromisoformat(day["date"])
            if day["type"] == "actual":
                last_actual = date
                continue
            for p in day["prices"]:
                if p["spot_dkk_mwh"] is None:   # a day the run left unforecast (not yet published)
                    continue
                # Each local clock hour; on a 25-hour day the repeated hour gets the same value.
                for fold in (0, 1):
                    lt = dt.datetime(date.year, date.month, date.day, p["hour"], tzinfo=TZ, fold=fold)
                    fc[minute_of(lt)] = p["spot_dkk_mwh"] / 1000.0
        runs.append((avail, last_actual, fc, d["issued"]))
    runs.sort()
    return runs
