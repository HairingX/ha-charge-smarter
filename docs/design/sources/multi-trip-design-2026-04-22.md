# Design: Multi-Trip Planning — Motor Redesign Round 2

> Kept as reference. Written on 2026-04-22; where it disagrees with `../decisions.md` or `../motor.md`, it is out of date. Planning gap by gap, as here, is replaced by D22.

- **Feature:** initial (continues from design round 1, not kept)
- **Date:** 2026-04-22
- **Workflow stage:** Stage 2 (design document) — awaiting Stage 3 multi-team review
- **Trigger:** user feedback after initial feature reached "motor complete". Two fundamental gaps were discovered that require redesign rather than incremental fix.

---

## Why this round

The first motor iteration planned for a **single upcoming trip** (or single `CHARGED_BY` deadline). Two user observations revealed structural issues:

1. **Single-trip myopia:** "*we need TRIPS in, not trip. Necessary to see, when we drive a lot, whether to charge today because the car is out driving all week.*" (translated) — planning for only the nearest trip ignores the far more important question of whether a sequence of trips is feasible without intermediate charging. If the car is away most of the week, the motor must fit charging into the short home-gaps between trips; if the trip AFTER next is a long one, the motor may need to start charging now even though the nearest trip's target is already met.

2. **Razor-thin margins:** "*the trip needs 20%, but it is not OK to skip charging when the car is at 21%*" (translated) — the motor's "SoC sufficient" check used the exact trip target, so a car at 21% with a 20% trip target was told "no charge needed", which no user would accept. A hysteresis floor (*min_idle_soc*) below which the motor always plans charging is needed independently of trips.

Both are public-contract changes. Both were missed by earlier review rounds because reviewers audited design conformance, not principle fit. This round replans the whole multi-trip contract with explicit scope.

---

## 2a. Problem statement

### What

Rework the planner contract and algorithm to:

- Accept a **list of upcoming trips** rather than a single calendar event.
- For each trip, plan charging so the required SoC is met by the trip's `start` time, using only time ranges where the car is available (not during any other trip's absence window).
- Account for **SoC consumption during a trip** — the motor must know how much SoC each trip costs so the next trip's starting SoC is realistic.
- Enforce a **hysteresis idle floor** (`min_idle_soc`) that sits between `min_safety_soc` and `default_target_soc`. When SoC dips below the floor without an imminent trip, the motor plans cheap charging back up to the floor.
- Keep the motor **source-agnostic** — no knowledge of calendars, distance, currency, or vehicle-specific wake behaviors.

### Why

- Users plan across days/weeks, not single trips. The motor must see the whole picture to avoid "plan was fine for Monday, got stuck Tuesday" outcomes.
- Battery protection: no one wants "needed 20%, had 21%, didn't charge, ran out mid-trip". Hysteresis is table-stakes.
- Principle fit: the earlier `CalendarEvent` type leaked a source assumption; `Trip` and a plural list are cleaner.

### Acceptance criteria

1. `PlannerInput.trips: list[Trip]` replaces `PlannerInput.events`. Each `Trip` has `start`, `end`, `target_soc`, `energy_kwh`, `description`.
2. Motor can return a `PlannerOutput` containing **multiple, chronologically-ordered `ChargeWindow`s** — one or more per trip gap, plus an optional idle-fill window if `min_idle_soc` is unmet with no upcoming trips.
3. Between-trip charging gaps are computed correctly: window candidates exclude price slots that overlap any trip's `[start, end]`.
4. `min_idle_soc` is a required `PlannerInput` field; its enforcement is documented and tested for all decision branches.
5. `should_charge_now` reflects whether **any** returned window covers `now`.
6. The motor rejects malformed inputs (naive datetimes, `end < start`, overlapping trips if we choose to enforce, etc.) with informative `ValueError`s or skip-with-warning — both behaviors documented.
7. Stage 3 multi-team review APPROVES unanimously, with findings either addressed in the design or explicitly escalated to the user.
8. All 100% line + branch coverage tests pass post-implementation.

---

## 2b. Affected components

### Types — full public surface after redesign

