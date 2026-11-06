# Feature Exploration: Advanced Charging Planner

> Kept as reference. Written on 2026-04-22; where it disagrees with `../decisions.md` or `../motor.md`, it is out of date. The status of each feature is in `../feature-candidates.md`.

- **Feature:** initial
- **Date:** 2026-04-22
- **Status:** Exploration document — not a design spec. Used to capture the full feature surface before deciding what goes into the initial motor vs. deferred to later iterations.
- **Trigger:** user request: *"make me a list of features that could interest those doing advanced charge planning, so we make sure this is the best engine there is."* (translated)

This document collects the full candidate-feature surface for an advanced EV charging motor. It is not a commitment. Each feature has a **scope** tag indicating whether it belongs in the initial motor (M), a later HA-integration feature (H), a much-later iteration (L), or out-of-scope entirely (X).

---

## 1. Price-intelligence features

### 1.1 Sliding forecast-confidence hysteresis (M) — user-requested

**Problem:** "It must not be fixed, but sliding." (translated) If future electricity is 2% cheaper, we shouldn't bet on it — forecasts can flip. If it's 20% cheaper, worth waiting. But "20% cheaper in 3 hours" is much more trustworthy than "20% cheaper in 5 days". Uncertainty grows with time horizon.

**Proposal — markup future prices by uncertainty:**

Add to `PlannerInput`:

```python
# Uncertainty markup for forecast prices. Prices flagged is_forecast=True
# are multiplied by (1 + markup) where markup = base + hours_ahead * per_hour.
# Raw prices (is_forecast=False) keep their value. Cost estimates in the
# output always use raw prices; the markup only affects WINDOW SELECTION.
forecast_markup_base_percent: float = 5.0        # flat markup for any forecast
forecast_markup_per_hour_percent: float = 0.2   # additional per hour ahead
```

**Defaults:** 5% + 0.2%/hour means:
- 12h ahead forecast: 5 + 2.4 = 7.4% markup
- 1d ahead: 5 + 4.8 = 9.8%
- 2d ahead: 5 + 9.6 = 14.6%
- 5d ahead: 5 + 24 = 29%
- 7d ahead: 5 + 33.6 = 38.6%

A 7-day-out forecast has to be **38.6% cheaper** than now to be picked — matching the user's intuition that far-future bets need big payoff.

**Integration into window search:**

`_find_cheapest_window` compares by `selection_price = raw_price * (1 + markup)`; cost estimates in `ChargeWindow.expected_cost` and `avg_price` still use raw prices.

**User-facing controls (all optional with sensible defaults):**
- `forecast_markup_base_percent` (default 5.0)
- `forecast_markup_per_hour_percent` (default 0.2)
- Future iteration: `forecast_markup_profile: list[tuple[int, float]]` — piecewise-linear profile (hours → markup), overriding the base+per_hour pair.

**Why this shape:**
- Motor stays currency-agnostic (markup is a percentage)
- Adapters can set low markup (trusting their forecasts) or high markup (defensive) per caller
- Per-weekday overrides are possible by adapting the PricePoint data: adapter can flip `is_forecast=False` for today's known-good hours and `True` for tomorrow+

### 1.2 Price-confidence field on `PricePoint` (L)

Alternative / extension: add `confidence: float` (0..1) to `PricePoint`. Motor uses `1 / confidence` as a direct markup multiplier. Defer until multi-source price fusion is a real need.

### 1.3 Time-of-use tariff with fixed blocks (L)

Some markets have flat-rate blocks (peak/off-peak tiers) rather than hourly prices. Adapter could flatten these into hourly prices, but a native block representation would be cleaner. Defer.

### 1.4 Demand charges (L)

Some commercial/industrial tariffs charge per-kW peak draw. Motor would need to minimize peak draw rather than minimize average cost. Out of scope for residential charging; defer.

### 1.5 Critical peak pricing / grid-stress events (L)

Grid operators issue "don't charge now" signals during stress. Easy to model as a one-hour absence window on a virtual trip, or as a price spike. Existing mechanisms cover it.

### 1.6 Carbon intensity optimization (L)

Add `grid_carbon_g_per_kwh: list[float]` parallel to prices. Motor picks windows minimizing a weighted combination of cost and carbon. Configurable weight. Nice-to-have, defer.

---

## 2. SoC and battery features

### 2.1 Hysteresis idle floor (`min_idle_soc`) (M) — already in design

Covered in current design.

### 2.2 Battery health — avoid-100% bias (L)

