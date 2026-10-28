# The planning engine

The engine decides when one car charges, how much, and at what cost, from the data it is given at
the moment it is called. It knows nothing of Home Assistant, calendars, chargers' brands or price
sources. It lives in `custom_components/charge_smarter/charge_smarter/`, imports only the
standard library, and is meant to become the library `charge-smarter`.

Decision IDs (D1, D2, ...) refer to [decisions.md](decisions.md).

## 1. Principles

1. **Environment-agnostic.** No Home Assistant, no I/O, no calendars, no third-party clients.
   Plain Python values in, plain Python values out (D1).
2. **Car- and charger-agnostic.** No brand, chemistry, power level or protocol is assumed; every
   car and charger value arrives with each call (D2).
3. **Units.** The engine works in kW, kWh, hours and SoC percent. Distance is converted to SoC
   or kWh by the caller (km and miles never reach the engine). Prices are opaque numbers in
   whatever currency the caller uses (D3).
4. **No hardcoded domain values.** Defaults exist only for algorithm tunables, and every one of
   them can be overridden per call (D4).
5. **A pure function.** Same input, same output. No state between calls, no memory of an earlier
   plan, no change detection. Each call plans from scratch (D10).
6. **The core trusts its input.** The public entry validates and corrects the input; the core
   computes on clean data with no defensive checks (D11).
7. **Never returns text.** Output is enum codes, typed values, structured parameters and
   references to input objects. Presentation and translation belong to the caller (D5).
8. **Environment is modelled by the caller.** Battery temperature, weather and altitude are folded
   into the power curves before the call. The engine models only what changes during charging:
   the taper with SoC and the charger's behaviour over the session (D6, D12).
9. **Declarative and best-effort.** The engine always returns a plan when one is possible, and
   charges in expensive hours when that is what a target requires. It never breaks a constraint
   the user set (a cap, the completion buffer); when a target cannot be met within them, it plans
   as far as it can and reports the shortfall (D7, D8, D9).
10. **A planning function, not a policy engine.** Solar surplus, load balancing, several cars on
    one charger, tariffs and V2G belong in the layers around it (D13).

## 2. Layers

