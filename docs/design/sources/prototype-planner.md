# First prototype of the engine

> Kept as reference for its window search and charge arithmetic. It plans for one trip at a time, with the data model and constant power that `../decisions.md` has since replaced; it is not code to build on.

```python
"""Stateless EV charging planner.

Call :meth:`ChargePlanner.plan` once per coordinator tick. The planner is
re-entrant and thread-safe; no instance state is carried between calls.

Invariants (caller's responsibility to uphold):
  - All datetimes must be timezone-aware (UTC strongly recommended).
    Naive datetimes raise ``ValueError`` at :meth:`plan` entry.
  - Power in kW; battery capacity in kWh. Time arithmetic uses
    ``datetime`` / ``timedelta`` (hours internally).
  - Prices must be supplied in the same currency across a single
    :meth:`plan` call. The planner performs no currency conversion;
    cost outputs are in the same currency as input prices
    (the planner is currency-agnostic).
  - The planner knows nothing about distance. It deals exclusively in
    SoC percentages, kWh, and time. Callers that want to plan by
    distance (km, miles, nautical miles, ...) must convert to an SoC
    target in their own layer before constructing :class:`Trip` objects.
  - :class:`Trip.target_soc` must be in [0, 100]. Trips whose
    ``end < start`` or whose ``target_soc`` is out of range are skipped
    with a warning; planning continues with the remaining trips.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

# =============================================================================
# MATHEMATICAL CONSTANT
# =============================================================================
#
# All other tunable values live on PlannerInput as optional fields with
# sensible defaults. The motor bakes in nothing that a caller might
# reasonably want to override.

FULL_TARGET_SOC = 100  # 100% = full battery. Mathematical upper bound, not tunable.


# =============================================================================
# ENUMS
# =============================================================================


class PlanReason(Enum):
    SCHEDULED_TRIP = "scheduled_trip"
    MIN_SOC_SAFETY = "min_soc_safety"
    NO_TRIPS_NO_NEED = "no_trips_no_need"
    SOC_ALREADY_SUFFICIENT = "soc_already_sufficient"
    CAR_NOT_PLUGGED_IN = "car_not_plugged_in"
    STALE_SOC_NEEDS_WAKEUP = "stale_soc_needs_wakeup"
    INSUFFICIENT_TIME = "insufficient_time"
    CHARGER_HANDLES_LOW_PRICE = "charger_handles_low_price"
    ACTIVE_PLAN_CONTINUES = "active_plan_continues"
    SESSION_TOO_SHORT = "session_too_short"


class ActionType(Enum):
    """Side-effect instructions the planner emits for a consuming layer.

    ``params`` schema by ``action_type``:

    - ``START_CHARGING``       -> ``{}`` (empty)
    - ``STOP_CHARGING``        -> ``{}`` (empty)
    - ``WAKE_UP_CAR``          -> ``{}`` (empty)
    - ``SET_CHARGE_LIMIT``     -> ``{"soc_limit": int (0..100)}``
    - ``REQUEST_SOC_REFRESH``  -> ``{}`` (empty)

    Consumers should treat any unrecognized key as informational and
    forward-compatible.
    """

    START_CHARGING = "start_charging"
    STOP_CHARGING = "stop_charging"
    WAKE_UP_CAR = "wake_up_car"
    SET_CHARGE_LIMIT = "set_charge_limit"
    REQUEST_SOC_REFRESH = "request_soc_refresh"


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass(frozen=True)
class PricePoint:
    """An hourly price slot starting at ``start`` and covering one hour.

    ``price_total`` is unit-free at the planner level; it is multiplied
    by power (kW) and time (hours) to produce cost in the same currency.
    Caller is responsible for currency consistency across a single
    :meth:`ChargePlanner.plan` call.
    """

    start: datetime
    price_total: float
    is_forecast: bool = False
    source: str = "nordpool"


@dataclass(frozen=True)
class Trip:
    """A scheduled trip with a required SoC at departure.

    The caller supplies ``target_soc`` directly. How they derived it
    (trip distance, arrival buffer, manual input, seasonal correction
    for outside temperature, etc.) is not the motor's concern. The
    motor does no distance arithmetic and no unit conversion.

    If ``end`` is set, the interval ``[start, end]`` is treated as a
    period when the car is unavailable for charging; the motor excludes
    that interval from window planning.
    """

    start: datetime
    target_soc: int
    end: datetime | None = None
    description: str = ""


@dataclass(frozen=True)
class ChargeWindow:
    start: datetime
    end: datetime
    target_soc: int
    expected_kwh: float
    expected_cost: float
    avg_price: float
    is_top_up: bool = False
    requires_wakeup: bool = False


@dataclass(frozen=True)
class PlannerAction:
    """A side-effect instruction emitted by the planner.

    The planner is the sole emitter; ``params`` keys are guaranteed at
    emit time to match the schema documented on :class:`ActionType`.
    """

    action_type: ActionType
    execute_at: datetime
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ActivePlan:
    planned_at: datetime
    windows: list[ChargeWindow]
    for_trip_start: datetime | None = None


@dataclass(frozen=True)
class PlannerInput:
    """All inputs the planner needs for one decision.

    Car and charger specs and user preferences are **required** — the
    motor is car-, charger-, and preference-agnostic and makes no
    assumptions about any of them. Callers (typically an HA-integration
    adapter) must supply every value.

    Validation is performed at :meth:`ChargePlanner.plan` entry:
    negative or out-of-range values raise ``ValueError``.
    """

    # --- State (required) ---
    now: datetime
    current_soc: float  # 0..100
    soc_last_updated: datetime
    is_plugged_in: bool

    # --- Car specs (required) ---
    battery_capacity_kwh: float  # > 0

    # --- Charger specs (required) ---
    charger_power_kw: float  # > 0
    charger_efficiency: float  # in (0, 1]

    # --- User preferences (required) ---
    default_target_soc: int  # 0..100 — normal charge ceiling, e.g. 80
    min_safety_soc: int  # 0..100 — emergency-charge floor, e.g. 25

    # --- Optional state ---
    is_currently_charging: bool = False
    prices: list[PricePoint] = field(default_factory=list)
    trips: list[Trip] = field(default_factory=list)
    active_plan: ActivePlan | None = None

    # Threshold below which the planner delegates to the charger's native
    # auto-logic (if any). ``None`` disables the branch entirely — the
    # safe default, since not all chargers have a native price floor.
    # Negative values raise ``ValueError``. Adapter sets this per charger.
    charger_auto_threshold: float | None = None

    # --- Algorithm tunables (defaults cover most cases; override freely) ---

    # Older than this, SoC data is considered stale; the planner wakes the
    # car and asks for a refresh instead of planning.
    soc_max_age_minutes: int = 30

    # Sessions shorter than this are skipped (many chargers/cars don't
    # reliably start a very short session). Adjust per charger.
    min_session_minutes: int = 15

    # How far before a charge window starts to send the wake-up /
    # set-charge-limit action. Car-dependent: slower-waking cars need more.
    wake_up_before_charge_minutes: int = 5

    # Plans older than this are discarded and the next tick replans.
    active_plan_max_age_hours: int = 12

    # Within this many seconds before a window start, the plan is still
    # considered "in" the window (prevents last-minute replanning).
    near_window_seconds: int = 300

    # Delay between WAKE_UP_CAR and the follow-up REQUEST_SOC_REFRESH.
    # Cars differ in how long they need to come out of deep sleep.
    soc_refresh_delay_seconds: int = 30


@dataclass(frozen=True)
class PlannerOutput:
    should_charge_now: bool
    reason: PlanReason
    windows: list[ChargeWindow] = field(default_factory=list)
    actions: list[PlannerAction] = field(default_factory=list)
    next_trip: Trip | None = None
    warnings: list[str] = field(default_factory=list)

    def first_window(self) -> ChargeWindow | None:
        return self.windows[0] if self.windows else None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def kwh_to_soc_percent(kwh: float, battery_capacity_kwh: float) -> float:
    if battery_capacity_kwh <= 0:
        raise ValueError("battery capacity must be positive")
    return (kwh / battery_capacity_kwh) * 100.0


def soc_percent_to_kwh(soc_percent: float, battery_capacity_kwh: float) -> float:
    return (soc_percent / 100.0) * battery_capacity_kwh


def hours_to_charge(
    kwh_needed: float, charger_power_kw: float, efficiency: float
) -> float:
    if charger_power_kw <= 0:
        raise ValueError("charger power must be positive")
    if efficiency <= 0 or efficiency > 1:
        raise ValueError("efficiency must be in the interval (0, 1]")
    return kwh_needed / (charger_power_kw * efficiency)


def is_soc_stale(
    now: datetime,
    soc_last_updated: datetime,
    max_age_minutes: int = 30,
) -> bool:
    age_seconds = (now - soc_last_updated).total_seconds()
    return age_seconds > (max_age_minutes * 60)


def are_hours_contiguous(prices: list[PricePoint]) -> bool:
    """Return ``True`` if ``prices`` cover contiguous hourly slots in order."""
    if len(prices) <= 1:
        return True
    for i in range(1, len(prices)):
        expected = prices[i - 1].start + timedelta(hours=1)
        if prices[i].start != expected:
            return False
    return True


def _contiguous_run_length(prices: list[PricePoint]) -> list[int]:
    """For each index ``i``, the number of contiguous hourly prices starting
    at ``i``. Enables O(1) contiguity checks inside sliding-window searches.
    """
    n = len(prices)
    if n == 0:
        return []
    runs = [1] * n
    for i in range(n - 2, -1, -1):
        if prices[i + 1].start == prices[i].start + timedelta(hours=1):
            runs[i] = runs[i + 1] + 1
    return runs


def _price_hour_overlaps_trip(price: PricePoint, trip: Trip) -> bool:
    """Return True if the one-hour slot starting at ``price.start`` overlaps
    the trip's absence window ``[trip.start, trip.end)``. If ``trip.end`` is
    None, the trip is just a deadline and occupies no time range.
    """
    if trip.end is None:
        return False
    price_end = price.start + timedelta(hours=1)
    return price.start < trip.end and trip.start < price_end


def _price_in_any_absence(price: PricePoint, trips: list[Trip]) -> bool:
    """Return True if the price slot overlaps any trip's absence window."""
    return any(_price_hour_overlaps_trip(price, t) for t in trips)


# =============================================================================
# PLANNER
# =============================================================================


class ChargePlanner:
    """Pure planning logic. No I/O. All inputs explicit."""

    def plan(self, inp: PlannerInput) -> PlannerOutput:
        """Evaluate a fixed-order decision tree and return a plan."""
        warnings: list[str] = []

        # Contract validation: fail fast on invariant violations.
        self._validate_timezone_aware(inp)
        self._validate_numeric(inp)
        self._validate_threshold(inp.charger_auto_threshold)

        # Normalize price ordering and detect duplicates.
        prices = self._sorted_prices(inp.prices, warnings)

        # Skip malformed trips with informative warnings.
        trips = self._validate_trips(inp.trips, warnings)

        # 1. Car not plugged in.
        if not inp.is_plugged_in:
            return PlannerOutput(
                should_charge_now=False,
                reason=PlanReason.CAR_NOT_PLUGGED_IN,
                warnings=warnings,
            )

        # 2. Active plan that is still valid.
        if self._active_plan_is_valid(inp):
            return self._follow_active_plan(inp, warnings)

        # 3. Stale SoC.
        if is_soc_stale(inp.now, inp.soc_last_updated, inp.soc_max_age_minutes):
            age_min = (inp.now - inp.soc_last_updated).total_seconds() / 60
            return PlannerOutput(
                should_charge_now=False,
                reason=PlanReason.STALE_SOC_NEEDS_WAKEUP,
                actions=[
                    # Schema: WAKE_UP_CAR.params = {}
                    PlannerAction(ActionType.WAKE_UP_CAR, inp.now),
                    # Schema: REQUEST_SOC_REFRESH.params = {}
                    PlannerAction(
                        ActionType.REQUEST_SOC_REFRESH,
                        inp.now + timedelta(seconds=inp.soc_refresh_delay_seconds),
                    ),
                ],
                warnings=[
                    f"SoC data is {age_min:.0f} min old (max "
                    f"{inp.soc_max_age_minutes} min); waking car and requesting refresh.",
                    *warnings,
                ],
            )

        # 4. Critical SoC.
        if inp.current_soc < inp.min_safety_soc:
            return self._plan_emergency_charge(inp, prices, trips, warnings)

        # 5. Charger handles low price (delegated auto-charge).
        if inp.charger_auto_threshold is not None:
            current_price = self._price_at(prices, inp.now)
            if current_price is not None and current_price < inp.charger_auto_threshold:
                return PlannerOutput(
                    should_charge_now=True,
                    reason=PlanReason.CHARGER_HANDLES_LOW_PRICE,
                    warnings=[
                        f"Current price {current_price:.2f} is below charger "
                        f"auto threshold {inp.charger_auto_threshold:.2f}; "
                        f"delegating to the charger's native auto-logic.",
                        *warnings,
                    ],
                )

        # 6. No upcoming trip.
        next_trip = self._next_trip(trips, inp.now)
        if next_trip is None:
            return PlannerOutput(
                should_charge_now=False,
                reason=PlanReason.NO_TRIPS_NO_NEED,
                warnings=warnings,
            )

        required_soc = next_trip.target_soc

        # 7. SoC already sufficient.
        if inp.current_soc >= required_soc:
            return PlannerOutput(
                should_charge_now=False,
                reason=PlanReason.SOC_ALREADY_SUFFICIENT,
                next_trip=next_trip,
                warnings=warnings,
            )

        # 8. Time check.
        deadline = next_trip.start
        kwh_needed = soc_percent_to_kwh(
            required_soc - inp.current_soc, inp.battery_capacity_kwh
        )
        hours_needed = hours_to_charge(
            kwh_needed, inp.charger_power_kw, inp.charger_efficiency
        )
        hours_available = (deadline - inp.now).total_seconds() / 3600.0

        session_minutes = hours_needed * 60
        if session_minutes < inp.min_session_minutes:
            return PlannerOutput(
                should_charge_now=False,
                reason=PlanReason.SESSION_TOO_SHORT,
                next_trip=next_trip,
                warnings=[
                    f"Required session is only {session_minutes:.0f} min; "
                    f"too short for reliable charger start.",
                    *warnings,
                ],
            )

        if hours_available < hours_needed:
            return self._plan_insufficient_time(
                inp, prices, trips, required_soc, deadline, hours_available, warnings
            )

        # 9. Normal planning.
        if required_soc > inp.default_target_soc:
            windows, actions = self._plan_with_top_up(
                inp, prices, trips, required_soc, deadline, warnings
            )
        else:
            window = self._find_cheapest_window(
                inp,
                prices,
                trips,
                required_soc,
                inp.now,
                deadline,
                warnings,
            )
            windows = [window]
            actions = self._actions_for_window(
                window, inp.wake_up_before_charge_minutes
            )

        should_charge_now = any(w.start <= inp.now < w.end for w in windows)

        return PlannerOutput(
            should_charge_now=should_charge_now,
            reason=PlanReason.SCHEDULED_TRIP,
            windows=windows,
            actions=actions,
            next_trip=next_trip,
            warnings=warnings,
        )

    # ------------------------------------------------------------------------
    # Contract validation
    # ------------------------------------------------------------------------

    def _validate_timezone_aware(self, inp: PlannerInput) -> None:
        """Raise ``ValueError`` if any input datetime lacks ``tzinfo``."""

        def _check(label: str, dt: datetime | None) -> None:
            if dt is not None and dt.tzinfo is None:
                raise ValueError(
                    f"{label} must be timezone-aware (UTC expected); "
                    f"got naive datetime."
                )

        _check("PlannerInput.now", inp.now)
        _check("PlannerInput.soc_last_updated", inp.soc_last_updated)
        for i, p in enumerate(inp.prices):
            _check(f"PlannerInput.prices[{i}].start", p.start)
        for i, t in enumerate(inp.trips):
            _check(f"PlannerInput.trips[{i}].start", t.start)
            _check(f"PlannerInput.trips[{i}].end", t.end)
        if inp.active_plan is not None:
            _check(
                "PlannerInput.active_plan.planned_at", inp.active_plan.planned_at
            )
            _check(
                "PlannerInput.active_plan.for_trip_start",
                inp.active_plan.for_trip_start,
            )
            for i, w in enumerate(inp.active_plan.windows):
                _check(f"PlannerInput.active_plan.windows[{i}].start", w.start)
                _check(f"PlannerInput.active_plan.windows[{i}].end", w.end)

    @staticmethod
    def _validate_threshold(threshold: float | None) -> None:
        if threshold is not None and threshold < 0:
            raise ValueError(
                f"charger_auto_threshold must be None or non-negative; "
                f"got {threshold!r}"
            )

    @staticmethod
    def _validate_numeric(inp: PlannerInput) -> None:
        if inp.battery_capacity_kwh <= 0:
            raise ValueError(
                f"battery_capacity_kwh must be positive; "
                f"got {inp.battery_capacity_kwh!r}"
            )
        if inp.charger_power_kw <= 0:
            raise ValueError(
                f"charger_power_kw must be positive; got {inp.charger_power_kw!r}"
            )
        if not (0 < inp.charger_efficiency <= 1):
            raise ValueError(
                f"charger_efficiency must be in (0, 1]; "
                f"got {inp.charger_efficiency!r}"
            )
        for label, value in (
            ("current_soc", inp.current_soc),
            ("default_target_soc", inp.default_target_soc),
            ("min_safety_soc", inp.min_safety_soc),
        ):
            if not (0 <= value <= 100):
                raise ValueError(f"{label} must be in [0, 100]; got {value!r}")

    def _sorted_prices(
        self, prices: list[PricePoint], warnings: list[str]
    ) -> list[PricePoint]:
        """Return a sorted-by-start copy. Warn on duplicate start times."""
        if not prices:
            return []
        sorted_prices = sorted(prices, key=lambda p: p.start)
        deduped: list[PricePoint] = []
        last_start: datetime | None = None
        for p in sorted_prices:
            if p.start == last_start:
                warnings.append(
                    f"Duplicate PricePoint at {p.start.isoformat()}; "
                    f"using first occurrence and ignoring the rest."
                )
                continue
            deduped.append(p)
            last_start = p.start
        return deduped

    def _validate_trips(
        self, trips: list[Trip], warnings: list[str]
    ) -> list[Trip]:
        """Skip malformed trips with a warning naming each one."""
        valid: list[Trip] = []
        for t in trips:
            if not (0 <= t.target_soc <= 100):
                warnings.append(
                    f"Skipped Trip {t.description!r}: target_soc must be in "
                    f"[0, 100]; got {t.target_soc!r}."
                )
                continue
            if t.end is not None and t.end < t.start:
                warnings.append(
                    f"Skipped Trip {t.description!r}: end ({t.end.isoformat()}) "
                    f"is before start ({t.start.isoformat()})."
                )
                continue
            valid.append(t)
        return valid

    # ------------------------------------------------------------------------
    # Plan decisions
    # ------------------------------------------------------------------------

    def _active_plan_is_valid(self, inp: PlannerInput) -> bool:
        plan = inp.active_plan
        if plan is None or not plan.windows:
            return False

        age_hours = (inp.now - plan.planned_at).total_seconds() / 3600.0
        if age_hours > inp.active_plan_max_age_hours:
            return False

        if plan.for_trip_start and plan.for_trip_start < inp.now:
            return False

        for w in plan.windows:
            if w.start <= inp.now < w.end:
                return True
            if (
                inp.now < w.start
                and (w.start - inp.now).total_seconds() < inp.near_window_seconds
            ):
                return True

        return False

    def _follow_active_plan(
        self, inp: PlannerInput, warnings: list[str]
    ) -> PlannerOutput:
        assert inp.active_plan is not None  # guarded by _active_plan_is_valid
        active_window: ChargeWindow | None = None
        for w in inp.active_plan.windows:
            if w.start <= inp.now < w.end:
                active_window = w
                break

        return PlannerOutput(
            should_charge_now=active_window is not None,
            reason=PlanReason.ACTIVE_PLAN_CONTINUES,
            windows=list(inp.active_plan.windows),
            warnings=[
                "Following active plan from previous tick; no replanning.",
                *warnings,
            ],
        )

    def _plan_emergency_charge(
        self,
        inp: PlannerInput,
        prices: list[PricePoint],
        trips: list[Trip],
        warnings: list[str],
    ) -> PlannerOutput:
        target = inp.default_target_soc
        kwh_needed = soc_percent_to_kwh(
            target - inp.current_soc, inp.battery_capacity_kwh
        )
        duration_hours = hours_to_charge(
            kwh_needed, inp.charger_power_kw, inp.charger_efficiency
        )
        window_end = inp.now + timedelta(hours=duration_hours)

        window = ChargeWindow(
            start=inp.now,
            end=window_end,
            target_soc=target,
            expected_kwh=kwh_needed,
            expected_cost=self._estimate_cost(
                prices, inp.now, window_end, inp.charger_power_kw, warnings
            ),
            avg_price=self._avg_price_in_range(
                prices, inp.now, window_end, warnings
            ),
        )

        return PlannerOutput(
            should_charge_now=True,
            reason=PlanReason.MIN_SOC_SAFETY,
            windows=[window],
            # Schema: START_CHARGING.params = {}
            actions=[PlannerAction(ActionType.START_CHARGING, inp.now)],
            next_trip=self._next_trip(trips, inp.now),
            warnings=[
                f"SoC critically low ({inp.current_soc}%); charging immediately "
                f"regardless of price.",
                *warnings,
            ],
        )

    def _plan_insufficient_time(
        self,
        inp: PlannerInput,
        prices: list[PricePoint],
        trips: list[Trip],
        target: int,
        deadline: datetime,
        hours_available: float,
        warnings: list[str],
    ) -> PlannerOutput:
        hours_needed = hours_to_charge(
            soc_percent_to_kwh(target - inp.current_soc, inp.battery_capacity_kwh),
            inp.charger_power_kw,
            inp.charger_efficiency,
        )
        warnings.append(
            f"Insufficient time: need {hours_needed:.1f} h, have "
            f"{hours_available:.1f} h before {deadline.isoformat()}. Charging at "
            f"maximum."
        )
        window = ChargeWindow(
            start=inp.now,
            end=deadline,
            target_soc=target,
            expected_kwh=hours_available
            * inp.charger_power_kw
            * inp.charger_efficiency,
            expected_cost=self._estimate_cost(
                prices, inp.now, deadline, inp.charger_power_kw, warnings
            ),
            avg_price=self._avg_price_in_range(prices, inp.now, deadline, warnings),
        )
        return PlannerOutput(
            should_charge_now=True,
            reason=PlanReason.INSUFFICIENT_TIME,
            windows=[window],
            # Schema: START_CHARGING.params = {}
            actions=[PlannerAction(ActionType.START_CHARGING, inp.now)],
            next_trip=self._next_trip(trips, inp.now),
            warnings=warnings,
        )

    # ------------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------------

    def _next_trip(
        self, trips: list[Trip], now: datetime
    ) -> Trip | None:
        future = [t for t in trips if t.start > now]
        return min(future, key=lambda t: t.start) if future else None

    def _price_at(self, prices: list[PricePoint], when: datetime) -> float | None:
        for p in prices:
            if p.start <= when < p.start + timedelta(hours=1):
                return p.price_total
        return None

    def _avg_price_in_range(
        self,
        prices: list[PricePoint],
        start: datetime,
        end: datetime,
        warnings: list[str],
    ) -> float:
        relevant = [p for p in prices if start <= p.start < end]
        if not relevant:
            warnings.append(
                f"No price data in range {start.isoformat()}..{end.isoformat()}; "
                f"cost estimate defaults to 0.0."
            )
            return 0.0
        return sum(p.price_total for p in relevant) / len(relevant)

    # Cost model: avg_price (currency/kWh) * power (kW) * hours = cost.
    # Efficiency is accounted for on the expected_kwh side, not in cost.
    # Both _estimate_cost and the split-plan main-window cost math use
    # ceiling-rounded integer hours for window selection so that window
    # choice and cost estimate remain consistent.
    def _estimate_cost(
        self,
        prices: list[PricePoint],
        start: datetime,
        end: datetime,
        power_kw: float,
        warnings: list[str],
    ) -> float:
        avg = self._avg_price_in_range(prices, start, end, warnings)
        hours = (end - start).total_seconds() / 3600.0
        return avg * power_kw * hours

    # ------------------------------------------------------------------------
    # Window finders
    # ------------------------------------------------------------------------

    def _find_cheapest_window(
        self,
        inp: PlannerInput,
        prices: list[PricePoint],
        trips: list[Trip],
        target_soc: int,
        earliest_start: datetime,
        latest_end: datetime,
        warnings: list[str],
    ) -> ChargeWindow:
        """Cheapest contiguous window that does not overlap any trip's
        absence period. Skips gaps in price data via a precomputed
        contiguous-run-length array; overall O(P).
        """
        kwh_needed = soc_percent_to_kwh(
            target_soc - inp.current_soc, inp.battery_capacity_kwh
        )
        if kwh_needed <= 0:
            return ChargeWindow(
                start=earliest_start,
                end=earliest_start,
                target_soc=target_soc,
                expected_kwh=0,
                expected_cost=0,
                avg_price=0,
            )

        hours_needed = hours_to_charge(
            kwh_needed, inp.charger_power_kw, inp.charger_efficiency
        )
        hours_needed_int = max(1, int(hours_needed + 0.99))

        # `prices` is sorted at plan() entry; preserve order while filtering.
        relevant_prices = [
            p
            for p in prices
            if earliest_start <= p.start < latest_end
            and not _price_in_any_absence(p, trips)
        ]

        if len(relevant_prices) < hours_needed_int:
            warnings.append(
                f"Insufficient price data for full window at target SoC; "
                f"planning best-effort from {earliest_start.isoformat()}."
            )
            end = min(earliest_start + timedelta(hours=hours_needed), latest_end)
            return ChargeWindow(
                start=earliest_start,
                end=end,
                target_soc=target_soc,
                expected_kwh=kwh_needed,
                expected_cost=self._estimate_cost(
                    prices, earliest_start, end, inp.charger_power_kw, warnings
                ),
                avg_price=self._avg_price_in_range(
                    prices, earliest_start, end, warnings
                ),
            )

        runs = _contiguous_run_length(relevant_prices)

        best_start_idx: int | None = None
        best_avg = float("inf")

        for i in range(len(relevant_prices) - hours_needed_int + 1):
            if runs[i] < hours_needed_int:
                continue
            window_prices = relevant_prices[i : i + hours_needed_int]
            avg = sum(p.price_total for p in window_prices) / hours_needed_int
            if avg < best_avg:
                best_avg = avg
                best_start_idx = i

        if best_start_idx is None:
            warnings.append(
                f"No contiguous {hours_needed_int}-hour window available in "
                f"price data; planning best-effort from "
                f"{earliest_start.isoformat()}."
            )
            end = min(earliest_start + timedelta(hours=hours_needed), latest_end)
            return ChargeWindow(
                start=earliest_start,
                end=end,
                target_soc=target_soc,
                expected_kwh=kwh_needed,
                expected_cost=self._estimate_cost(
                    prices, earliest_start, end, inp.charger_power_kw, warnings
                ),
                avg_price=self._avg_price_in_range(
                    prices, earliest_start, end, warnings
                ),
            )

        window_start = relevant_prices[best_start_idx].start
        window_end = min(window_start + timedelta(hours=hours_needed), latest_end)

        return ChargeWindow(
            start=window_start,
            end=window_end,
            target_soc=target_soc,
            expected_kwh=kwh_needed,
            expected_cost=self._estimate_cost(
                prices, window_start, window_end, inp.charger_power_kw, warnings
            ),
            avg_price=best_avg,
        )

    def _plan_with_top_up(
        self,
        inp: PlannerInput,
        prices: list[PricePoint],
        trips: list[Trip],
        target_soc: int,
        deadline: datetime,
        warnings: list[str],
    ) -> tuple[list[ChargeWindow], list[PlannerAction]]:
        """Split plan: main charge to ``default_target_soc`` during cheap
        hours, then a top-up to ``target_soc`` immediately before the
        deadline. Both legs respect any trip absence windows inside
        ``[now, deadline]``.

        The top-up window emits ``SET_CHARGE_LIMIT`` as its pre-window
        action. On some vehicles, setting the target SoC wakes the car
        from deep sleep as a side effect; adapter implementations decide
        whether a separate ``WAKE_UP_CAR`` action is also needed.
        """
        windows: list[ChargeWindow] = []

        # Top-up leg: anchored at the deadline, sized for (target - default).
        extra_soc = target_soc - inp.default_target_soc
        extra_kwh = soc_percent_to_kwh(extra_soc, inp.battery_capacity_kwh)
        top_up_hours = hours_to_charge(
            extra_kwh, inp.charger_power_kw, inp.charger_efficiency
        )
        top_up_duration = timedelta(hours=top_up_hours)
        top_up_start = deadline - top_up_duration

        # Main leg: fill from current SoC to default_target_soc using the
        # cheapest contiguous window in [now, top_up_start) that does not
        # overlap any trip absence.
        main_kwh = soc_percent_to_kwh(
            inp.default_target_soc - inp.current_soc, inp.battery_capacity_kwh
        )

        if main_kwh > 0:
            main_hours = hours_to_charge(
                main_kwh, inp.charger_power_kw, inp.charger_efficiency
            )
            main_hours_int = max(1, int(main_hours + 0.99))

            relevant_prices = [
                p
                for p in prices
                if inp.now <= p.start < top_up_start
                and not _price_in_any_absence(p, trips)
            ]

            main_start = inp.now
            main_end = inp.now + timedelta(hours=main_hours)
            main_avg = 0.0

            if len(relevant_prices) >= main_hours_int:
                runs = _contiguous_run_length(relevant_prices)
                best_idx: int | None = None
                best_avg = float("inf")
                for i in range(len(relevant_prices) - main_hours_int + 1):
                    if runs[i] < main_hours_int:
                        continue
                    window_prices = relevant_prices[i : i + main_hours_int]
                    avg = (
                        sum(p.price_total for p in window_prices) / main_hours_int
                    )
                    if avg < best_avg:
                        best_avg = avg
                        best_idx = i

                if best_idx is not None:
                    main_start = relevant_prices[best_idx].start
                    main_end = min(
                        main_start + timedelta(hours=main_hours), top_up_start
                    )
                    main_avg = best_avg

            windows.append(
                ChargeWindow(
                    start=main_start,
                    end=main_end,
                    target_soc=inp.default_target_soc,
                    expected_kwh=main_kwh,
                    # Cost: main_avg (currency/kWh) * power (kW) * main_hours.
                    expected_cost=main_avg * inp.charger_power_kw * main_hours,
                    avg_price=main_avg,
                    is_top_up=False,
                    requires_wakeup=False,
                )
            )

        # Top-up window.
        windows.append(
            ChargeWindow(
                start=top_up_start,
                end=deadline,
                target_soc=target_soc,
                expected_kwh=extra_kwh,
                expected_cost=self._estimate_cost(
                    prices, top_up_start, deadline, inp.charger_power_kw, warnings
                ),
                avg_price=self._avg_price_in_range(
                    prices, top_up_start, deadline, warnings
                ),
                is_top_up=True,
                requires_wakeup=True,
            )
        )

        # Actions for both windows.
        actions: list[PlannerAction] = []
        for w in windows:
            if w.requires_wakeup:
                # Schema: SET_CHARGE_LIMIT.params = {"soc_limit": int (0..100)}
                actions.append(
                    PlannerAction(
                        action_type=ActionType.SET_CHARGE_LIMIT,
                        execute_at=w.start
                        - timedelta(minutes=inp.wake_up_before_charge_minutes),
                        params={"soc_limit": w.target_soc},
                    )
                )
            # Schema: START_CHARGING.params = {}
            actions.append(PlannerAction(ActionType.START_CHARGING, w.start))
            # Schema: STOP_CHARGING.params = {}
            actions.append(PlannerAction(ActionType.STOP_CHARGING, w.end))

        return windows, actions

    def _actions_for_window(
        self, window: ChargeWindow, wake_up_before_charge_minutes: int
    ) -> list[PlannerAction]:
        actions: list[PlannerAction] = []
        if window.requires_wakeup:
            # Schema: SET_CHARGE_LIMIT.params = {"soc_limit": int (0..100)}
            actions.append(
                PlannerAction(
                    action_type=ActionType.SET_CHARGE_LIMIT,
                    execute_at=window.start
                    - timedelta(minutes=wake_up_before_charge_minutes),
                    params={"soc_limit": window.target_soc},
                )
            )
        # Schema: START_CHARGING.params = {}
        actions.append(PlannerAction(ActionType.START_CHARGING, window.start))
        # Schema: STOP_CHARGING.params = {}
        actions.append(PlannerAction(ActionType.STOP_CHARGING, window.end))
        return actions
```