Prefer charging to `default_target_soc` (80%) rather than 100% even when 100% is reachable. The existing split-plan already does this implicitly (main window fills to default_target, top-up only fills the remainder). Explicit "battery-health mode" could flatten `target_soc=90` to `default_target_soc=80` unless a trip actually requires higher. Defer.

### 2.3 Slow-charge in cold (L)

Add optional `outside_temp_c` input; slow charging rate when cold for battery longevity. Requires charger supports variable power. Adapter-level concern.

### 2.4 Partial-cycle preference (L)

Battery longevity is better with 30→70% cycles than 10→90%. Motor could prefer plans that stay in a tight band. Complex trade-off vs. trip feasibility. Defer.

### 2.5 Target SoC range (soft vs. hard minimum) (M, optional)

Allow `Trip.target_soc_min` and `Trip.target_soc_preferred`:
- Motor tries to reach `preferred`
- Falls back to at-least `min` if prices/time are bad
- Warning when only `min` is achievable

Trade-off: nice flexibility but adds complexity to every window search. Optional for initial motor.

### 2.6 Safety-floor violation alert (M, small)

Output flag: `plan_guarantees_safety: bool` — false if the multi-trip plan cannot keep SoC above `min_safety_soc` at all times across the chain. Adapter can alert user.

---

## 3. Trip / schedule features

### 3.1 Multi-trip planning (M) — in current design

Covered.

### 3.2 Uncertain / probabilistic trips (L)

`Trip.probability: float` (0..1). Motor weights planning effort by probability. Complex. Defer.

### 3.3 Intermediate charging stops during long trips (X)

For a 800 km trip, user might public-charge mid-way. Motor just sees a single Trip with `energy_kwh = net_consumption_after_midway_charge`. Adapter handles decomposition. No motor feature needed.

### 3.4 Calendar-flex: "must be ready by X OR Y" (L)

User sets two acceptable departure times; motor picks the one with cheapest plan. Requires multi-plan comparison. Defer.

### 3.5 Preconditioning hooks (H)

Cabin heating / battery warming before departure. Emit a `PRECONDITION` action N minutes before trip. Likely adapter/HA-integration territory, not motor.

### 3.6 Vacation / extended-absence mode (M, small)

A single Trip with a very long `end - start` already models this (car is away for a week). Multi-trip absence filter handles it. Document the pattern; no new feature.

### 3.7 Recurrence (L)

"Commute every weekday 07:00-17:00" as a recurring Trip. Adapter should expand recurrence into concrete Trips before passing to motor; no recurrence concept in motor. Document adapter pattern.

### 3.8 Post-trip return-home idle fill (M, optional)

After last trip ends, if expected-SoC-at-end < `min_idle_soc`, emit trailing idle-fill window. **Open decision point** per Stage 3 algorithm review. Recommend: defer, let next tick's branch 6b handle it.

---

## 4. Charger features

### 4.1 Variable current / ramp profiles (L)

Many chargers support 6-32A with minimum current thresholds. Motor currently assumes constant power. Adapter can flatten an effective power, but native support would be more flexible. Defer.

### 4.2 Charger-native price floor delegation (M) — already in design

`charger_auto_threshold` — covered.

### 4.3 Solar surplus charging (H)

Adapter watches solar signal, feeds motor a synthetic "free hour" or flips `charger_auto_threshold` when solar surplus is available. No motor feature needed.

### 4.4 Load balancing / mains limit (H)

Coordinator watches other loads and caps charger power. Adapter-layer. No motor feature needed.

### 4.5 V2G / bidirectional (L)

`DISCHARGE` action type, negative energy trips (feed-in). Large scope. Defer.

### 4.6 Multi-charger per-car (L)

Car sometimes charges at home, sometimes at work. Adapter switches `charger_power_kw` between calls (already supported). Active-plan handling across charger changes: verify tests cover. No new motor feature.

### 4.7 Multi-car per-charger (L)

Two cars sharing one charger; scheduling between them. Coordinator layer concern, not motor. Motor runs once per car. No new feature.

---

## 5. User-experience features

### 5.1 Override / "force charge now" button (H)

User manually triggers immediate charging regardless of plan. Adapter injects a synthetic "very cheap" current hour or sets `charger_auto_threshold` temporarily high. No motor feature.

### 5.2 Pause charging schedule (H)

User says "don't charge tonight". Adapter inserts a no-go absence window (can model as a synthetic Trip with energy_kwh=0). Works via existing absence filter.

