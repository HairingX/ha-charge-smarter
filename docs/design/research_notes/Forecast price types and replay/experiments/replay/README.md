# End-to-end replay

The experiments behind `../../end_to_end_replay.md`: one car charged at home, re-planned every
hour (and at every plug-in) with only what the integration would know at that moment, over every
day with an elpriser.org forecast run (2026-10-07 to 2026-11-06) and, for the policies that need
no forecast, over the twelve months 2025-11-07 to 2026-11-06.

Python 3.13 or later, standard library only. `sim.py` imports `fulldp.py` from
`../../../Cheapest home EV charging/experiments/panel_optimisation/` (the exact DP over slot, SoC
grid and on-state), so keep both folders in place. The downloaded data is not kept here.

| File | What it does |
|---|---|
| `fetch.py DATA_DIR` | Downloads the public data into `DATA_DIR`: Energi Data Service `DayAheadPrices` for DK1, DK2 and SE3 (quarter hours, 2025-10-01 on); `DatahubPricelist` rows for N1 A/S - 131 and Radius Elnet (Nettarif C), Energinet's system and transmission tariffs and the elafgift, and any tariff row published per quarter hour; every elpriser.org forecast archive run for DK1 and DK2 (`/api/forecast/archive`). Never calls Carnot. Retries on HTTP 429 |
| `data.py` | Composes the price the engine is given: `(spot + grid tariff of the local date and clock hour + Energinet + elafgift) x 1.25`, per quarter (`total_q`) and as the hourly product, the simple mean of the four quarters plus the hourly tariff (`total_h`). Loads the forecast runs with the minute each became available (`generatedAt`) |
| `sim.py` | The replay: schedules, the caller (consumption estimates, departures expanded over the horizon), the information set at each minute (published prices, newest run, bias corrections, N8 proxy prices, deliberate composition faults), the corrected greedy, the DP wrapper, execution with late start, and the metrics |
| `run.py DATA_DIR OUT.jsonl EXPERIMENT [procs]` | Runs one experiment in parallel and appends a JSON line per run. Experiments: `fc_dk1` (all policies, 3 schedules x 10 seeds, forecast window), `fc_dk2`, `fc_quarter` (DK1 and DK2 on quarter-hour billing), `year` (known-price policies, DK1/DK2/SE3, hourly and quarter-hour billing), `faults` (composition faults), `publication` (late or missing next-day prices), `sensitivity` (taper, 15-minute re-planning, idle floor, buffer, start cost) |
| `summarise.py OUT.jsonl ...` | Markdown tables: adjusted cost, paired difference against P2 and against perfect foresight, misses, shortfall, arrivals under 20 %, hours above 55/60 %, charge starts, plan time; energy by tariff period |
| `fcerr.py DATA_DIR` | Bias and MAE of the elpriser.org runs by lead day, against settled prices |

How to run, from this folder:

```bash
python3 fetch.py /tmp/replay-data
for e in fc_dk1 fc_dk2 fc_quarter year faults publication sensitivity; do
  python3 run.py /tmp/replay-data /tmp/replay-results.jsonl $e
done
python3 summarise.py /tmp/replay-results.jsonl
python3 fcerr.py /tmp/replay-data
```

On four cores the whole set takes about an hour and a half; `fc_dk1` alone about ten minutes.

Policies (`run.py`, `POL`): P0 charge on plug-in to 80 % (or the next trip's floor); P1 timer from
00:00 to the same level; P2 corrected greedy on published prices, next departure beyond them on N8
proxy prices; P2n the same with the deadline clipped to the published prices instead; P3 P2 plus
the newest forecast with an additive markup, the coming days' usual departures as soft targets and
a 60 % ceiling on soft stock (`_m0`, `_m005`, `_m008`, `_m010`, `_step` = 0.08 then 0.10 from 48 h
after the last published hour, `_c55` = 55 % ceiling, `_noceil`); P4 the same with the rolling mean
error by lead day (last 15 days of settled outcomes) added to the forecast; P5 with the error of
the last published day's forecast added to every forecast day; P6a and P6b the exact DP in place of
the greedy for P2 and P3_m008 (`_start`: start overhead 0.3 kWh); P7 perfect foresight of prices
and consumption, re-planned daily over ten days; P7c the same under the 60 % soft ceiling rule.
