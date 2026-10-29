# ChargeSmarter Motor — Consolidated Requirements

> Kept as reference. Written on 2026-04-22 and last revised on 2026-04-23; where it disagrees with `../decisions.md` or `../motor.md`, it is out of date.

> **Purpose:** single source of truth for what the motor must do. Designs, implementations, and reviews all reference this document. Updated as requirements solidify. Not the same as design docs — those propose *how*; this captures *what* and *why*.

- **Feature:** initial (motor core; HA-integration is a separate later feature)
- **Last updated:** 2026-04-22
- **Status:** living document — revise as requirements clarify

**Related documents:**
- Design — Motor round 1 (completed; superseded in part by round 2; not kept)
- [Design — Motor round 2 (multi-trip)](multi-trip-design-2026-04-22.md) (in Stage 3 review)
- [Feature exploration — advanced planning surface](feature-exploration-2026-04-22.md) (candidate feature list)
- Agent notes — working context (not kept)

---

## 1. Core principles (immutable)

These are derived directly from user statements during the initial feature work. Any feature or implementation detail must honor all of them. Violations are blockers, not preferences.

1. **Environment-agnostic.** The motor has no knowledge of Home Assistant, calendars, data sources, user interfaces, or any consuming layer. It receives plain Python values and returns plain Python values. It imports only from the standard library.

2. **Car-agnostic.** No specific car brand, battery chemistry, charging behavior, or wake-up protocol is baked into the motor. All car-specific values arrive as inputs per call.

3. **Charger-agnostic.** No specific charger vendor, power level, efficiency curve, or auto-pricing feature is assumed. All charger values arrive as inputs per call.

4. **Unit-agnostic where sensible.** The motor hardcodes only the energy/time pair (kW, kWh, hours) — any distance/miles/etc. conversion is the adapter's responsibility. Currency is fully free: the motor propagates whatever currency values the caller supplies. No unit conversion happens in the motor.

5. **All data comes from outside.** No hardcoded assumptions about specific values (battery size, charger power, safety thresholds, etc.). Defaults exist only for algorithmic tunables (not for car/charger/user-preference inputs).

6. **Defaults are fine; overrides must be possible.** For tunable algorithmic parameters (stale threshold, session minimum, wake-up lead, etc.), the motor provides defaults but every one must be overridable per `plan()` call.

7. **Stateless.** The motor carries no instance state between calls. Any "plan that spans multiple ticks" information is returned as `ActivePlan` and fed back in. Pure input-output.

8. **Fail fast on contract violations; be forgiving on data quality.** Malformed configuration (negative battery, naive datetime, out-of-range thresholds) raises `ValueError`. Malformed data rows (one bad trip among many, duplicate prices) is skipped with an informative warning; planning continues with the rest.

9. **Source-agnostic naming.** Identifiers in the public contract do not reference specific vendors, sources, or regions. "Trip" not "CalendarEvent"; "charger_auto_threshold" not "goe_price_limit".

10. **Motor is a planning function, not a policy engine.** Complex use-case logic (solar surplus prioritization, V2G, multi-car scheduling, tariff interpretation) belongs in adapter layers. The motor answers: "given these inputs, when should this one car charge, to meet which targets, at what cost."

11. **NEVER return text.** The motor produces only structured, machine-readable output — enum codes, typed dataclasses, structured `params` dicts, and object references. No free-form English strings in any public output field. Callers (the HA layer and other adapters) are responsible for any localization / presentation. This applies to warnings, trip results, status signals, and any future diagnostic output. *Principle locked 2026-04-22.*

12. **Environmental modeling is adapter-layer.** Battery temperature, outdoor weather, altitude, humidity, and other environmental factors that affect charging are **not modeled in the motor**. The adapter pre-composes motor inputs (notably the power-curve step tables) based on current environmental conditions and passes already-adjusted values to the motor each tick. This keeps the motor environmentally blind and maximally portable. A future PyPI-side utility module may provide `compose_curve(base_soc_steps, base_session_steps, battery_temp, ...)` helpers for adapters; those live *outside* the motor. *Principle locked 2026-04-22.*

13. **Best-effort, never refuse.** The motor always produces a plan when a plan is possible, even when prices are high or data is incomplete. A real home charger must charge on high-price hours if that's what it takes to meet the target; the motor does the same, just smarter. No branch of the motor raises "I cannot plan"; worst case it emits best-effort windows with warnings. *Principle locked 2026-04-22.*

---

## 2. Scope boundaries

### In scope (initial motor)

