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
| `run.py DATA_DIR OUT.jsonl EXPERIMENT [procs]` | Runs one experiment in parallel and appends a JSON line per run. Experiments: `fc_dk1` (all policies, 3 schedules x 10 seeds, forecast window), `fc_dk2`, `fc_quarter` (DK1 and DK2 on quarter-hour billing), `year` (known-price policies, DK1/DK2/SE3, hourly and quarter-hour billing), `faults` (composition faults), `publication` (late or missing next-day prices), `sensitivity` (taper, 15-minute re-planning, idle floor, buffer, start cost), `extra` (start cost on quarter-hours, a 0.33 kWh grid, forecast policies without the ceiling), `grid` (a 0.2475 kWh grid, a whole number of steps per quarter at 9.9 kW), `starts` (charge starts with the corrected start rule) |
| `summarise.py OUT.jsonl ... [--variants \| --billing]` | Markdown tables: adjusted cost, paired difference against P2 and against perfect foresight, misses, shortfall, arrivals under 20 %, hours above 55/60 %, charge starts, plan time; energy by tariff period. `--variants`: each sensitivity variant against its base run; `--billing`: quarter-hour against hourly billing |
| `fcerr.py DATA_DIR` | Bias and MAE of the elpriser.org runs by lead day, against settled prices |

How to run, from this folder:

```bash
python3 fetch.py /tmp/replay-data
for e in fc_dk1 fc_dk2 fc_quarter year faults publication sensitivity extra grid starts; do
  python3 run.py /tmp/replay-data /tmp/replay-results.jsonl $e
done
python3 summarise.py /tmp/replay-results.jsonl
python3 summarise.py /tmp/replay-results.jsonl --variants
python3 summarise.py /tmp/replay-results.jsonl --billing
python3 fcerr.py /tmp/replay-data
```

On four cores the whole set takes about two hours; `fc_dk1` alone about twenty minutes.

Two changes were made while the experiments ran, and neither changes a cost:
- Execution: a partly used slot that continues a running session now starts at once; only the
  first slot of a session starts late. All experiments before `starts` ran with every partly used
  slot starting late, which split some sessions in two and inflated the charge starts. Set
  `REPLAY_LATE_ALWAYS=1` to reproduce them; within a slot the price is constant, so the costs
  are identical (checked on one run: 810.71 DKK both ways, 43 against 35 starts).
- DP ceiling: a ceiling is now rounded down to the SoC grid and a hard target's level up. In
  `fc_dk1` and `fc_dk2` the ceiling was rounded up, so P6b and P7c could sit 0.05 kWh above 60 %
  and count as hours above 60 %.

`run.py sensitivity` lists P2 with the buffer, idle and re-plan variants twice; the duplicate rows
are identical and only double the count in `--variants`.

Policies (`run.py`, `POL`): P0 charge on plug-in to 80 % (or the next trip's floor); P1 timer from
00:00 to the same level; P2 corrected greedy on published prices, next departure beyond them on N8
proxy prices; P2n the same with the deadline clipped to the published prices instead; P3 P2 plus
the newest forecast with an additive markup, the coming days' usual departures as soft targets and
a 60 % ceiling on soft stock (`_m0`, `_m005`, `_m008`, `_m010`, `_step` = 0.08 then 0.10 from 48 h
after the last published hour, `_c55` = 55 % ceiling, `_noceil`, `_noceil_m0`, `_noceil_m020`); P4 the same with the rolling mean
error by lead day (last 15 days of settled outcomes) added to the forecast; P5 with the error of
the last published day's forecast added to every forecast day; P6a and P6b the exact DP in place of
the greedy for P2 and P3_m008 (`_start`: start overhead 0.3 kWh per session start); `P4_noceil`, `P5_noceil` without the ceiling; P7 perfect foresight of prices
and consumption, re-planned daily over ten days; P7c the same under the 60 % soft ceiling rule.
Composition faults (`faults`), each planned with the faulty price and billed correctly:
`P2_tariff_utc` (tariff hour read in UTC), `P2_tariff_position` (tariff hour counted from local
midnight, wrong on DST days), `P2_tariff_frozen` (tariff row and state charges of the planning
date for every slot), `P2_rank_quarters` (ranking quarter prices on an hourly product),
`P2_hour_first_quarter` (the hour priced at its first quarter).