### 5.3 Departure-ready notifications (H)

Adapter watches motor output and notifies user if `should_charge_now` but car isn't actually charging (charger not responding, etc.). Adapter concern.

### 5.4 Plan explanations / "why did you do that?" (M, small)

Rich `PlannerOutput.warnings` with structured reason codes. Current design has unstructured English strings. Consider promoting to structured warnings later. Low priority.

### 5.5 Cost display in native currency (H)

Adapter formats `expected_cost` with user's currency symbol. No motor feature.

### 5.6 Savings vs. dumb-charging comparison (L)

Motor returns `savings_vs_immediate_charge` — cost delta between planned window and charging immediately. Requires computing an alternative plan. Defer.

---

## 6. Algorithmic / optimization features

### 6.1 Window-selection strategies (L, flagged earlier)

Current: cheapest average. Alternatives: min-peak, prefer-daytime (solar proxy), prefer-night, prefer-earliest-safe. Pluggable strategy. Flexibility-audit flagged this as Tier-1; given user's focus on the best motor, consider promoting to M.

### 6.2 Rounding mode (ceiling/floor/nearest) (L)

Window-hour rounding is always ceiling. Pluggable for edge cases. Defer.

### 6.3 Active-plan invalidation predicates (L)

Currently: age + event-passed. User could supply callables for "invalidate if SoC drifted >5%" or "if price forecast changed >20%". Needs callables in contract. Defer.

### 6.4 Cost model plugins (L)

Pluggable `cost(price, power, hours, ...) -> cost` for fixed-fee tariffs, demand charges, etc. Defer until needed.

### 6.5 Multi-pass optimization (L)

Replace greedy forward iteration with full optimizer (integer programming) for complex multi-trip scenarios. Defer unless realism of the greedy algorithm becomes insufficient.

### 6.6 Horizon-aware planning (M — enabled by 1.1)

With forecast-confidence hysteresis, the motor naturally prefers nearer-term cheap hours over distant ones. Covered by 1.1.

---

## 7. Observability / diagnostics

### 7.1 Rich `PlannerOutput` with trace (L)

Return step-by-step reasoning: "Evaluated 12 candidate windows; selected [X, Y] with adjusted avg price Z; rejected [A, B] because cheaper but 5 days out with 29% markup." Useful for debugging. Defer.

### 7.2 Determinism token / plan ID (L)

Return a hash of the input + plan for debugging. Defer.

### 7.3 Metrics output (H)

Motor returns metrics (cost savings, carbon avoided, etc.) for HA sensor dashboards. Adapter computes; no motor feature.

---

## Summary — proposed scope for the INITIAL motor

**Must-have (M):**
- Multi-trip planning (in current design; algorithm bug to fix)
- Hysteresis idle floor (`min_idle_soc`) (in current design)
- **NEW: Sliding forecast-confidence hysteresis** (§1.1) — add to design
- `charger_auto_threshold` (already in design)
- Full configurability of algorithm tunables (already in design)
- Safety-floor violation flag in output (§2.6) — consider adding

**Consider for initial (M, optional):**
- Target SoC range with min vs. preferred (§2.5)
- Post-trip return-home idle fill (§3.8) — decision pending

**Defer to later (H/L):**
- Most everything else

**Out of scope (X):**
- V2G
- Intermediate charging stops (adapter handles)
- Multi-car scheduling (coordinator handles)

---

## Decisions I need from you

1. **Sliding forecast hysteresis:** include in initial motor (§1.1)? Recommended: **yes** — it directly addresses your concern about rigid fixed thresholds.
2. **Target SoC range (§2.5):** `Trip.target_soc_min` + `target_soc_preferred`? Trade-off: real feature, adds complexity to window search. Recommended: **defer** unless you see an immediate need.
3. **Safety-floor violation flag (§2.6):** add `plan_guarantees_safety: bool` to `PlannerOutput`? Recommended: **yes** — small cost, meaningful signal.
4. **Post-trip idle-fill (§3.8):** add or defer? Algorithm review recommends defer; next tick catches it.
5. **Window-selection strategies (§6.1):** initial motor ships with cheapest-only, or pluggable from day one? Flexibility audit flagged this as Tier 1. Recommended: **defer to later feature** — pluggable strategies add a lot of surface and can be retrofitted without breaking contract.

Once you choose, I fold decisions into the multi-trip design (revision 2) and the algorithm-ordering fix from Stage 3 agents. Then Stage 3 round 2 review, then implementation.