| Layer | Owns |
|---|---|
| **Caller** (the Home Assistant integration, other adapters) | Reading chargers, cars, prices, calendars and solar through other integrations; turning trips into absences and targets; converting distance to energy; folding temperature into the curves; when to call the engine; caching, debounce, hysteresis against replanning churn; persistence across restarts; the manual controls; acting on the plan |
| **API** (the engine's public `plan()`) | Validating the input. What can safely be corrected is corrected and reported (prices out of order are sorted); what cannot is refused with `ValueError` (a naive datetime, a negative capacity) |
| **Core** | Computing the plan from clean input |

Callers see one function, `plan(input) -> output`. The split between API and core is internal.
Which faults are corrected and which refused is settled per field in the design of the API
layer (O6).

## 3. Code structure

Each concern is its own module, so that each can grow without touching the others. No abstract
base classes or strategy objects until a second implementation exists (D14).

| Module | Concern |
|---|---|
| `contract` | The public types |
| `validation` | The API layer: checks and corrections |
| `charging_model` | Simulating a charge: SoC, time and the power curves to energy and SoC over time |
| `windows` | Finding the hours available for charging: absences and price data |
| `scoring` | Ranking hours: today the price with the forecast markup; later carbon, solar, battery wear |
| `trip_chain` | The SoC chain across absences, required SoC per target, the up-front feasibility check |
| `planner` | `plan()`: the decision order and assembly of the output |

## 4. Input

### 4.1 State, read live from the car and charger

| Field | Meaning |
|---|---|
| `now` | Current time, timezone-aware |
| `current_soc` | 0–100 |
| `soc_last_updated` | When `current_soc` was read, timezone-aware |
| `is_plugged_in` | Whether the car is connected |
| `is_currently_charging` | Whether a charge is running |

### 4.2 Car and charger

| Field | Meaning |
|---|---|
| `battery_capacity_kwh` | Usable capacity, > 0 |
| `car_power_soc_steps` | `[(soc_percent, max_kw), ...]`, ascending: what the car accepts from that SoC upward. The taper, e.g. 11 kW falling to 7.5 kW from 65 % (D16) |
| `charger_power_session_steps` | `[(minutes_into_session, max_kw), ...]`, ascending: what the charger delivers that far into a session. Covers both a gentle start (`[(0, 3.3), (2, 6.6), (5, 11.0)]`) and derating from heat (D16) |
| `charger_efficiency` | In (0, 1] |
| `charger_max_session_kwh` | Optional limit on the energy of one session (D17) |
| `car_max_soc` | Hard ceiling the car allows, e.g. 100 or 95. Never exceeded (D18) |
| `charger_auto_threshold` | Optional price below which the charger's own automation is left to charge. `None` turns it off; `0.0` means negative prices only |

Power at any moment of a charge = `min(car curve at current SoC, charger curve at minutes into
the session) × efficiency`.

### 4.3 The user's preferences

| Field | Meaning |
|---|---|
| `default_target_soc` | The normal ceiling, e.g. 80. A soft limit: exceeded only where a target's own cap allows it |
| `min_safety_soc` | Below this the car charges at once, whatever the price |
| `min_idle_soc` | With nothing planned, keep the car at least this full, charged in cheap hours |
| `default_arrival_soc` | Default for the SoC wanted on return from an absence, e.g. 15 (`default_trip_buffer_soc` in `sources/`) |
| `charge_complete_buffer_minutes` | Charging is planned to finish this long before each target; default 20. Covers a slow charge on a cold day, a tired battery, and unplugging before leaving. Global; per target later if needed (D8) |

Recommended order, documented but not enforced: `min_safety_soc ≤ min_idle_soc ≤
default_target_soc`.

### 4.4 Schedule

The schedule is two lists, which the caller links when an absence is a trip (D15):

- **`AbsenceWindow(start, end, energy_kwh)`**: the car cannot charge in `[start, end)`. `energy_kwh`
  is what it uses meanwhile (0 for a car at the workshop). Covers trips, workshop visits and
  hours the user does not want the car to charge.
- **`ChargeTarget(at, target_soc, max_charge_soc=None)`**: the car must have `target_soc` at
  `at`. A departure, or "ready by Saturday 07:00" with no trip. `max_charge_soc` is this
  target's own cap; `None` means `default_target_soc`.

A trip becomes an absence from departure to return, and a target at departure. Where the
arrival SoC for an absence is stated is open (O2).

### 4.5 Prices

`PricePoint(start, price, is_forecast=False)`, one per hour (sub-hour slots are a later
question). Known prices and forecasts arrive in the same list; `is_forecast` tells them apart. The
API layer sorts them and checks they form a continuous series.

### 4.6 Tunables (all with defaults, all overridable)

| Field | Default | Meaning |
|---|---|---|
| `soc_max_age_minutes` | 30 | A SoC reading older than this is stale |
| `soc_refresh_delay_seconds` | 30 | Delay from waking the car to asking for SoC |
| `wake_up_before_charge_minutes` | 5 | Wake the car this long before a window |
| `idle_planning_horizon_hours` | 24 | Deadline for reaching `min_idle_soc` with nothing planned |
| `simulation_step_minutes` | 6 (3 proposed) | Resolution of the charge simulation: precision against speed |
| `min_session_kwh` | 2.0 | A soft minimum per session: skipped when below, unless a target requires it or charging later costs more (D19) |
| `forecast_markup_steps` | not decided | Uncertainty markup on forecast prices by hours ahead (D20, O4) |

## 5. Output

| Field | Meaning |
|---|---|
| `should_charge_now` | True when a window covers `now` |
| `reason` | `PlanReason`, below |
| `feasibility` | `FULL`, `PARTIAL` or `INFEASIBLE`, the worst of the target results |
| `windows` | Chronological `ChargeWindow(start, end, target_soc, expected_kwh, expected_cost, avg_price, requires_wakeup)`. Cost and average price use the raw prices, never the marked-up ones |
| `actions` | Chronological `PlannerAction(type, execute_at, params)`: `START_CHARGING`, `STOP_CHARGING`, `WAKE_UP_CAR`, `SET_CHARGE_LIMIT {soc_limit}`, `REQUEST_SOC_REFRESH` |
| `target_results` | Per target: status (`FULLY_MET`, `PARTIAL`, `INFEASIBLE`), planned SoC at the target, expected SoC on return, margin to the arrival SoC (`TripResult` in `sources/`) |
| `warnings` | `PlannerWarning(code, subject, params)`. Each code has a fixed schema for `params` (D21) |

`PlanReason`: `CAR_NOT_PLUGGED_IN`, `STALE_SOC_NEEDS_WAKEUP`, `MIN_SOC_SAFETY`,
`CHARGER_HANDLES_LOW_PRICE`, `NO_TRIPS_NO_NEED`, `BELOW_IDLE_FLOOR`, `SOC_ALREADY_SUFFICIENT`,
`SCHEDULED_TRIP`, `INSUFFICIENT_TIME`, `SESSION_TOO_SHORT`.

Warning codes kept: `TRIP_ENERGY_EXCEEDS_CAPACITY`, `TRIP_BUFFER_UNREACHABLE`,
`TRIP_REQUIRED_EXCEEDS_CAP`, `INSUFFICIENT_PRICE_DATA`, `INSUFFICIENT_TIME_WITH_BUFFER`,
`INFEASIBLE_TRIP_CHAIN`, plus whatever the API layer's corrections report. Codes for bad rows that
the core used to skip are gone; the API layer handles bad rows (D11).

## 6. Algorithm

### 6.1 Decision order, first match wins

1. Not plugged in → `CAR_NOT_PLUGGED_IN`.
2. SoC stale → `STALE_SOC_NEEDS_WAKEUP`, with `WAKE_UP_CAR` now and `REQUEST_SOC_REFRESH` after
   `soc_refresh_delay_seconds`. Whether a stale reading below `min_safety_soc` should charge
   first is open (O7).
3. `current_soc < min_safety_soc` → `MIN_SOC_SAFETY`, charge now, price ignored.
4. Current price below `charger_auto_threshold` → `CHARGER_HANDLES_LOW_PRICE`.
5. No targets ahead: at or above `min_idle_soc` → `NO_TRIPS_NO_NEED`; below → fill to
   `min_idle_soc` in the cheapest hours before `min(now + idle_planning_horizon_hours, end of
   price data)` → `BELOW_IDLE_FLOOR`.
6. Targets ahead → plan them (6.2) → `SCHEDULED_TRIP`, or `SOC_ALREADY_SUFFICIENT` when nothing
   needs charging.

### 6.2 Planning the targets: cheapest first over the whole horizon (D22)

Planning gap by gap is wrong. Two cases show why:

- A trip in the morning and another in the evening, with little time between them: the evening's
  energy must be bought in the cheap night before the morning trip, though the morning trip
  alone needs less.
- A trip in the evening, with half-price hours the night after: charge only what the evening trip
  needs, and buy the rest in the night.

**Pass 1, required SoC.** Working backwards from the last target, compute for each target the SoC
it must have:

- its own need: `max(target_soc, arrival_soc + consumption of the absence that follows)`, where
  consumption is `energy_kwh` as a percentage of capacity;
- plus whatever a later target needs that cannot be charged in the hours between the two.

The result is a hard floor per target. If the floors add up to more than the available hours can
deliver, the engine reports `INFEASIBLE_TRIP_CHAIN` here, before searching (D23).

**Pass 2, cheapest hours.** Take every hour in which the car can charge (not in an absence, not in
the buffer before a target, within the price data). Rank them by marked-up price. Take hours
cheapest first and give each to the earliest target still short whose deadline it precedes,
until every floor is met. The charge in each hour is simulated with the power curves (6.3), so
a later hour at high SoC delivers less than an early one.

A plan with a main charge and a late top-up is then just one possible result, not a special
case. Whether to charge beyond the floors when hours are cheap is open (O1).

**Limits applied throughout:**

- **Caps.** A target's cap is `max_charge_soc`, or `default_target_soc` when unset, never above
  `car_max_soc`. The engine never plans above it. When the need exceeds the cap, it plans to the
  cap and reports `PARTIAL` with `TRIP_REQUIRED_EXCEEDS_CAP`: the user chose the cap, perhaps
  knowing they can charge on the way (D7).
- **Buffer.** No charging in `[target.at − charge_complete_buffer_minutes, target.at]`. Short of
  time, the engine plans up to the buffer and reports `PARTIAL` or `INFEASIBLE` with
  `INSUFFICIENT_TIME_WITH_BUFFER` (D8).
- **Absences.** An hour overlapping an absence is not available. An hour starting exactly at an
  absence's end is.
- **Session limit.** No window delivers more than `charger_max_session_kwh`.

### 6.3 Charge simulation (D12)

Step through the window at `simulation_step_minutes`. At each step take
`min(car_power_soc_steps at SoC, charger_power_session_steps at minutes into the session) ×
efficiency`, add the energy, update SoC. The result is an approximation, accepted for the sake of
speed and of needing nothing beyond the standard library.

### 6.4 Forecast prices (D20)

Choosing hours uses a marked-up price; costs reported use the raw one.

```
adjusted_price = price × (1 + markup / 100)
markup         = 0                                         for a known price
markup         = step value for the hours ahead            for a forecast
```

A forecast only wins when it is cheaper by more than its markup, and the further ahead, the
larger the markup. The shape of the markup and its defaults are open (O4).

## 7. Performance

`plan()` within 10 ms for 168 price points, 20 absences and 20 targets; about 1 ms is expected.
Re-entrant; frozen dataclasses only.

## 8. Tests

pytest with 100 % line coverage, as the repository requires. Every branch of the decision order,
every action with its `params`, every validation fault, and the edge cases listed in
`sources/requirements-2026-04-22.md` §7 (numeric and time boundaries, price data shapes,
combinations of targets) that still apply.