```python
@dataclass(frozen=True)
class Trip:
    """A scheduled trip with required SoC at departure and expected energy use.

    - ``start`` / ``end``: both required; trip is unavailable for charging
      during ``[start, end)``.
    - ``target_soc``: SoC in [0, 100] required at start.
    - ``energy_kwh``: energy consumed during the trip, >= 0. Motor uses
      this to compute the expected SoC at end (as the starting SoC for
      the next trip's planning). If the caller has no estimate, pass 0
      and the motor will treat the trip as a pure deadline (no SoC drop).
    """
    start: datetime
    end: datetime
    target_soc: int
    energy_kwh: float
    description: str = ""


@dataclass(frozen=True)
class PlannerInput:
    # State (required)
    now: datetime
    current_soc: float
    soc_last_updated: datetime
    is_plugged_in: bool

    # Car specs (required)
    battery_capacity_kwh: float

    # Charger specs (required)
    charger_power_kw: float
    charger_efficiency: float

    # User preferences (required)
    default_target_soc: int   # normal charge ceiling (e.g., 80)
    min_safety_soc: int       # emergency floor — charge NOW (e.g., 25)
    min_idle_soc: int         # hysteresis floor — plan cheap charge (e.g., 50)

    # Optional state
    is_currently_charging: bool = False
    prices: list[PricePoint] = field(default_factory=list)
    trips: list[Trip] = field(default_factory=list)
    active_plan: ActivePlan | None = None

    charger_auto_threshold: float | None = None

    # Algorithm tunables
    soc_max_age_minutes: int = 30
    min_session_minutes: int = 15
    wake_up_before_charge_minutes: int = 5
    active_plan_max_age_hours: int = 12
    near_window_seconds: int = 300
    soc_refresh_delay_seconds: int = 30
    idle_planning_horizon_hours: int = 24


@dataclass(frozen=True)
class PlannerOutput:
    should_charge_now: bool
    reason: PlanReason
    windows: list[ChargeWindow] = field(default_factory=list)  # chronological
    actions: list[PlannerAction] = field(default_factory=list) # chronological
    next_trip: Trip | None = None
    warnings: list[str] = field(default_factory=list)
```

`PlanReason` gains `BELOW_IDLE_FLOOR` (for no-trip idle-fill) and keeps the others. Semantic shifts:

- `SCHEDULED_TRIP` now means "at least one upcoming trip requires charging".
- `SOC_ALREADY_SUFFICIENT` means "all upcoming trips are covered by the current/expected SoC chain AND SoC is at or above the idle floor".
- `NO_TRIPS_NO_NEED` means "no upcoming trips AND SoC is at or above the idle floor".

### Files affected

- `custom_components/charge_smarter/charge_smarter/planner.py` — full rewrite of decision tree, helpers, window finders.
- `custom_components/charge_smarter/charge_smarter/__init__.py` — remove `CalendarEvent`, `EventType`; export `Trip`.
- `custom_components/charge_smarter/charge_smarter/test_planner.py` — full rewrite against the new contract (currently a stub awaiting this design).
- `docs/designs/2026-04-22-charge-planner-motor.md` — updated revision history pointing to this doc as the successor.
- `docs/features/initial/agent_notes.md` — update once design is locked.

Scaffold files (`__init__.py`, `config_flow.py`, `coordinator.py`, `manifest.json`, etc.) — unchanged. HA-integration work is still a separate future feature.

---

## 2c. Proposed algorithm

### Decision tree (top to bottom; first match wins)

1. **Not plugged in** → `CAR_NOT_PLUGGED_IN`.
2. **Active plan still valid** → `ACTIVE_PLAN_CONTINUES` (follow the plan).
3. **Stale SoC** → `STALE_SOC_NEEDS_WAKEUP` + wake/refresh actions.
4. **Critical SoC** (`current_soc < min_safety_soc`) → `MIN_SOC_SAFETY` + emergency charge NOW.
5. **Current price below `charger_auto_threshold`** → `CHARGER_HANDLES_LOW_PRICE`.
6. **No upcoming trips**:
   - **6a.** `current_soc >= min_idle_soc` → `NO_TRIPS_NO_NEED`.
   - **6b.** `current_soc < min_idle_soc` → plan idle fill to `min_idle_soc` with deadline `min(now + idle_planning_horizon_hours, end_of_price_horizon)` → `BELOW_IDLE_FLOOR`.