- Computing charging windows to meet specific SoC targets at specific times.
- Multi-trip sequence awareness (plan across a list of upcoming trips).
- Hysteresis idle floor (ensure the car is kept above a floor SoC when idle).
- Absence filtering (don't plan charging during times the car is unavailable).
- Emergency charging when SoC is critically low.
- Delegation to charger auto-logic when spot price is below a threshold.
- Active-plan stickiness (avoid thrashing on small price updates).
- Stale-SoC detection with wake-up request.
- Split-plan charging (main cheap window + late top-up).
- Source-agnostic scheduled SoC targets (weekday-readiness patterns, etc., via `ScheduledTarget` or equivalent).
- Forecast-price uncertainty weighting (prefer nearer-term savings over distant speculation).
- Full configurability of every algorithmic tunable.
- Unit tests with full branch + line coverage.

### Out of scope (deferred)

- HA integration (coordinator, config flow, entities) — separate feature.
- Distance-to-SoC conversion helpers — adapter's job.
- Solar surplus awareness — adapter handles via synthetic cheap hours or threshold flips.
- Load balancing against other household loads — coordinator layer concern.
- Vehicle-to-grid / bidirectional charging — future iteration.
- Multi-car scheduling (sharing one charger) — coordinator concern.
- Intermediate public-charger stops during long trips — adapter handles via `energy_kwh`.
- Pluggable cost models (demand charges, fixed fees) — future iteration.
- Pluggable window-selection strategies (min-peak, prefer-daytime, prefer-night) — future iteration.
- Localization of warning strings — adapter handles at presentation.
- Observability / trace output — future iteration.
- Configuration-change hot-reload, hot-invalidation of stale plans — coordinator concern.

### Not a motor feature ever

- UI
- Persistence
- I/O of any kind
- Calendar integration
- Third-party API clients
- Vendor-specific adapter logic

---

## 3. Public contract (stable types)

The following types form the motor's stable public surface. Any addition or removal is a public-contract change that requires a full design revision.

### 3.1 Inputs

#### `PlannerInput` (frozen dataclass)

**Required — state:**
- `now: datetime` — current time, timezone-aware.
- `current_soc: float` — 0..100. Current state of charge.
- `soc_last_updated: datetime` — when `current_soc` was read, timezone-aware.
- `is_plugged_in: bool` — whether the car is currently plugged into the charger.

**Required — car specs:**
- `battery_capacity_kwh: float` — > 0.

**Required — charger specs:**
- `charger_efficiency: float` — in (0, 1].
- `charger_power_soc_steps: list[tuple[int, float]]` — piecewise-constant power-vs-SoC curve. Each tuple is `(soc_threshold_percent, max_power_kw)`; the motor applies the power cap from a given threshold upward until the next threshold. Sorted ascending. Must have at least one entry. Simple constant-power case: `[(0, 11.0)]`. Models battery-chemistry taper at high SoC.
- `charger_power_session_steps: list[tuple[int, float]]` — piecewise-constant power-vs-session-duration curve. Each tuple is `(minutes_since_session_start, max_power_kw)`. Same shape as above. Models heat-accumulation derate during sustained charging. For "no heat derate" (most conservative baseline): `[(0, <very_large_value>)]` or adapter supplies realistic values.

Effective power at any moment of charging = `min(step_lookup(charger_power_soc_steps, current_soc), step_lookup(charger_power_session_steps, minutes_elapsed_this_session)) * charger_efficiency`.

**Environmental modeling is adapter-layer (principle 12):** if the user's battery temperature, outdoor weather, or altitude affects charging speed, the adapter pre-composes `charger_power_soc_steps` and `charger_power_session_steps` to already account for current conditions. Motor takes whatever curves the adapter supplies.

**Required — user preferences:**
- `default_target_soc: int` — 0..100. Normal charge ceiling (e.g., 80 for battery-health). Used as the fill-up target when preparing for a trip and as the implicit `max_charge_soc` when a trip doesn't specify one. Never exceeded unless a trip explicitly overrides via `max_charge_soc` OR the computed required SoC exceeds this value (safety override with warning).
- `min_safety_soc: int` — 0..100. Emergency floor. Below this, the motor charges immediately regardless of price.
- `min_idle_soc: int` — 0..100. Hysteresis floor. When no imminent trip AND `current_soc < min_idle_soc`, the motor plans cheap charging up to this floor. Also raises the effective target for trips whose computed requirement is below this value.
- `default_trip_buffer_soc: int` — 0..100. Default for `Trip.required_soc_at_end` when the trip doesn't specify one. User's typical "don't arrive with less than this" preference (e.g., 15 — never arrive with less than 15%).

Recommended ordering: `min_safety_soc <= min_idle_soc <= default_target_soc`. Not enforced by the motor; document only.

**Optional — state:**
- `is_currently_charging: bool = False`
- `prices: list[PricePoint] = []`
- `trips: list[Trip] = []`
- `scheduled_targets: list[ScheduledTarget] = []` — time-bound SoC targets without an absence window (weekend readiness, morning readiness, etc.)
- `active_plan: ActivePlan | None = None`
- `charger_auto_threshold: float | None = None` — price threshold below which the motor delegates to charger auto-logic. `None` disables. Negative values raise `ValueError`.

**Optional — algorithm tunables (all have sensible defaults, all overridable):**
- `soc_max_age_minutes: int = 30`
- `min_session_minutes: int = 15` — must be ≥ 1.
- `wake_up_before_charge_minutes: int = 5`
- `active_plan_max_age_hours: int = 12`
- `near_window_seconds: int = 300`
- `soc_refresh_delay_seconds: int = 30`
- `idle_planning_horizon_hours: int = 24` — must be ≥ 1.
- `default_charge_complete_buffer_minutes: int = 20` — minutes by which charging must be complete before every trip's start. Treats the trip's effective planning deadline as `trip.start - buffer`. **Motor always respects this buffer** — it is never "eaten" by the motor. If there is insufficient time to meet target within the buffered deadline, motor plans up to `trip.start - buffer` and reports the shortfall in `TripResult` (status `PARTIAL` or `INFEASIBLE`) plus warning `INSUFFICIENT_TIME_WITH_BUFFER`. The adapter/user decides whether to loosen the buffer. Global only in this iteration; per-trip override deferred (YAGNI). Actual absence window stays `[trip.start, trip.end)`.
- `simulation_step_minutes: int = 6` — resolution of the forward charging simulation in `hours_to_charge` (lower = more accurate, more compute). Kept configurable for future tuning.

**Optional — price intelligence:**
- `forecast_markup_base_percent: float = 5.0` — flat markup applied to forecast-flagged prices for window selection (not for cost estimates).
- `forecast_markup_per_hour_percent: float = 0.2` — additional markup per hour ahead, for forecast prices.

### 3.2 Domain types

#### `PricePoint` (frozen dataclass)

- `start: datetime` — timezone-aware; start of the one-hour slot.
- `price_total: float` — in caller's chosen currency per kWh; never interpreted by the motor.
- `is_forecast: bool = False` — whether this price is a forecast (uncertain) or a known/actual value. Drives forecast-markup logic.
- `source: str = "nordpool"` — advisory; not used by motor.

#### `Trip` (frozen dataclass) — proposed revised shape

A scheduled trip that makes the car unavailable for charging during `[start, end]` and optionally specifies SoC requirements at departure and return.

- `start: datetime` — required; departure time, timezone-aware.
- `end: datetime` — required; return time, timezone-aware.
- `energy_kwh: float` — required (no default); >= 0. Energy expected to be consumed during the trip. Used to compute expected SoC at return as the starting SoC for the next gap's planning. If caller has no estimate, pass 0 explicitly (motor treats trip as a pure deadline with no SoC drop).
- `required_soc_at_start: int = 0` — 0..100. Minimum SoC the user demands at departure (the "must-have" level; e.g., "I need at least 60% to do this trip").
- `required_soc_at_end: int = 0` — 0..100. Minimum SoC the user wants at return ("buffer" — no arrival with 1% left; typically 10-20%). Motor adds this + `energy_kwh`-derived consumption to compute the actual start-time requirement, taking the MAX of `required_soc_at_start` and `(required_soc_at_end + consumption)`.
- `max_charge_soc: int | None = None` — 0..100 or None. Per-trip **upper limit** on how high the motor is allowed to fill this trip. `None` defers to `default_target_soc`. If the computed required SoC exceeds `max_charge_soc`, motor emits a warning and honors the required value anyway (safety wins over ceiling).
- `description: str = ""` — advisory; appears in warnings.

Validation: `end >= start`. All SoC fields in `[0, 100]`. `energy_kwh >= 0`.

**Derived effective target** (what motor aims for at trip start):
```
consumption_soc   = kwh_to_soc_percent(trip.energy_kwh, battery_capacity_kwh)
buffer_at_start   = min(FULL_TARGET_SOC, trip.required_soc_at_end + consumption_soc)
mandatory_at_start = max(trip.required_soc_at_start, buffer_at_start, min_idle_soc)

cap = trip.max_charge_soc if trip.max_charge_soc is not None else default_target_soc
effective_target = min(cap, max(mandatory_at_start, cap))
# Simpler: effective_target = min(max(mandatory_at_start, cap), cap) = cap if mandatory ≤ cap, else motor plans to cap and reports shortfall.
```

In plain English: **the cap is hard.** Motor plans up to `cap` (providing buffer up to the ceiling when mandatory is lower) but never above. If `mandatory_at_start > cap` (the trip demands more than the cap allows), motor plans to `cap`, marks the trip as `PARTIAL` or `INFEASIBLE` in `TripResult`, and emits a `TRIP_REQUIRED_EXCEEDS_CAP` warning. **Motor never overrides the user's cap** — it is the user's / adapter's responsibility to decide whether to raise the cap, accept an under-charged trip, or reschedule. *Principle 13 applies: best-effort within constraints, never breaks them.*

#### `ScheduledTarget` (frozen dataclass)

A time-bound SoC target without an absence window. Used for patterns like "be at 90% by Saturday 07:00" where the car isn't actually going anywhere at that moment; it should just be charged by then.

- `at: datetime` — required; target deadline, timezone-aware.
- `target_soc: int` — required; 0..100.
- `max_charge_soc: int | None = None` — optional per-target cap override, same semantics as `Trip.max_charge_soc`.
- `description: str = ""`

Validation: `0 <= target_soc <= 100`.

#### `ChargeWindow` (frozen dataclass, immutable)

A planned window during which the motor says "charge during this time".

- `start: datetime`
- `end: datetime`
- `target_soc: int` — SoC aimed for by window end.
- `expected_kwh: float`
- `expected_cost: float` — in input prices' currency.
- `avg_price: float` — raw (unmarkedup) average price across the window.
- `is_top_up: bool = False` — whether this is the late top-up leg of a split plan.
- `requires_wakeup: bool = False` — whether the consumer should emit a pre-window wake action.

#### `PlannerAction` (frozen dataclass)

A side-effect instruction emitted by the motor for the consumer to execute.

- `action_type: ActionType` — see below.
- `execute_at: datetime`
- `params: dict` — shape depends on `action_type`. Documented per-action schema in the `ActionType` class docstring.

#### `ActionType` (enum)

- `START_CHARGING` — params `{}`.
- `STOP_CHARGING` — params `{}`.
- `WAKE_UP_CAR` — params `{}`.
- `SET_CHARGE_LIMIT` — params `{"soc_limit": int (0..100)}`.
- `REQUEST_SOC_REFRESH` — params `{}`.

#### `ActivePlan` (frozen dataclass)

Persisted plan state that callers pass back in on subsequent ticks for stickiness.

- `planned_at: datetime` — when the plan was built.
- `windows: list[ChargeWindow]` — chronological.
- `for_first_trip_start: datetime | None = None` — the earliest trip the plan was built for. Used to invalidate the plan when that trip has passed.

### 3.3 Outputs

#### `WarningCode` (enum)

Motor-emitted warning codes. Every warning is a structured `PlannerWarning` with a code; no free-form text (principle 11).

- `TRIP_TARGET_SOC_OUT_OF_RANGE` — trip's `required_soc_at_start` or `required_soc_at_end` outside [0,100]; trip skipped.
- `TRIP_ENERGY_NEGATIVE` — trip's `energy_kwh < 0`; skipped.
- `TRIP_END_BEFORE_START` — trip's `end < start`; skipped.
- `TRIP_IN_PAST` — trip's `start <= now`; treated as ongoing/past; skipped from planning.
- `TRIP_OVERLAP_SKIPPED` — overlapping trips; later one skipped.
- `TRIP_ENERGY_EXCEEDS_CAPACITY` — `energy_kwh > battery_capacity_kwh`; post-trip SoC clamped to 0.
- `TRIP_BUFFER_UNREACHABLE` — even at 100% departure, arrival SoC is below `required_soc_at_end`; plan assumes best-effort.
- `TRIP_REQUIRED_EXCEEDS_CAP` — computed required SoC exceeds `max_charge_soc`; motor honors cap, trip is partial/infeasible. Adapter decides next step.
- `SCHEDULED_TARGET_IN_PAST` — scheduled target at `at <= now`; skipped.
- `DUPLICATE_PRICE_POINT` — duplicate `PricePoint` start times; first kept.
- `INSUFFICIENT_PRICE_DATA` — fewer price points than needed; best-effort fallback.
- `NO_CONTIGUOUS_WINDOW` — no contiguous hour run matches required duration; best-effort fallback.
- `EMPTY_PRICE_RANGE` — price range filter returned no points; cost estimate defaults to 0.
- `INSUFFICIENT_TIME_WITH_BUFFER` — required duration exceeds available time given `default_charge_complete_buffer_minutes`; motor honors buffer, trip is partial/infeasible. Adapter decides next step.
- `INFEASIBLE_TRIP_CHAIN` — cumulative trip energy exceeds total charging capacity across available gaps; best-effort per gap.
- `ACTIVE_PLAN_INVALIDATED_TRIP_SET_CHANGED` — trips differ from the set the active plan was built for; replanning forced.
- `ACTIVE_PLAN_INVALIDATED_EXPIRED` — active plan exceeded `active_plan_max_age_hours`.
- (extend as needed; every new emitter adds its code here)

#### `PlannerWarning` (frozen dataclass)

- `code: WarningCode`
- `subject: Trip | ScheduledTarget | PricePoint | None = None` — reference to the offending object when applicable. Callers match on identity to surface in UI.
- `params: dict = field(default_factory=dict)` — structured context. Values by code; documented alongside each code. No free-form English.

#### `TripResult` (frozen dataclass) — per-trip analysis

Part of `PlannerOutput.trip_results` when trips were planned. Carries the motor's computed view of each trip. **Pinned for this round:** only status and computed SoC figures; no advisory output (see §10b — the future "suggestions" work is explicitly deferred until the data-shape is proven in practice).

- `trip: Trip` — reference to the input trip.
- `status: TripResultStatus`
- `planned_soc_at_start: float` — SoC the motor projects at `trip.start`, given the planned windows.
- `expected_soc_at_end: float` — derived arrival SoC = `max(0, planned_soc_at_start - kwh_to_soc_percent(trip.energy_kwh, battery_capacity_kwh))`.
- `end_buffer_margin: float` — `expected_soc_at_end - trip.required_soc_at_end`. Negative = under buffer; positive = over.

#### `TripResultStatus` (enum)

- `FULLY_MET` — `planned_soc_at_start >= computed_mandatory`, and arrival honors buffer.
- `PARTIAL` — `planned_soc_at_start` covers at least `required_soc_at_start` but arrival is under `required_soc_at_end`, or the target was reduced because of cap/time.
- `INFEASIBLE` — motor could not meet `required_soc_at_start` even with best-effort windows.

#### `PlanReason` (enum)

- `SCHEDULED_TRIP` — plan covers one or more upcoming trips.
- `BELOW_IDLE_FLOOR` — no upcoming trips, but SoC is below `min_idle_soc`; planning idle fill.
- `MIN_SOC_SAFETY` — critical SoC; charging immediately.
- `NO_TRIPS_NO_NEED` — no trips AND SoC at or above idle floor; nothing to do.
- `SOC_ALREADY_SUFFICIENT` — every upcoming trip is covered by the SoC chain.
- `CAR_NOT_PLUGGED_IN` — nothing to do while car is disconnected.
- `STALE_SOC_NEEDS_WAKEUP` — SoC reading too old; wake car and request refresh.
- `INSUFFICIENT_TIME` — can't meet a deadline; best-effort max charge.
- `CHARGER_HANDLES_LOW_PRICE` — delegating to charger's native auto-logic.
- `ACTIVE_PLAN_CONTINUES` — following an existing valid plan.
- `SESSION_TOO_SHORT` — session would be too brief; skipping.

#### `PlannerOutput` (frozen dataclass)

- `should_charge_now: bool` — true iff any window in `windows` covers `now`.
- `reason: PlanReason`
- `feasibility: Feasibility` — derived from `trip_results`; see enum below.
- `windows: list[ChargeWindow]` — chronological, may be empty.
- `actions: list[PlannerAction]` — chronological, may be empty.
- `next_trip: Trip | None` — the earliest trip this plan concerns.
- `trip_results: list[TripResult]` — one entry per planned trip, chronological; empty if no trips were planned.
- `warnings: list[PlannerWarning]` — structured; never free-form text (principle 11).

#### `Feasibility` (enum)

- `FULL` — every trip is `FULLY_MET` and (when implemented) safety is guaranteed.
- `PARTIAL` — at least one trip is `PARTIAL` but none `INFEASIBLE`.
- `INFEASIBLE` — at least one trip is `INFEASIBLE`.

---

## 4. Functional requirements

### 4.1 Multi-trip planning

**R-MT-1.** The motor accepts a list of upcoming trips and considers every trip that starts in the future and is non-malformed.

**R-MT-2.** Trips may be passed in any order. The motor sorts internally by `start` time.

**R-MT-3.** For each trip, the motor plans charging windows in the **gap** between the previous trip's end (or `now` if the first trip) and this trip's start, so the expected SoC at trip start meets `max(trip.target_soc, min_idle_soc, any ScheduledTarget.target_soc deadlines within this gap)`.

**R-MT-4.** Starting SoC for each gap is the **expected SoC at the previous trip's end**, computed as `max(0, prev_effective_target - kwh_to_soc_percent(prev_trip.energy_kwh, battery_capacity_kwh))`. For the first gap, starting SoC is `current_soc`.

**R-MT-5.** When `trip.energy_kwh > battery_capacity_kwh`, motor emits a warning ("trip energy exceeds battery capacity") and clamps the post-trip SoC to 0.

**R-MT-6.** Overlapping trips: motor skips the later-started trip with a warning naming both trips. Trips with identical `start` times: the one with the later `end` wins (deterministic tie-break); a warning names the skipped trip.

**R-MT-7.** Trips that start before `now` (in-progress or past) are filtered out with a warning. Motor does not plan for in-progress trips.

**R-MT-8.** If the cumulative energy required by the trip chain exceeds the total charging capacity available in all gaps, the motor emits a summary warning ("trip chain is infeasible; planning best-effort per gap"). It does NOT refuse to plan; it plans best-effort per gap.

**R-MT-9.** The motor must detect that `trips` in the current call differ from `trips` implicitly assumed by the `active_plan`. If the trip set has changed in a way that makes the active plan unsafe, the motor invalidates the plan and replans. Specifically: if any new trip exists inside a planned window's time range, or if any trip the plan was built for is now missing, invalidate. *[SAFETY CRITICAL — flagged by edge-case review.]*

### 4.2 Idle-floor hysteresis

**R-IF-1.** When no upcoming trips exist and `current_soc >= min_idle_soc`, the motor returns `NO_TRIPS_NO_NEED` with no windows.

**R-IF-2.** When no upcoming trips exist and `current_soc < min_idle_soc`, the motor plans a cheap-window charge up to `min_idle_soc`. Deadline is `min(now + idle_planning_horizon_hours, last_price_point + 1h)`. Returns `BELOW_IDLE_FLOOR`.

**R-IF-3.** The **effective target** for any trip's gap planning is `max(trip.target_soc, min_idle_soc, any applicable ScheduledTarget.target_soc)`. If all upcoming trips' target_socs are already at or below `min_idle_soc`, the idle floor dominates.

**R-IF-4.** `min_idle_soc > default_target_soc` is legal; it forces split-plan behavior for every trip. Documented; not enforced against.

**R-IF-5.** `min_idle_soc < min_safety_soc` is legal but effectively useless (safety branch fires first). Documented.

### 4.3 Scheduled targets (source-agnostic weekday patterns)

**R-ST-1.** `scheduled_targets` is a separate list of time-point SoC targets without an absence window. Use case: "be at 90% by Saturday 07:00" without a trip.

**R-ST-2.** During planning, the motor treats each `ScheduledTarget` as a deadline inside the relevant gap. If a gap's end has a trip AND a scheduled target occurs inside the gap, the gap's effective target is `max(trip.target_soc, min_idle_soc, max scheduled_target.target_soc inside the gap)`.

**R-ST-3.** `ScheduledTarget` is the motor's mechanism for supporting weekday patterns, seasonal adjustments, manual overrides, and similar. The **adapter** generates these — the motor has no weekday logic, no recurrence logic, no pattern logic. *[User requirement: weekday-weighting should be supported; adapter responsibility.]*

**R-ST-4.** A scheduled target that is already "past" (at < now) is filtered out with a warning.

### 4.4 Absence filtering

**R-AF-1.** When searching for cheapest contiguous charging windows, the motor excludes any price point whose one-hour slot overlaps the absence window `[trip.start, trip.end)` of any trip.

**R-AF-2.** A price point starting exactly at `trip.end` is NOT in the absence window (half-open interval) — the first chargeable hour immediately after a trip is available.

**R-AF-3.** Absence filtering applies to every gap's window search, including split-plan main and top-up searches.

### 4.5 Emergency charging (critical SoC)

**R-EC-1.** When `current_soc < min_safety_soc`, the motor emits a `START_CHARGING` action at `now` and returns `MIN_SOC_SAFETY`. Price is ignored.

**R-EC-2.** Emergency charge window ends when the car reaches `default_target_soc` (or earlier if car is unplugged).

### 4.6 Charger auto-delegation

**R-CAD-1.** If `charger_auto_threshold` is not `None` AND the current hour's raw price is below the threshold, the motor returns `CHARGER_HANDLES_LOW_PRICE` with no windows. The charger is expected to start autonomously.

**R-CAD-2.** `charger_auto_threshold = None` disables the branch (safe default; not all chargers have this feature).

**R-CAD-3.** Negative thresholds raise `ValueError`.

### 4.7 Active-plan stickiness

**R-AP-1.** When an `ActivePlan` is valid per §R-AP-2..5, the motor follows it without replanning.

**R-AP-2.** A plan is valid if: age ≤ `active_plan_max_age_hours` AND `now` is inside some window OR within `near_window_seconds` before one.

**R-AP-3.** `plan.for_first_trip_start` is in the past → invalidate (the plan's lead trip has departed).

**R-AP-4.** Trip-set change as specified in §R-MT-9 → invalidate.

**R-AP-5.** When the active plan contains multiple windows (multi-trip plan), the motor reports `should_charge_now = True` only when `now` is inside some window; between windows, `should_charge_now = False`. The plan remains valid during gaps.

### 4.8 Stale SoC

**R-SS-1.** If `now - soc_last_updated > soc_max_age_minutes`, the motor returns `STALE_SOC_NEEDS_WAKEUP` with actions `WAKE_UP_CAR` (at `now`) and `REQUEST_SOC_REFRESH` (at `now + soc_refresh_delay_seconds`).

**R-SS-2.** Stale SoC takes precedence over normal planning but NOT over critical SoC. (Semi-stale data might still indicate critical safety — TBD. Current decision: critical wins only if stale-SoC was already fresh enough to read as critical, otherwise we wake first. Documented.)

### 4.9 Split-plan for high SoC targets

**R-SP-1.** When `effective_target > default_target_soc`, the motor produces two windows per gap: (a) main window filling to `default_target_soc` during the cheapest contiguous hours, and (b) top-up window filling from `default_target_soc` to `effective_target` immediately before the gap's deadline.

**R-SP-2.** The top-up window emits a `SET_CHARGE_LIMIT` pre-action at `window.start - wake_up_before_charge_minutes` to wake the car.

### 4.10 Session-too-short skip

**R-ST-1.** When the required duration is below `min_session_minutes`, the motor skips the session with a warning. Returns `SESSION_TOO_SHORT`.

### 4.11 Insufficient-time best-effort

**R-IT-1.** When a trip's deadline is closer than the hours needed, the motor schedules a max-power charge from `gap_start` to the deadline with a warning.

---

## 5. Price intelligence

### 5.1 Sliding forecast uncertainty (user requirement)

**R-PF-1.** Price selection (not cost estimation) uses an **adjusted price**:
```
adjusted = raw_price * (1 + markup / 100)
markup = forecast_markup_base_percent + hours_ahead * forecast_markup_per_hour_percent   (if is_forecast)
markup = 0   (if is_forecast is False)
```

**R-PF-2.** Window search compares by `adjusted`; cost outputs (`expected_cost`, `avg_price` on `ChargeWindow`) use raw prices.

**R-PF-3.** Default values: base 5%, per-hour 0.2%. At 1 day: 9.8% markup. At 7 days: 38.6%. Callers tune as needed.

**R-PF-4.** Rationale: "we don't bet on 2% a week out; maybe on 20% a couple of days out" (translated) — longer forecast horizons need bigger payoff to be preferred over nearer-term options.

### 5.2 Currency-agnostic

**R-PC-1.** Prices are opaque floats. Motor propagates currency through math without interpretation.

**R-PC-2.** Caller is responsible for consistent units across a single call. Mixing currencies within one call is undefined behavior.

---

## 6. Validation requirements

### 6.1 Fail-fast (raise `ValueError`)

Invariants violated → fail fast at `plan()` entry:

- Any datetime field missing `tzinfo`.
- `battery_capacity_kwh <= 0`.
- `charger_power_kw <= 0`.
- `charger_efficiency not in (0, 1]`.
- `current_soc not in [0, 100]`.
- `default_target_soc not in [0, 100]`.
- `min_safety_soc not in [0, 100]`.
- `min_idle_soc not in [0, 100]`.
- `charger_auto_threshold < 0` (when not `None`).
- `min_session_minutes < 1`.
- `idle_planning_horizon_hours < 1`.

### 6.2 Skip-with-warning (don't abort)

Data-quality issues per row → skip the row, keep planning:

- Trip with `target_soc` out of `[0, 100]` → skip, warn naming trip.
- Trip with `energy_kwh < 0` → skip, warn.
- Trip with `end < start` → skip, warn.
- Trip with `start < now` (past or in-progress) → skip, warn.
- Trip overlap → skip later trip (tie-break by later `end`), warn naming both.
- Duplicate `PricePoint` starts → keep first, skip rest, warn.
- `ScheduledTarget` at `< now` → skip, warn.
- `energy_kwh > battery_capacity_kwh` → accept but warn and clamp post-trip SoC to 0.

---

## 7. Edge cases (comprehensive enumeration)

All of the following must have explicit, documented, tested behavior:

### 7.1 Numeric boundaries

- `current_soc == 0`, `current_soc == 100`.
- `current_soc == min_safety_soc` exactly (just-above-critical; no emergency).
- `current_soc == min_idle_soc` exactly (no idle-fill).
- `current_soc == required_soc` exactly (sufficient; no plan).
- `target_soc == 0`, `target_soc == 100`.
- `energy_kwh == 0`.
- `charger_efficiency == 1.0` exactly.
- `min_idle_soc == 0`, `min_idle_soc == 100`.
- `min_safety_soc > min_idle_soc`, `min_idle_soc > default_target_soc` (legal; document).
- `charger_auto_threshold == 0.0` (vs. `None`).

### 7.2 Time boundaries

- Trip with `end == start` (zero duration) — handled how? Recommend: allow, treat as pure deadline with no absence window; adapter uses this for weekday targets if `ScheduledTarget` is not preferred.
- Trip end exactly at next trip start (gap of size 0) — valid; no window planned there.
- Trip start exactly at `now`.
- Trip end exactly at `now`.
- DST transitions inside trips or windows — no impact (UTC internals).
- Extremely long trip (days) — absence filter still works.

### 7.3 Price-data shape

- Empty `prices` list.
- Prices covering only part of the planning horizon.
- Prices with gaps (non-contiguous hours).
- Prices out of order (motor sorts).
- Prices with identical start times (dedupe).
- Negative prices (grid-support scenario) — accept.
- All prices equal (no distinct "cheapest") — deterministic pick (first-found).

### 7.4 Trip/target combinations

- Zero trips.
- Single trip in the future.
- Ten trips in 24 hours.
- Trip with `energy_kwh == battery_capacity_kwh` exactly.
- Two trips with identical start (tie-break).
- Three trips chained where each ends below `min_safety_soc`.
- `scheduled_targets` at the boundary of a trip's gap.
- `scheduled_targets` inside a trip's absence window (impossible — skip with warning).

### 7.5 Active-plan combinations

- Plan built for 3 trips; 1st completed; motor sees current SoC reflects post-trip.
- Plan built; new trip appears → invalidate (R-MT-9).
- Plan built; trip removed from input → invalidate.
- Plan with past-window and future-window; `now` between them → follow the plan (no charge now, window later).
- Plan's `for_first_trip_start` passed but later windows still future → invalidate (lead trip gone).
- Plan exactly at age `active_plan_max_age_hours`.

### 7.6 Tunable extremes

- `soc_max_age_minutes == 0` → always stale.
- `min_session_minutes == 1` (boundary).
- `wake_up_before_charge_minutes > gap_duration` → action lands before gap starts (consumer must handle out-of-order `execute_at`).
- `near_window_seconds == 0`.
- `active_plan_max_age_hours == 1`.
- `idle_planning_horizon_hours == 1` (boundary).

---

## 8. Test coverage requirements

**R-TC-1.** Every decision branch of `plan()` has at least one test.

**R-TC-2.** Every `ActionType` is emitted in at least one test that asserts the action's `params` dict shape.

**R-TC-3.** Every invariant check in §6.1 has a test confirming the `ValueError` is raised with the correct field named.

**R-TC-4.** Every skip-with-warning case in §6.2 has a test confirming the warning is emitted with the offending row named.

**R-TC-5.** Every edge case in §7 has a test.

**R-TC-6.** Multi-trip SoC chain correctness has tests covering:
- 2 trips, first target met, second needs charging after first's return.
- 3 trips, infeasible chain, best-effort emitted.
- Trip with `energy_kwh > target_soc` (clamping case).

**R-TC-7.** Scheduled target combination tests:
- Target inside a trip gap — raises effective target.
- Target alongside a trip in the same gap — max of both.

**R-TC-8.** Forecast uncertainty tests:
- Two equal-price windows, one forecast one not — motor picks non-forecast.
- Near-term forecast vs. distant forecast of equal price — motor picks near.
- User sets markup=0 — behavior matches pre-forecast-markup version.

**R-TC-9.** Target: **100% line + branch coverage** via `coverage.py`.

**R-TC-10.** Tests use `unittest.TestCase`; discovered by the project's canonical test command.

---

## 9. Performance requirements

**R-PERF-1.** `plan()` runtime ≤ 10 ms at realistic inputs (P ≤ 168 price points, N ≤ 20 trips, M ≤ 20 scheduled targets) on typical hardware.

**R-PERF-2.** Algorithm complexity: O((P + N × M) × N) worst case; O(P + N) amortized typical.

**R-PERF-3.** Motor is re-entrant; concurrent calls with different inputs are safe without external synchronization.

**R-PERF-4.** No allocation-in-loop patterns that blow GC. Frozen dataclasses only.

---

## 9a. Ratified decisions log (snapshot 2026-04-22)

Authoritative record of every decision locked in this iteration. All items below are **closed**; any re-opening requires explicit user request.

| Item | Decision | Notes |
|---|---|---|
| `CalendarEvent` → `Trip` rename | LOCKED | Source-agnostic |
| `EventType` enum | REMOVED | No TRIP/CHARGED_BY distinction in motor |
| `NO_CHARGE` event type | REMOVED | Adapter uses absence-filter mechanism |
| Motor owns distance conversion | NO | Adapter does `km→SoC`; motor only sees SoC/kWh |
| Hardcoded constants (battery, charger) | REMOVED | All are required PlannerInput fields (revision 3 fix) |
| Algorithm-policy as module constants | REMOVED | All moved to PlannerInput optional fields with defaults (revision 4 fix) |
| Trip.energy_kwh required (no default) | LOCKED | Algorithm-review blocker |
| Trip SoC fields split (at_start, at_end) | LOCKED | required_soc_at_start + required_soc_at_end |
| Trip.max_charge_soc per-trip cap | LOCKED | None = use default_target_soc; safety overrides cap |
| default_trip_buffer_soc global | LOCKED | Default for trip.required_soc_at_end when absent |
| min_idle_soc hysteresis floor | LOCKED | Required field; distinct from min_safety_soc |
| BELOW_IDLE_FLOOR branch | LOCKED | No-trips + below-floor → plan cheap fill to floor |
| ScheduledTarget separate type | LOCKED | Per §10 decision 1; adapter generates for weekday patterns |
| Multi-trip planning with SoC chain | LOCKED | See §4.1; algorithm bugs fixed per round 2 review |
| Trip-set-change detection | LOCKED | Invalidates active plan; safety critical |
| Active-plan `for_trip_start` rename | LOCKED | → `for_first_trip_start` |
| Overlap-later-trip skip + warning | LOCKED | Later-start wins skip; tie-break by later end |
| Empty prices → best-effort + warning | LOCKED | Motor never refuses to plan |
| Negative prices | SUPPORTED | Grid-support scenario; motor exploits them |
| Forecast uncertainty markup | LOCKED | 5% base + 0.2%/h default; selection-only (cost uses raw) |
| CS-A dual-curve (SoC + session steps) | LOCKED | Piecewise; min(both); adapter pre-composes for environment |
| Temperature modeling in motor | NO | Principle 12; adapter-layer concern |
| default_charge_complete_buffer_minutes | LOCKED | 20-min global default; per-trip deferred |
| Insufficient-time may spend buffer | LOCKED | Extends to trip.start with warning |
| NEVER return text (codes + params only) | LOCKED | Principle 11 |
| Structured warnings (PlannerWarning) | LOCKED | Code + subject + params; no message strings |
| TripResult output | LOCKED | Status + SoC figures only (no advisory) |
| Feasibility output flag | LOCKED | Derived from trip_results |
| Advisory "Suggestion" output | PINNED | Deferred until data-shape is proven; name TBD |
| plan_guarantees_min_safety (B18) | DEFERRED | Design TBD; combinations need more thought |
| Global max_charge_soc cap (B13) | REJECTED | Would block smart long-trip planning |
| force_top_up_threshold (B14) | REJECTED | Covered by required_soc_at_end |
| DM-A vs DM-B data model | LOCKED — DM-B | `AbsenceWindow` + `ChargeTarget` separate types; adapter links them for trips |
| `max_charge_soc` is hard cap | LOCKED | Motor never overrides; shortfall reported in TripResult |
| `default_charge_complete_buffer_minutes` respected always | LOCKED | Motor never eats buffer; shortfall reported in TripResult |
| Motor is declarative (plans within constraints, reports infeasibility) | LOCKED (principle) | Motor never breaks user constraints on its own; adapter decides loosening |
| Final pass on field/enum names for clarity | PENDING | Once all requirements are locked, do a naming sweep before implementation |

## 10. Open decisions — CLOSED LOG

All original items locked or rejected. Historical record only:

| # | Decision | Outcome |
|---|---|---|
| 1 | Separate type for weekday patterns | DM-B locked: `ChargeTarget` handles it |
| 2 | `energy_kwh` required or default-to-0 | **Required, no default** |
| 3 | Post-last-trip trailing idle-fill | **Deferred** (next tick catches it) |
| 4 | Forecast markup defaults | **Accepted** (5% + 0.2%/h) |
| 5 | Trip-set-change detection | **In scope** (safety critical) |
| 6 | Cumulative-feasibility precheck | **Best-effort + summary warning** |
| 7 | Split SoC fields at_start vs. at_end | **Yes** |
| 8 | Per-`ChargeTarget` `max_charge_soc` cap | **Yes — hard cap, no override** |
| 9 | Global `default_trip_buffer_soc` preference | **Yes** |
| 10 | Safety override for cap breach | **Rejected** — cap is hard; shortfall reported instead |

**No open decisions remain.** Requirements.md is LOCKED pending the naming-pass (cosmetic) and design-doc revision 3 (structural).

---

## 10b. Brainstorm — additional concepts to consider (user decision: ACK or REJECT each)

The following are proposed concepts that extend the motor's flexibility. None are in scope until user ACKs them. All are motor-level (not adapter-level); otherwise they'd be HA-integration concerns.

### Per-trip optional fields

| ID | Concept | Description | Recommend |
|---|---|---|---|
| B1 | `Trip.allow_precondition: bool` | Emit a PRECONDITION action N minutes before start (heat/cool cabin). Requires new ActionType. | Defer — HA-integration territory |
| B2 | `Trip.delay_tolerance_minutes: int` | "I can tolerate starting N minutes late if it saves money." Motor may plan a slightly-later departure if cheaper. | Defer — changes trip semantics, user would need to accept shifted start |
| B3 | `Trip.alternate_starts: list[datetime]` | "I could leave at 07:00 OR 08:30; pick cheaper." Multi-plan comparison. | Defer — complex |
| B4 | `Trip.priority: int` | 1..10 importance. Motor deprioritizes low-priority trips when resources are constrained. | Defer — no clear win |
| B5 | `Trip.cost_cap: float` | "Don't spend more than X on charging for this trip." Motor refuses to plan if cost exceeds. | Defer — rare need |
| B6 | `Trip.charge_during_trip_hint: bool` | "I'll public-charge mid-trip; don't try to get full SoC before departure." Overrides the `required_soc_at_end + energy_kwh` math. | Defer — adapter can pass `energy_kwh=net_of_midway_charge` instead |

### Global preferences

| ID | Concept | Description | Recommend |
|---|---|---|---|
| B7 | `no_charge_periods: list[AbsenceWindow]` | Explicit "never charge in these time ranges" (noise sensitivity, night-time quiet, etc.). Separate from Trip absence. | **ACK** — legitimate use case, low cost; reuses absence-filter machinery |
| B8 | `max_daily_kwh: float` | Hard cap on total kWh charged per 24h (battery longevity). | Defer — battery-health fine print; rare need |
| B9 | `min_rest_between_sessions_minutes: int` | Cooldown between charge sessions to reduce cycle wear. | Defer — battery chemistry detail |
| B10 | `preferred_window_strategy: Literal["cheapest", "prefer_night", "prefer_day", "earliest"]` | User picks a window-selection bias. | Defer — flexibility-audit flagged; keep "cheapest" for now |
| B11 | `soc_rounding_step: int` | Round target SoCs to nearest N% (default 5). | Defer — cosmetic |
| B12 | `default_trip_buffer_soc` | Global default for trip's `required_soc_at_end` | **ACK** — already added to §3.1 |

### Global limits

| ID | Concept | Description | Recommend |
|---|---|---|---|
| B13 | `max_charge_soc_global: int` | Hard upper cap; motor NEVER fills above this regardless of per-trip overrides. | **ACK** — legitimate "battery protection" hard limit; reasonable default = 100 (effectively no cap) but user can set 90 to ban 100% fills entirely |
| B14 | `force_top_up_threshold_percent: float` | If a trip's `required_soc_at_start` is within N% of `current_soc`, override session-too-short and charge anyway. Addresses your "21% vs 20% is not OK" concern. | **ACK** — directly addresses the razor-thin-margin concern; consider default 5% (if you're within 5% of required, charge anyway) |

### Reasoning / output features

| ID | Concept | Description | Recommend |
|---|---|---|---|
| B15 | `PlannerOutput.explains: list[str]` | Structured explanation of why the motor chose this plan. For debugging / user UI. | Defer — adapter can format `warnings` for explanation |
| B16 | `PlannerOutput.alternative_plans: list[PlannerOutput]` | Up to N alternative plans the motor considered. | Defer — too expensive |
| B17 | `PlannerOutput.feasibility: Literal["full", "partial", "infeasible"]` | Quick-read flag of whether plan fully meets every trip's requirements. | **ACK** — single boolean-ish field; small cost, clear signal to HA layer ("red badge if plan is partial") |
| B18 | `PlannerOutput.plan_guarantees_min_safety: bool` | True iff the plan ensures SoC stays above `min_safety_soc` at all times. | **ACK** — safety-critical signal; merges well with B17 |

### Data-model alternative

Your message hints that the current Trip/ScheduledTarget split might be wrong. Here's the alternative I see:

**Option DM-A (current):** `Trip` (absence + targets) + `ScheduledTarget` (targets only).

**Option DM-B (radical):** split further:
- `AbsenceWindow(start, end, energy_consumed_kwh = 0, description)` — pure "car unavailable" period.
- `ChargeTarget(at, required_soc, max_charge_soc = None, description)` — pure "want this SoC at this time".

Trip = pair of AbsenceWindow + ChargeTarget that adapter creates together. Motor receives them as separate lists.

**Pros of DM-B:**
- Even more agnostic. "AbsenceWindow" means any reason the car can't charge (trip, maintenance, quiet-hours) — not tied to "trips".
- Clean: consumption goes with absence (trip consumes energy), target goes with deadline (you want X at time Y).
- A charge target might not correspond to a trip (pure weekday pattern).
- An absence might not have a target (car in shop for repair; don't plan around SoC).

**Cons of DM-B:**
- Adapter complexity: for a normal trip, adapter creates TWO objects (absence + target) instead of one.
- Harder to keep them linked in warnings ("trip to work: X problem" vs. "absence to work: X, target at 07:00: Y").

**Recommendation:** **DM-B is cleaner architecturally**; worth the adapter complexity because:
1. Motor stays maximally agnostic (any "car can't charge" reason uses AbsenceWindow).
2. ChargeTarget covers ScheduledTarget naturally (same semantics; no need for two types).
3. Adapter gets to express exactly what it knows, without conflating concepts.
4. User's "trip is sometimes just a deadline" observation is honored directly.

If we go DM-B, the public contract becomes:
```python
PlannerInput(
    ...,
    absences: list[AbsenceWindow],   # time ranges when charging is impossible
    targets: list[ChargeTarget],      # SoC-at-time requirements
    # trips: removed
)
```

And a typical adapter for a real trip creates both: `AbsenceWindow(07:00, 17:00, energy_kwh=40)` + `ChargeTarget(at=07:00, required_soc=80, max_charge_soc=None)`.

**This is a fundamental contract choice — please decide DM-A or DM-B explicitly.**

---

## 11. Out-of-scope confirmations

The following will NOT be added to the initial motor:

- Pluggable window-selection strategies (cheapest-only for now).
- Pluggable cost models.
- Callback-based invalidation predicates.
- `PricePoint.confidence` field.
- `PlannerAction.params` typed union.
- Sub-hour pricing granularity (`PricePoint.duration_minutes`).
- Structured warning codes (enum + context dict).
- Carbon-intensity weighting.
- `target_soc_min` vs. `target_soc_preferred` on `Trip`.

All flagged for future iterations if concrete need emerges.

---

## Changelog

- **2026-04-22 (initial)** — consolidated requirements doc. Supersedes scattered requirements across design docs and chat transcripts.
- **2026-04-22 (afternoon update)** — added principles 11, 12, 13 (never-text, adapter-environmental-modeling, best-effort). Split SoC fields. Added max_charge_soc, default_trip_buffer_soc, default_charge_complete_buffer_minutes, CS-A dual-curve (charger_power_soc_steps + charger_power_session_steps). Replaced text-valued `warnings: list[str]` with structured `list[PlannerWarning]`. Added `WarningCode` enum, `TripResult`/`TripResultStatus`, `Feasibility`. Pinned advisory output for later.
- **2026-04-22 (evening update)** — DM-B locked: `AbsenceWindow` + `ChargeTarget` replace `Trip` + `ScheduledTarget`. `max_charge_soc` is hard cap (no safety override). `default_charge_complete_buffer_minutes` is always respected (motor never eats buffer). Motor is declarative — reports infeasibility but never breaks user constraints on its own. Names will be reviewed in a dedicated pass before implementation. No open decisions remain.