7. **Upcoming trips: build the multi-trip plan** (see algorithm below). If the plan is empty (every trip's required SoC is already met by the starting-SoC chain AND the idle floor is satisfied) → `SOC_ALREADY_SUFFICIENT`. Otherwise → `SCHEDULED_TRIP` with the collected windows and actions.

Session-too-short (`SESSION_TOO_SHORT`) and insufficient-time (`INSUFFICIENT_TIME`) are checked per-trip during the planning loop and can short-circuit a specific trip's plan.

### Multi-trip planning algorithm

**Inputs:** sorted-by-start list of trips, `current_soc`, `now`, prices, tunables.

**Pre-processing:**

1. Sort trips by `start`.
2. Validate each trip: `target_soc` in `[0, 100]`, `energy_kwh >= 0`, `end > start`. Skip malformed trips with a warning.
3. Validate no overlap between trips. If two trips overlap, **skip the later one** with a warning (the earlier wins). Adapter is expected to emit non-overlapping trips; the motor does not merge them.

**Main loop:**

```
expected_soc_at_gap_start := current_soc
gap_start := now
planned_windows := []
for each trip in sorted trips:
    gap_end := trip.start
    effective_target := max(trip.target_soc, min_idle_soc)
    soc_delta := effective_target - expected_soc_at_gap_start

    if soc_delta > 0:
        kwh_delta := soc_percent_to_kwh(soc_delta, battery_capacity_kwh)
        hours_needed := hours_to_charge(kwh_delta, charger_power_kw, charger_efficiency)

        if hours_needed * 60 < min_session_minutes:
            # Session-too-short; skip this trip (SoC is close enough)
            continue

        hours_available := (gap_end - gap_start).total_seconds() / 3600
        if hours_available < hours_needed:
            # Insufficient time; charge at max from gap_start to gap_end
            windows.append(best_effort_window(gap_start, gap_end, ...))
        else:
            # Find cheapest contiguous window inside [gap_start, gap_end]
            # that also excludes any absence overlap (there shouldn't be
            # any inside the gap, but absences from earlier trips that
            # straddle our gap boundary need to be filtered).
            # Split plan if effective_target > default_target_soc.
            windows.append(plan_for_gap(gap_start, gap_end, expected_soc_at_gap_start, effective_target))

    # Expected SoC at this trip's end = effective_target consumed by trip energy.
    soc_consumed := kwh_to_soc_percent(trip.energy_kwh, battery_capacity_kwh)
    expected_soc_at_gap_start := max(0.0, effective_target - soc_consumed)
    gap_start := trip.end

# Optional: after the last trip, if expected_soc_at_gap_start < min_idle_soc,
# add an idle-fill window (with horizon cap) so the car returns to the floor.
# TODO for Stage 3 review: confirm whether this post-last-trip idle-fill is
# desirable or overreach.
```

**Output:** a chronological list of `ChargeWindow`s covering all trips' pre-gaps (and optionally a trailing idle-fill). Actions are collected per window using `_actions_for_window`. `should_charge_now = any(w.start <= now < w.end)`. `next_trip = trips[0]`.

### Split-plan per trip

If a trip's `effective_target > default_target_soc`, the per-gap planning uses the existing split-plan machinery:

- Main window fills to `default_target_soc` in the cheapest contiguous hours of `[gap_start, deadline - top_up_hours)`.
- Top-up window fills from `default_target_soc` to `effective_target` immediately before `trip.start` (emits `SET_CHARGE_LIMIT` pre-window).

Split-plan interaction with multi-trip is straightforward because each trip plans in its own gap.

### Absence filtering

When searching for cheapest contiguous windows, price points whose hour overlaps **any trip's absence window** are excluded. This is already implemented via `_price_in_any_absence`.

Edge: a price point at `p.start = trip.end` is *not* in the absence window (half-open interval `[start, end)`), so the first chargeable hour after a trip is immediately available.

### Active-plan interaction

`ActivePlan.windows` may now contain **multiple** windows (carried over from a multi-trip plan). The `_active_plan_is_valid` logic already handles multiple windows via its `for w in plan.windows:` loop — no change needed. But:

- `active_plan.for_trip_start` referred to a single trip. With multi-trip plans, this field becomes "the earliest trip this plan was built for". Rename to `for_first_trip_start` or deprecate. **Decision point for Stage 3 review.**
- If a new trip is added after the plan was built, the plan may become inadequate. The motor currently follows the plan anyway (stickiness). A user might want to invalidate. **Decision point — out of scope for this revision; flag for future work.**

---

## 2d. Code-trace analysis (flows the redesign touches)

- `plan()` — decision tree expanded with idle-fill branches and multi-trip loop.
- `_next_trip()` — returns the earliest trip (unchanged from single-trip version except for naming).
- `_validate_trips()` — extended to check `energy_kwh >= 0`, `end > start`, and overlap between trips.
- `_find_cheapest_window()` — unchanged (already takes `trips` for absence filtering).
- `_plan_with_top_up()` — called per trip with per-trip expected starting SoC rather than `inp.current_soc`; signature changes to take `starting_soc: float`.
- `_plan_idle_fill()` — new helper for branch 6b and optional trailing idle-fill.
- `_required_soc_for_upcoming_events()` — deleted (multi-trip replaces it).

### Breakage points

- Any code (future adapter) consuming `PlannerOutput.windows` must handle a list of length ≥ 1 chronologically ordered. Current consumers: none (no HA layer yet). No backward-compat burden.
- `Trip.energy_kwh` is required; adapters that don't know energy use must pass 0. Document clearly.
- `active_plan.for_trip_start` semantic shift — only affects plans built by v2 motor consumed by v2 motor; no mixed-version concern.

---

## 2e. Risks and edge cases

### Trips-list shape risks

- **Trips out of order:** motor sorts internally. Warning on re-sort? *Decision: silent sort (adapters fix their own bug; motor is forgiving).*
- **Overlapping trips:** skip later with warning. Alternative: merge into a single trip. *Decision: skip — merging hides the adapter's data quality issue.*
- **Trip entirely in the past:** filter out with `_next_trip`-style `t.start > now`.
- **Trip partially in the past** (started before `now`, still ongoing): motor treats it as an active absence window; no planning for this trip itself (already departed). Is-plugged-in check in branch 1 probably covers it (car not home). *Decision: filter out; the motor doesn't plan for in-progress trips. Warning on ongoing trip.*
- **Empty trips list:** branch 6 handles it.

### SoC-chain risks

- **Trip energy exceeds target_soc:** adapter says "trip uses 50 kWh out of 80 kWh target". SoC at end = 80% - (50/battery*100). If battery is 60 kWh, SoC at end is 80 - 83 = -3%, clamped to 0. We charge from 0 next gap. *Decision: clamp to 0 with a warning ("trip energy exceeds target SoC; assuming SoC=0 at return").*
- **Expected SoC drops below `min_safety_soc` mid-chain:** the motor doesn't panic; it just plans for the next gap starting from the low SoC. Safety branch 4 would fire on the *next* `plan()` call when `current_soc` reflects that low value. *Decision: no special handling in the chain; safety branch handles it when it becomes real.*

### Idle floor risks

- **`min_idle_soc > default_target_soc`:** effective target = max(trip.target_soc, min_idle_soc) could exceed default_target_soc, triggering split-plan even for small trips. *Decision: allowed; user configured it that way. Document the interaction.*
- **`min_idle_soc < min_safety_soc`:** effectively disables the idle floor (safety branch fires first). Legal but pointless. *Decision: allowed; document.*
- **Idle-fill during price gap:** horizon cap prevents silent over-planning.

### Numeric / time risks

- Naive datetimes still rejected at plan entry (unchanged).
- Trip `end` exactly at next trip's `start`: no overlap, acceptable. Price points at that boundary: first point at `t1.end` is chargeable (half-open interval).
- Active-plan windows interacting with new trip that appears after the plan: *flagged for future work*.
- DST transitions inside a trip's absence window: UTC internals unaffected.

### Performance risks

- With N trips and P prices, per-gap window search is O(P_gap) where P_gap is the number of price points inside that gap. Total work = O(P) amortized across all gaps. Unchanged from single-trip performance.
- Trip overlap check is O(N²) worst case; N ≤ 50 per design bound, so acceptable (~2500 comparisons).
- Active-plan windows list: length = number of trips planned. Linear iteration; fine.

---

## 2f. Best-practice checklist

- [x] Library / HA separation — motor still has no HA imports.
- [x] Minimal over-engineering — algorithm is forward-iteration only; no optimizer or lookahead.
- [x] Performance — O(P) per call at realistic sizes.
- [x] Concurrency — still stateless and thread-safe.
- [x] Python 3.14 — PEP 604 unions, no deprecated features.
- [x] English throughout.
- [x] Type hints — full.
- [x] Runtime validation on all public-contract invariants.

---

## Open decision points for Stage 3 review

Teams are asked to take explicit positions on:

1. **`Trip.energy_kwh = 0` semantics:** is "adapter doesn't know" best modeled as 0 (motor assumes SoC doesn't drop), or as a separate sentinel (None? negative? a flag?)? Does making it required-but-allow-0 confuse adapters?
2. **Trip overlap handling:** skip-the-later vs merge vs raise `ValueError`. Motor's choice has real consequences for adapter behavior.
3. **Post-last-trip idle-fill:** after planning all trips, if expected-SoC-at-chain-end is below `min_idle_soc`, should the motor add a trailing idle-fill window (bounded by `idle_planning_horizon_hours`), or leave it to the next tick's branch 6b to notice?
4. **`active_plan.for_trip_start` field:** rename to `for_first_trip_start`, generalize to a list of trip starts, or drop entirely (plans are their own truth)?
5. **`should_charge_now` with multi-trip:** currently "any window covers now". Is there a case where we want "the planned window for the *current* planning gap covers now" (stricter)?
6. **Empty prices with multi-trip:** motor falls back to best-effort windows at `gap_start`. Acceptable, or should it refuse to plan (raise) when no price data is available?
7. **Trip in the past but still ongoing:** filter + warning? Reject?
8. **`min_idle_soc` interaction with `default_target_soc`:** what's the cleanest semantic when the user sets `min_idle_soc > default_target_soc`? (Current design honors the user config.)

---

## Stage 3 — Multi-team review request

Five review teams (Algorithm, Architecture, Code Trace, Performance, Edge-Case Hunt). Each operates in parallel. Each has mandate to **REJECT** if the design has a hole — this round requires more rigor than previous rounds, which missed two residual prototype-isms.

Special instruction to reviewers: **also audit whether the design actually upholds the project's agnosticism principle end-to-end**. The previous rounds missed two violations; this round must not.
