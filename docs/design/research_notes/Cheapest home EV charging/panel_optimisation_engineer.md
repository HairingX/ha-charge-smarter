# Panel paper: optimisation and systems engineering — the planning algorithm and the engine's formulation

Written 2026-10-28 by the panel's optimisation and systems engineer. It resolves conflict C3
(D22, D12, O8), the missing designs of C8 and the formulation of O1. It does this by reviewing
the seven research notes in this folder and by running five new experiments.

**How to read this paper.**
- A link to a note and section (for example [scheduling_algorithm.md §2](scheduling_algorithm.md))
  points to a claim that note sources. Where I checked the note's own source or code, I say so.
- **(E1)–(E5)** mark my own experiments. They ran on CPython 3.13.17, x86-64, in this container.
  The scripts are in [experiments/panel_optimisation/](experiments/panel_optimisation/README.md).
- **Price data.** All experiments use DK1 quarter-hour day-ahead prices for 2025-10-01 to
  2026-10-28, 37,732 rows, fetched on 2026-10-28 from
  [Energi Data Service DayAheadPrices](https://api.energidataservice.dk/dataset/DayAheadPrices).
- **"Total price"** is (spot + grid tariff + 0.115 Energinet + 0.008 elafgift) × 1.25 VAT,
  with no supplier markup. The grid tariff is N1 area 131 "Nettarif C": in winter (Oct–Mar)
  0.088 / 0.264 / 0.791 DKK/kWh low / high / peak, in summer 0.132 high and 0.343 peak. The
  periods are 00–06 low, 17–21 peak, other hours high. These are the rates and periods of
  [price_composition_denmark.md §1](price_composition_denmark.md).
  - The 2026 flat parts are used for the whole period. Flat parts change neither the ranking of
    hours nor the absolute gaps.
  - N1's separate December 2025 rate is ignored.
- **(reasoning)** marks my own argument.

The headline: replace D22's pass 2 with an exact DP over (slot, SoC grid, on-state). The DP's
saving on price alone is small. The case for it is that it is the only stdlib method that can
carry the whole objective the other notes ask for. To keep it inside a sane budget:
- plan at the resolution of the prices given (hourly for most Danish households, quarters only
  where they are billed per quarter and the price is known);
- use a 0.25–0.5 kWh grid, rounded conservatively;
- restate the budget as about 50 ms, run in Home Assistant's executor.

O1 becomes "expected cost of the coming days' need": soft future demands inside the
forecast horizon, plus a concave terminal value.

---

## 1. C3 / D22, D12, O8 — exact DP or corrected greedy? Formulation, complexity, budget

### Takeaway
- **Price alone is a weak case for the DP.**
  - On realistic Danish inputs (total price with tariffs, 15-minute or hourly slots) the
    corrected greedy is exact at constant power. It loses only when the power tapers: median
    0.00–0.03 %, p90 0.9–1.5 %, worst week 8.6–15 % or up to about 9 DKK a week (E1).
  - Danish tariffs shrink the greedy's typical gap, mainly by removing negative prices. They do
    not remove its worst case.
- **The objective is the strong case.**
  - The other notes ask the objective to carry a per-start cost, a power-dependent efficiency or
    overhead, soft floors or a terminal value (O1), a wear hold cost, caps as segment limits, a
    best-effort shortfall, a forecast markup and a latest-slot tie-break.
  - A price ranking cannot express most of these. The DP expresses all of them in one
    O(T·S·2) pass.
- **The DP fits a looser budget.**
  - With every term on, it takes 13 ms at 168 hourly slots with a 0.5 kWh grid, 26 ms at
    0.25 kWh, 41 ms for a mixed horizon (35 h of quarters, then hours) and 100 ms for 672
    quarters (E2, E3).
  - Coarser grids are **not** a free speed-up. At 15-minute slots they cost +1.6 % to +21 %, or
    give plans that miss a floor, unless rounding is conservative and the grid divides the slot
    energy (E3).
- **Recommendation.**
  - Exact DP, state (slot, SoC on a 0.25 kWh grid, on-state).
  - Hourly slots by default; mixed resolution where quarter prices are both known and billed.
  - A budget of about 50 ms in the executor.
  - Keep the corrected greedy and a brute-force DP as test oracles.

### Cited Findings
**What the notes established, and what they did not test**
- **Constant power.** The fixed greedy is exact for constant power, non-negative prices and no
  binding caps. D22 as written (cumulative "short", charging in time order up to a floor) was
  +7.6 % median and +63 % worst on 60 real weeks
  ([scheduling_algorithm.md §1](scheduling_algorithm.md), matroid argument from the
  [Rochester slides](https://www.cs.rochester.edu/~gildea/csc282/slides/C17-amortized.pdf)).
- **Taper.** The best greedy variant had a median gap of 0.01 %, p90 1.93 % and a maximum of
  5.44 % ([scheduling_algorithm.md §2](scheduling_algorithm.md)).
- **What that evidence did not cover.** Exp 3 used:
  - hourly 2025 **spot** prices, clipped at 0 for the main result, with no tariffs;
  - one assumed taper;
  - synthetic commute schedules.
  It did not test 15-minute prices
  ([scheduling_algorithm.md §2 Gaps, §7 Gaps](scheduling_algorithm.md)).
- **Timings** ([scheduling_algorithm.md §2](scheduling_algorithm.md)):
  - plain energy DP: 5.7 ms (168 × 1 h, 0.5 kWh) and 21 ms (672 × 15 min);
  - with a session-start state: 10.6 / 35 ms;
  - backtracking was not timed ("an estimate, not measured", same note §2 Inferences).
- **Untested claims elsewhere.**
  - research.md said the greedy "runs well inside the 10 ms budget". That was reasoning: the
    note's experimental greedy took 28 ms and 799 ms ([research.md](../../research.md),
    [scheduling_algorithm.md §2](scheduling_algorithm.md)).
  - The coarser grid option for 672 slots ([scheduling_algorithm.md §2, §7 O8](scheduling_algorithm.md))
    had its speed measured but not its plan quality.
- **Tariffs are half the value.**
  - Grid tariffs are hourly with a peak at 17–21. Ranking by spot alone costs 185–217 DKK/yr
    more than ranking by total price.
  - On about 70 % of nights the cheapest spot quarter falls outside the low-tariff block
    ([price_composition_denmark.md §5](price_composition_denmark.md)).
- **Billing resolution.**
  - Households on the default product are billed the hourly mean of the four quarters, so
    choosing quarters inside an hour earns them nothing.
  - Choosing quarters is worth about 45–75 DKK/yr to those on a quarter-hour product
    ([price_composition_denmark.md §3](price_composition_denmark.md), citing
    [Forbrugerrådet Tænk](https://taenk.dk/forbrugerliv/bolig/flere-elpriser-i-doegnet-giver-minimale-besparelser)).
- **Forecast resolution.** Forecasts (Carnot, elpriser.org) are hourly. Known prices reach
  about 11–35 h ahead ([price_forecast_uncertainty.md §1](price_forecast_uncertainty.md)).
  Mixed resolution is therefore the normal input
  ([home_assistant_data.md, price integrations](home_assistant_data.md)).
- **What the objective must carry, by note.**
  - **Power-dependent efficiency.** Efficiency falls at low power, from a 100–300 W auxiliary
    load. Partial hours should run at full power for part of the hour, never at low current.
    The 6 A minimum means no power between 0 and about 4.1 kW three-phase
    ([charging_physics_battery.md §2, §3, §7](charging_physics_battery.md)).
  - **Per-start cost.** A per-start cost instead of a hard minimum
    ([charging_physics_battery.md §3](charging_physics_battery.md)). A hard minimum slot made
    evcc miss a target (#33936)
    ([prior_art_software.md, evcc known problems](prior_art_software.md)).
  - **Latest-slot tie-break**, and wear for hours spent above about 55–70 % SoC
    ([charging_physics_battery.md §5](charging_physics_battery.md)).
  - **Forecast markup.** Additive, not a percentage
    ([price_forecast_uncertainty.md §4, §6](price_forecast_uncertainty.md)).
  - **Caps.** A cap should limit charging in the segment before a target, not the SoC carried
    through it, or a later target goes falsely PARTIAL
    ([scheduling_algorithm.md §7, D23 row](scheduling_algorithm.md)).
- **Home Assistant's event loop.** "A blocking call in the event loop stalls all of Home
  Assistant until it returns". "heavy computation" is listed among what blocks; such work is to
  run in the executor (`hass.async_add_executor_job`). The page states no time threshold —
  [HA contributors docs, blocking operations](https://contributors.home-assistant.io/core/internals/blocking-operations/).

**E1 — greedy against the exact DP on Danish total prices** ([e1b.py](experiments/panel_optimisation/e1b.py))

Setup:
- 150 paired random weeks, the same weeks for every price case.
- Car: 75 kWh. Taper of 11 kW to 60 kWh, 7 kW to 67.5 kWh, 3.5 kW above (the scheduling note's
  Exp 3 car and schedules).
- Algorithms: the corrected greedy ("cum + price-ordered trim") against the exact DP
  (`dp_energy_fast`, 0.25 kWh grid).
- A negative gap is grid rounding in the greedy's favour.

| Taper car | Slots | Median | p90 | p95 | Max | Max DKK/week | Weeks > 1 % worse | Mean optimum DKK/week |
|---|---|---|---|---|---|---|---|---|
| Spot | 1 h | 0.20 % | 4.15 % | 11.7 % | 39.3 % | 9.10 | 42 | 33.9 |
| Spot ≥ 0 | 1 h | 0.08 % | 1.63 % | 2.58 % | 15.5 % | 4.19 | 30 | 34.6 |
| **Total** | 1 h | 0.03 % | 1.49 % | 3.42 % | 15.0 % | 9.33 | 20 | 68.3 |
| Spot | 15 min | 0.04 % | 10.9 % | 17.2 % | (optimum ≈ 0) | 9.94 | 33 | 29.9 |
| Spot ≥ 0 | 15 min | 0.00 % | 1.42 % | 2.76 % | 18.5 % | 5.35 | 15 | 30.9 |
| **Total** | 15 min | 0.00 % | 0.86 % | 2.96 % | 8.55 % | 6.31 | 13 | 63.9 |

At constant 11 kW, on the same 150 weeks:
- total price, hourly and 15 min, and spot ≥ 0: **0 weeks worse**. This confirms the matroid
  result on real Danish totals.
- spot with its negative prices: worst 9.9–10.8 DKK a week. The cause is energy beyond the
  floors in negative hours, which a floors-only greedy cannot buy.

**E2 — the full DP: correctness and time** ([fulldp.py](experiments/panel_optimisation/fulldp.py), [e2.py](experiments/panel_optimisation/e2.py))
- **Correctness.**
  - On 25 real weeks the full DP agreed with `dp_energy_fast` within 7×10⁻⁴ DKK a week.
  - Re-simulating its backtracked plans gave the same cost, with every floor met (0 mismatches).
- **Timing with every term on.** The terms: a ramp in the first slot of a session, efficiency
  0.9 plus 0.3 kW overhead, a 0.2 kWh start cost, the tie-break, a wear hold cost above 45 kWh,
  soft floors, a terminal value, and backtracking.

  | Slots | Grid | States | Without the extras | Every term on |
  |---|---|---|---|---|
  | 168 × 1 h | 1.0 kWh | 75 | 6.0 ms | 6.6 ms |
  | 168 × 1 h | 0.5 kWh | 150 | 11.6 ms | 13.0 ms |
  | 168 × 1 h | 0.25 kWh | 300 | 23.3 ms | 25.8 ms |
  | 672 × 15 min | 1.0 kWh | 75 | 21.9 ms | 23.8 ms |
  | 672 × 15 min | 0.5 kWh | 150 | 45.9 ms | 50.0 ms |
  | 672 × 15 min | 0.25 kWh | 300 | 94.5 ms | 101.4 ms |

  The precompute (per-state slot reach and wall energy, by sub-step simulation) takes 0.4–1.9 ms.
  The extra terms add about 10 %. The on-state and backtracking roughly double the plain value
  pass of the scheduling note.

**E3 — what the speed-ups cost** ([e3.py](experiments/panel_optimisation/e3.py))

Setup: 60 weeks, total price, taper. The reference is the exact 15-minute DP at 0.25 kWh, which
took 101 ms. "inf" means that, re-simulated on the true (unrounded) values, the plan missed a
floor.

| Scheme | Median | p90 | Max | Time |
|---|---|---|---|---|
| Grid 0.275 kWh (divides 2.75 kWh) | +0.53 % | +1.73 % | inf (≥ 1 week) | 91 ms |
| Grid 0.5 kWh | +4.0 % | inf (> 10 % of weeks) | inf | 50 ms |
| Grid 0.55 kWh (divides 2.75 kWh) | +2.1 % | inf | inf | 45 ms |
| Grid 1.0 kWh | +21.9 % | inf | inf | 23 ms |
| Hourly DP (0.25 kWh), then each hour's energy put in its cheapest quarters | +0.58 % | +2.28 % | +4.19 % | 25 ms |
| Mixed: quarters for 35 h, then hours (0.25 kWh) | +0.45 % | +2.30 % | +5.08 % | 41 ms |
| Mixed, 0.55 kWh | — | — | — | 18.5 ms |

Coarse-grid gaps stay large after valuing extra carried energy at the reference plan's average
price (0.5 kWh: +4.0 %; 1.0 kWh: +20.7 %). The cause is truncation of each slot's reach to the
grid, not overbuying.

### Inferences
- **(reasoning) Steelman for keeping a corrected greedy.**
  - It is continuous (no grid), so it never has to round.
  - It is exact for what Danish totals plus constant power look like (E1: 0 of 300
    week-cases). The physics note doubts the 11 → 7.5 kW taper is real: it may be a phase drop
    ([charging_physics_battery.md §1](charging_physics_battery.md)). Without a taper the price
    case for the DP almost disappears.
  - It is easy to explain to users ("the cheapest hours").
  - Implemented incrementally, it is likely fast (unmeasured).
- **(reasoning) Why I still choose the DP.**
  1. **The objective.** Start costs and ramps are fixed costs per session: lot-sizing with setup
     costs, which a per-slot ranking cannot weigh
     ([scheduling_algorithm.md §2](scheduling_algorithm.md)). Soft floors, a terminal value,
     wear cost and caps on segments break the matroid structure
     ([scheduling_algorithm.md §1, §3](scheduling_algorithm.md)). Each would need its own
     heuristic bolted onto the greedy, and each bolt is a new place for a missed-target bug.
     The prior-art note found that every missed-target bug was in such add-on rules
     ([prior_art_software.md, "Ideas worth borrowing"](prior_art_software.md)).
  2. **One mechanism replaces three.** D23's chain check, pass 1 and pass 2 become one DP.
     Infeasibility is V = ∞, and best effort is a shortfall penalty
     ([scheduling_algorithm.md §2, §7](scheduling_algorithm.md)).
  3. **Determinism.** With a fixed tie-break the DP is deterministic, unlike a MILP stopping at
     a 1 % gap ([prior_art_software.md, emhass](prior_art_software.md)). That suits D10.
  4. **The taper is cheap to carry.** The DP needs only that `b + reach(b)` is non-decreasing in
     b, which any physical taper meets ([scheduling_algorithm.md §2, Exp 5](scheduling_algorithm.md)).
- **(reasoning) The formulation I recommend for `planner`.**
  - **State.** (t, b, o): slot boundary t; SoC index b on a grid of g kWh,
    S = capacity / g + 1 states; o = whether the previous slot charged. The initial o is
    `is_currently_charging`, so a running session pays no start cost (as the evcc optimiser and
    emhass's `def_current_power` do,
    [prior_art_software.md](prior_art_software.md)).
  - **Per-call precompute.** Do this once per distinct slot length L, by sub-step simulation of
    both curves at full power:
    - `reach_L[first][b]`, the highest SoC reachable in one slot, with first = 1 meaning the
      session-start ramp applies;
    - `Wall[b]`, the cumulative wall energy from 0 to b at full power, with
      `P_batt = η·P_wall − P_aux`.

    This is where D12's simulation lives. O8's `simulation_step_minutes` only sets the
    precompute's precision (about 1–2 ms), not the planning speed.
  - **Transition in an available slot.**
    - Idle: (b, ·) → (b, 0), cost 0.
    - Charge: (b, o) → (nb, 1) for b < nb ≤ min(reach_L[1−o][b], cap_t). Cost
      `p̂_t·(Wall[nb] − Wall[b]) + [o = 0]·start_kwh·p̂_t`, where `p̂_t` is the decision price
      (raw + additive markup + ε·(T − t)).
    - Because the cost is linear in Wall, the best predecessor of each nb is a sliding-window
      minimum of `V[b] − p̂·Wall[b]` (a monotone queue). That makes each slot O(S) per source.
  - **How the physical constraints fit.**
    - Partial slots are full power for part of the slot. This meets the 6 A minimum: there is
      never a power between 0 and the curve's power. It is also the efficient choice
      ([charging_physics_battery.md §3](charging_physics_battery.md)).
    - The overhead and the power-dependent efficiency are inside Wall.
  - **Unavailable slot** (absence, buffer): idle only.
  - **Events at a slot boundary.**
    - Hard floor: V = ∞ below it.
    - Soft floor: + penalty × shortfall.
    - Departure: shift b by the consumption, and o := 0.
  - **Every slot:** + wear hold cost × L × (kWh above the step), for the battery panellist to
    value.
  - **End of horizon:** − terminal value(b) (section 3).
  - **Complexity.** Time O(T·S·2) plus O(S·sub-steps) of precompute. Memory O(T·S)
    back-pointers, for example 273 × 300 × 3 ints.
  - **Output.** Backtracking gives energy per slot. Windows are maximal runs. Each partial slot
    starts late in its hour if the next slot charges, or early if the previous one did. Cost is
    reported at raw prices (D20).
- **(reasoning) Session-time effects.**
  - A soft-start ramp shorter than one slot is exact through `reach[first]`.
  - Heat derating that grows with session age would need session age in the state (2–3× the
    states). It is not worth it. Let the caller lower the curve, as D6 already does for
    temperature.
- **(reasoning) Resolution and budget: the scheme I choose.**
  - **Variable slot length in `PricePoint`** (`end` or `duration`), as the price and Home
    Assistant notes ask. The engine plans at the resolution it is given:
    - the integration passes **hourly** prices to households on the default hourly product. For
      them, hourly is exact for what they are billed ([price_composition_denmark.md §3](price_composition_denmark.md));
    - it passes **quarters only for known prices** to households on a quarter-hour product;
    - forecasts stay hourly.
  - **Size.** Worst case is about 140 quarters plus about 133 hours = 273 slots: 41 ms at
    0.25 kWh (E3). The common case of 168 hourly slots takes 26 ms at 0.25 kWh, or 13 ms at
    0.5 kWh. 0.5 kWh divides 11, 7 and 3.5 kWh per hour, so that grid is aligned for hourly
    slots of this car.
  - **Hourly DP plus quarter refinement** (E3: +0.58 % median, 25 ms) is a sound fallback if
    full quarter horizons are ever needed. It loses less than the quarter-versus-hour value
    itself (about 2 %, [price_composition_denmark.md §3](price_composition_denmark.md)).
  - **Reject** coarse grids as the speed knob.
  - **Grid rule.** Choose g so that full-power slot energy is a multiple of g where possible.
    Round conservatively: start SoC down, consumption and floors up, reach down. Then a plan is
    always physically feasible. My E3 runs used naive rounding and so show the failure mode.
  - **Budget.** Restate §7 as "≤ 50 ms on a desktop CPython for 168 hourly or about 300 mixed
    slots, called from the executor". The HA docs require heavy computation off the event loop
    in any case. A call every few minutes at 50 ms is negligible CPU (reasoning).
  - **10 ms is still reachable** at 168 hourly slots with g = 0.5 kWh and no on-state (5.7 ms in
    the scheduling note). If the maintainer insists on 10 ms, that is the configuration.
- **(reasoning) Does adding tariffs change the greedy-versus-DP gap?**
  - Yes, but not the verdict. Tariffs remove almost all negative totals: only 2 DK1 quarters in
    13 months ([price_composition_denmark.md §4](price_composition_denmark.md)). With them the
    floors-only gap of spot-based tests disappears. At 15 minutes the p90 gap fell from 10.9 %
    (spot) to 0.86 % (total).
  - The tail from the taper stays: up to 8.6–15 % in long-trip weeks.
  - So on Danish totals the greedy's loss is only taper-driven and rare. The DP is justified by
    the objective terms, not by price.

### Gaps
- **Hardware.** Timings are from this container. Raspberry Pi-class Home Assistant hosts were
  not measured, and several times slower is likely but unmeasured. This is the main risk to the
  50 ms figure.
- **Other inputs.** One taper, one DK1 grid company, synthetic schedules. DK2 and real calendars
  were not tested. A properly incremental greedy was not implemented or timed.
- **Overhead's effect.** The effect of the overhead term or a start cost on plan cost with real
  curves was not measured. Only E4's start-cost run exists.
- **Not tried.** A coarse-to-fine SoC band (DP at 1 kWh, then 0.25 kWh around that path), and
  a DP that interpolates between grid points.
- **No source.** I found no published source for Wagner–Whitin-type setup-cost DP; the
  Wikipedia pages I tried returned 404. The lot-sizing analogy stays reasoning, as in the
  scheduling note.

---

## 2. C8 — the missing designs: missed target, missing prices, consumption beyond targets, plan churn

### Takeaway
- **(a) Missed target.** The engine must accept an **overdue** target. Its deadline becomes
  "as soon as possible": a lateness penalty per slot, cap still respected, reason
  `TARGET_OVERDUE`. The integration keeps passing the target until it is met, the car is
  unplugged, or the user dismisses it. O10's lean "skip a target whose buffer starts in the
  past" would recreate evcc #24339.
- **(b) Missing or partial prices.**
  - Plan over all available time, never only "within the price data" as motor.md §6.2 says.
  - Fill slots without a price with a pessimistic price (the highest price given, plus the
    markup).
  - In Denmark the caller can almost always pass the tariff part, which is published months
    ahead.
  - With no prices at all, charge as soon as possible up to the floors.
- **(c) Consumption beyond the known targets.** The caller turns an assumed daily use into
  **soft demands**. The engine treats them as soft floors with a penalty, plus a terminal value
  (section 3).
- **(d) Churn.** Re-planning itself adds almost no churn (E4). The fragmentation is in each plan,
  from 15-minute prices. An engine-side start cost with the on-state as input cuts session
  starts from 3.0 to 1.2 a night for +0.19 % cost. Integration-side hysteresis is still needed,
  but for actuation limits, not for churn.

### Cited Findings
- **(a) How others fail and recover.**
  - evcc #24339: after a plan overran its deadline, the planner picked the next day's plan and
    stopped at 70–90 %. It was fixed with a plan lock that "caches the goal a soc-based plan has
    committed to" ([prior_art_software.md, evcc](prior_art_software.md), from
    [issue #24339](https://github.com/evcc-io/evcc/issues/24339) and `loadpoint_plan.go`).
  - evcc "keeps charging after the target time if the goal was missed".
  - emhass's template rolls a missed deadline to the next 05:00
    ([prior_art_software.md](prior_art_software.md)).
  - A stateless ChargeSmarter call after `target.at` "will no longer see that target … not
    covered by D10, L4 or O12" ([prior_art_software.md, Pitfalls 2](prior_art_software.md)).
  - O10 proposes to "skip with a warning a target whose buffer starts in the past"
    ([decisions.md](../../decisions.md)).
- **(b) Fallbacks elsewhere.**
  - evcc's "simple plan" charges in one block ending at the target when rates are missing. With
    a target beyond the rates it waits if the time after the rates suffices.
  - Tibber's fallback started 6 h before departure without optimisation
    ([prior_art_software.md](prior_art_software.md)).
  - Danish grid tariffs and Energinet rates are published in DataHub months ahead
    ([price_composition_denmark.md §1, §7](price_composition_denmark.md)).
  - Tomorrow's spot is known only after about 13:00 CET
    ([price_composition_denmark.md §3](price_composition_denmark.md)).
- **(c) Unannounced trips.**
  - Users rarely enter trips. Unannounced trips are the main reason for overrides
    ([driver_behaviour_ux.md §1, §3](driver_behaviour_ux.md), Electric Nation).
  - The forecast note's next-cheaper rule "needs an assumed daily consumption beyond the known
    targets, which the engine does not have"
    ([price_forecast_uncertainty.md §7](price_forecast_uncertainty.md)).
- **(d) Anti-churn in prior art and the literature.**
  - evcc's stateful rules ("don't stop an already running slot", "avoid re-start within [slot
    duration]", skipping short slots) live in the loadpoint, outside the pure planner.
  - The evcc optimiser feeds in the current on-state and makes fewer starts a cost-bounded
    preference ([scheduling_algorithm.md §4](scheduling_algorithm.md);
    [prior_art_software.md](prior_art_software.md)).
  - Actuation limits: Zaptec recommends not changing values more often than every 15 minutes;
    Škoda's API allows 20 requests per hour per VIN
    ([home_assistant_data.md](home_assistant_data.md)).
  - "No study was found that quantifies chattering or plan churn for a single home EV"
    ([scheduling_algorithm.md §4 Gaps](scheduling_algorithm.md)).
- **E4 — churn under re-planning every 15 minutes** ([e4.py](experiments/panel_optimisation/e4.py)).
  - **Setup.**
    - 120 random nights, 17:00 → 07:00, DK1 total quarter prices.
    - The floor is 45 kWh at 07:00 with no buffer. Start SoC is 22–35 kWh.
    - The truth delivers U(90 %, 100 %) of planned energy. The engine sees SoC rounded down to
      a whole percent.
  - **Results:**

  | Engine setting | Starts per night executed (max) | Starts in the first plan | Mean cost per night | Floor met |
  |---|---|---|---|---|
  | No start cost, no tie-break | 3.02 (7) | 2.98 | 18.772 DKK | 115/120 |
  | Tie-break to later slots only | 3.04 (7) | 2.99 | 18.751 DKK | 114/120 |
  | Start cost 0.3 kWh × price, on-state as input | 1.17 (2) | 1.17 | 18.807 DKK (+0.19 %) | 113/120 |
  | Start cost 1.0 kWh × price, on-state as input | 1.10 (2) | 1.10 | 18.872 DKK (+0.53 %) | 114/120 |

  The cost figures are energy cost only, without the start overhead itself.

### Inferences
- **(a) Missed target (reasoning).**
  - The engine stays pure. It accepts `ChargeTarget.at ≤ now` (and a target whose buffer has
    begun) as **overdue** and does not refuse or skip it.
  - In the DP: a soft floor at every slot boundary from now on, each with a large penalty per
    kWh short. The cheapest plan is then "as soon as possible to `target_soc`", capped.
  - It reports `TARGET_OVERDUE` with the shortfall.
  - The integration owns the memory (D10): it keeps passing the target, with the plan-lock
    semantics evcc needed, until it is met, unplugged or dismissed.
  - E4's 5–7 missed nights in 120 show why this matters. They came from under-delivery in the
    last planned slot, which re-planning cannot recover without time left.
  - Two consequences:
    1. Keep D8's buffer.
    2. Once inside the buffer with the floor unmet, charging is better than not, because an
       unplug stops it anyway. I propose an exception to D8: "inside the buffer and short →
       charge now". This is evcc's `planDeadlineCritical` priority
       ([prior_art_software.md](prior_art_software.md)). It changes D8, so it is the
       maintainer's call.
- **(b) Missing or partial prices (reasoning).**
  - Feasibility and the plan must use every available slot. Slots without prices get a decision
    price equal to the highest price given plus the largest markup. The DP then uses them only
    when priced slots cannot meet a floor, which removes evcc's implicit bet.
  - With no prices at all, the risk-minimising plan is as soon as possible up to the floors,
    with `INSUFFICIENT_PRICE_DATA`. E4 shows late plans are exposed to under-delivery. Tibber's
    fallback also starts early.
  - The integration should prefer passing tariff-only prices marked `is_forecast` over passing
    nothing. That keeps the 00–06 low-tariff block, about half the value
    ([price_composition_denmark.md §5](price_composition_denmark.md)).
- **(c) Beyond the known targets (reasoning).**
  - The caller generates recurring departures as it already does (D27). For "assumed daily
    use" it generates soft demands: `ChargeTarget(..., soft_penalty)`, or a new
    `ExpectedUse(at, energy_kwh)` with an absence.
  - The engine treats them as soft floors. Missing one never makes the plan PARTIAL; it is
    reported separately.
  - Section 3 gives the penalty and the terminal value.
- **(d) Churn (reasoning from E4).**
  - Executed starts (3.02) barely exceed those already in the first plan (2.98). Re-planning
    under SoC noise and under-delivery is not the problem. The cheapest-quarter plan is
    inherently fragmented.
  - The fix belongs in the engine as a cost: `start_overhead_kwh` × price, with
    `is_currently_charging` as the initial on-state. It is pure (D10), soft (D19, avoiding
    evcc's hard-minimum bug), unit-free (D3), and costs about 0.2 %.
  - A latest-slot tie-break alone does nothing for churn.
  - Integration hysteresis remains for actuation:
    - rate budgets and minimum dwell (Zaptec, Škoda);
    - read back and re-assert;
    - never let hysteresis override a deadline-critical state.

### Gaps
- E4 used one floor, no buffer, an assumed under-delivery distribution and quarter prices only.
  Forecast-to-known price changes (another churn source) were not simulated.
- The start overhead in kWh (0.1–0.3) is a tunable without measurement
  ([charging_physics_battery.md §3 Gaps](charging_physics_battery.md)).
- Whether a quarter-hour product user is actually billed the quarters was not verified
  ([price_composition_denmark.md §3 Gaps](price_composition_denmark.md)).

---

## 3. O1 as an optimisation: "value of stored energy" or "expected cost of the next days' need"? Where does the trend view enter?

### Takeaway
- **The right formulation is the expected cost of the coming days' need**, in two parts:
  1. inside the price and forecast horizon, the coming days' known or assumed demands are
     demands in the DP. Recurring departures are hard; assumed use is soft. Forecast hours are
     priced with a small **additive** markup.
  2. beyond the horizon, a **concave** terminal value. Each kWh is worth its replacement price
     up to the expected need, and nothing above it. A wear hold cost caps the incentive.
- **A flat "value of stored energy" is the degenerate case.** It assumes an unbounded need, so
  it is an O1(b)-style threshold rule.
- **E5, on 21 real daily decisions with real forecasts:**

  | Formulation | Share of the oracle's saving |
  |---|---|
  | Full chain over the forecast horizon, markup 0.05–0.10 DKK/kWh | 66–78 % |
  | Flat value | 4–47 % |
  | Percentile fill rule (O1c) | −5 to −30 % (worse than charging only the floors) |

- **The trend view enters only through the forecast prices in the horizon.** No separate trend
  switch is needed, as the forecast note found too.

### Cited Findings
- **The forecast note's trend test.**
  - Ranking days by forecast and charging "until the next forecast-cheaper day" recovered
    80–97 % of perfect-foresight savings, against 62–80 % for a binary trend switch.
  - Forecasts rank the coming days well: Spearman about 0.7–0.8, the cheapest day picked 50–71 %
    of the time.
  - Direction is a coin flip for moves under about 100 DKK/MWh.
  - The model was day-level, with the 2 cheapest hours, no schedule and no tariffs
    ([price_forecast_uncertainty.md §7](price_forecast_uncertainty.md)).
- **Markup.** Additive, about 50–100 DKK/MWh at the first forecast day, never above about one
  MAE. 300 DKK/MWh clearly cost money
  ([price_forecast_uncertainty.md §6, §7](price_forecast_uncertainty.md)).
- **Wear.** Calendar ageing runs in plateaus with a step at about 55–70 % SoC. Hours above the
  step matter. The physics note's lean is O1(a), with any surplus capped below the step
  ([charging_physics_battery.md §5](charging_physics_battery.md), citing
  [Keil et al. 2016](https://mediatum.ub.tum.de/doc/1651485/document.pdf)).
- **Behaviour.** Users fill up in cheap night hours. Unannounced trips drive overrides. The
  driver note favours O1(c), a percentile, or (b), a threshold
  ([driver_behaviour_ux.md §2, §7](driver_behaviour_ux.md)).
- **Prior art.** Prior art favours (b), a user price threshold: evcc smart cost limit, openWB
  eco, EV Smart Charging. The evcc optimiser values "the energy left in the batteries at the
  end" ([prior_art_software.md](prior_art_software.md);
  [scheduling_algorithm.md §4](scheduling_algorithm.md)).
- **E5 — rolling daily re-planning** ([e5.py](experiments/panel_optimisation/e5.py)).
  - **Setup.**
    - The engine re-plans at 13:00 every day, 21 decisions from 2026-10-06. It executes the
      first 24 h of each plan, in quarters.
    - Prices: actual DK1 quarters to the end of D+1, then the elpriser.org median forecast
      (hourly, D+2..D+9). Everything is converted to the total price with the same tariffs.
    - Car: 75 kWh with taper. Away 07–17 daily using U kWh, with a hard floor of 15 + U kWh at
      07:00.
    - Energy left at the end is valued at the oracle's average price.
  - **Policies.**
    - **Known-only:** O1(a), only targets within known prices.
    - **Chain + forecast:** hard daily targets through D+9 at forecast + markup m DKK/kWh,
      including VAT.
    - **Percentile 30 fill:** O1(c), a soft floor of 60 kWh at the end of known prices, valued
      at the 30th percentile of known prices.
    - **Flat value:** known-only plus a terminal value of 60 kWh at the median forecast price.
    - **Oracle:** the chain on actual prices.
  - **Results:**

  | Policy | Share of oracle saving, U = 6 / 12 / 20 kWh | Hours with SoC > 55 kWh over 21 days, U = 6 / 12 / 20 |
  |---|---|---|
  | Known-only, O1(a) | 0 / 0 / 0 % (1.142 / 1.197 / 1.240 DKK/kWh) | 0 / 0 / 0 |
  | Chain + forecast, m = 0 | 66 / 64 / 69 % | 133 / 136 / 39 |
  | Chain + forecast, m = 0.05 | 66 / 70 / 78 % | 134 / 140 / 41 |
  | Chain + forecast, m = 0.10 | 68 / 76 / 78 % | 188 / 166 / 42 |
  | Chain + forecast, m = 0.30 | 55 / 48 / 51 % | 240 / 245 / 65 |
  | Percentile 30 fill to 60 kWh, O1(c) | −30 / −14 / −5 % | 389 / 394 / 107 |
  | Flat value to 60 kWh | 4 / 25 / 47 % | 270 / 275 / 65 |
  | Oracle | 100 % (0.510 / 0.783 / 0.979 DKK/kWh) | 158 / 141 / 37 |

  Every floor was met in every run.

### Inferences
- **(reasoning) Steelmen.**
  - **(a) "never".** Simplest, and it minimises wear (0 h above 55 kWh in E5). The physics
    evidence supports it. Its cost: in E5 it paid 1.14–1.24 DKK/kWh where the chain paid
    0.71–1.04, so it forgoes most of the multi-day value. The Lund thesis puts that value at
    44–56 EUR a year ([price_forecast_uncertainty.md §5](price_forecast_uncertainty.md)).
  - **(b) A flat value or threshold.** Familiar from evcc, openWB and EV Smart Charging. It
    needs no forecast. But a kWh is worth its replacement price only until the next cheaper
    opportunity's need is covered. A flat value keeps buying beyond that, which is why E5's flat
    value captured as little as 4 %.
  - **(c) A percentile.** Needs no user input and adapts to tariff changes. But "cheap relative
    to the known 35 h" says nothing about the coming days. In a falling week it fills before
    cheaper days, which is why E5's percentile rule lost money in every case.
- **(reasoning) The formulation.** Minimise:

  raw cost + markup on forecast slots + start costs + Σ wear(b, t)·L
  + Σ soft-demand penalties − TerminalValue(b_T)

  subject to the hard floors and caps.
  - **Inside the horizon.** The DP's shadow price on stored energy is exactly "the cheapest
    future price at which this kWh's need could otherwise be met". That is the
    next-cheaper-day rule, computed rather than hand-coded.
  - **The trend view enters here and only here.** A rising week makes later slots dearer, so
    the DP buys now. A falling week makes it wait.
  - **The markup is the risk premium of the optimiser's curse.** In E5 a premium of 0.05–0.10
    DKK/kWh including VAT, about 40–80 DKK/MWh excluding VAT on spot, was best. 0.30 hurt.
    This agrees with the forecast note.
  - **Beyond the horizon,** the terminal value is concave piecewise linear, a step list like the
    power curves: `[(kwh_up_to, value_per_kwh), …]`, with value 0 above the assumed need
    between the end of the horizon and the next likely cheap period. The caller supplies it in
    its own price unit (D3). A default could be a fraction of the call's median forecast price
    (unvalidated).
- **(reasoning) The penalty for soft demands.**
  - It should be high enough that the DP buys the assumed need somewhere in the horizon, at the
    cheapest place, but finite, so a wrong assumption never makes the plan infeasible.
  - Using "the highest decision price in the horizon + 1" makes them lexicographically second
    to hard floors and first against cost.
  - Because the engine re-plans every call (MPC), an assumed trip that does not happen simply
    leaves energy that the next call sees in `current_soc`.
- **(reasoning) The wear tension is real and measured.**
  - The chain policies held the car above 55 kWh for 133–188 h over 21 days at low daily use,
    against 0 h for O1(a). A larger markup raises it further, because it biases the plan toward
    buying now.
  - So the wear hold cost (battery panellist's number) must be in the same objective. Then the
    DP buys ahead only when the price advantage exceeds the extra wear. The wear term costs
    O(S) per slot (E2).
  - The latest-slot tie-break and the wear cost point the same way.
  - E5 did not include a wear cost. Its effect on the saving is untested.

### Gaps
- **Small sample.** 21 decisions in one month, one forecast provider, DK1 only, no wear cost.
  The trend figures inherit the forecast note's small-sample warning. Carnot, which most Home
  Assistant users have, was not tested.
- **Terminal value beyond the forecast horizon.** It was not exercised: the horizon ran to D+9
  and the result was dominated by in-horizon demands.
- **Soft assumed demands.** E5 used hard daily targets, not soft demands with the proposed
  penalty. Their behaviour under unannounced trips was not simulated.

---

## 4. What exactly must the engine's contract gain or lose for the chosen algorithm?

### Takeaway
- **The contract gains:**
  - variable slot length;
  - a decision price separate from the raw price, with an additive markup;
  - a start overhead in kWh and a charging overhead;
  - soft demands and a terminal value;
  - wear hold costs, from the battery panel;
  - an SoC resolution tunable;
  - acceptance of overdue targets;
  - a per-target shortfall and partial-slot start times in the output.
- **It loses:**
  - the two-pass algorithm as a specification, with pass 1 kept only as reporting;
  - `min_session_kwh` as a threshold;
  - `simulation_step_minutes` as a speed knob;
  - the percentage markup, `is_top_up`, "hours within the price data";
  - the "about 1 ms expected" claim.

### Cited Findings
- Sources as in sections 1–3. Additionally:
  - `SET_CHARGE_LIMIT` should be a safety ceiling, not the means of cutting a partial hour
    (counterexample CE-B, [scheduling_algorithm.md §1, §7 O9](scheduling_algorithm.md)).
  - The Škoda API accepts limits only in steps of 10 %
    ([home_assistant_data.md](home_assistant_data.md)).

### Inferences
All rows are reasoning.

| Contract item | Change | Why |
|---|---|---|
| `PricePoint` | Add `end` (or `duration`). Mixed 15 / 60 min allowed. The API layer checks continuity | Plan at billed resolution (§1). O11 |
| Decision price | Keep `price` raw. Add an additive `forecast_markup_steps: [(hours_ahead, price_units)]`, or a per-point `decision_price`. Never a percentage | §3, [price_forecast_uncertainty.md §4](price_forecast_uncertainty.md). D20, O4 |
| `min_session_kwh` | Replace with `start_overhead_kwh` (cost = kWh × slot price). Soft by construction | E4. D19 |
| `charger_efficiency` | Keep, and add `charging_overhead_kw` (or efficiency by power) | Enters only through Wall[b]. [Physics §2, §7](charging_physics_battery.md) |
| `simulation_step_minutes` | Precompute only. Add `soc_resolution_kwh`, default 0.25, conservative rounding | E2, E3. O8 |
| Targets | Allow `at ≤ now` (overdue). Add `soft` / `penalty`, or a separate `ExpectedUse` | §2a, §2c |
| Terminal value | Optional `stored_energy_value_steps: [(kwh, value_per_kwh)]`, concave, default empty (= O1a) | §3 |
| Wear | Optional `soc_hold_cost_steps: [(soc, cost per kWh·h)]` | §3. Values from the battery panel |
| Caps (D7) | Define a cap as the ceiling on charging during the segment ending at that target. A slot's cap is the cap of the next target | Per-slot `cap_t` in the DP, avoiding false PARTIAL ([scheduling_algorithm.md §7](scheduling_algorithm.md)) |
| Tie-break | Specified: later slot first among equal decision prices | Deterministic (D10). [Physics §5](charging_physics_battery.md) |
| `is_currently_charging` | Becomes the DP's initial on-state | E4 |
| Feasibility (D23) | Still reported (`INFEASIBLE_TRIP_CHAIN`), now read from the DP (V = ∞ without the shortfall penalties). Best effort = DP with shortfall penalties | One mechanism |
| Output | Per-target planned SoC and shortfall. Windows with exact start and end (partial slots start late or early per continuity). Expected cost at raw prices. Reasons `TARGET_OVERDUE`, `NO_PRICE_DATA` fallback | §2 |
| Removed | `is_top_up` (O9). "Available = within price data". Percentage markup. "About 1 ms expected" (motor.md §7) | §1, §2b |
| §7 budget | "≤ 50 ms desktop CPython, 168 hourly or about 300 mixed slots, in the executor" | E2, E3. [HA docs](https://contributors.home-assistant.io/core/internals/blocking-operations/) |
| Test oracles | A brute-force DP (`dp_exact`) on small cases. The constant-power greedy must equal the DP when no extra terms are on. CE-A to CE-D as regression tests | [scheduling_algorithm.md §7](scheduling_algorithm.md) |

### Gaps
- Defaults for `start_overhead_kwh`, the soft penalty, the terminal value and wear costs are
  not calibrated.
- How users would set a terminal value in their currency (D3) is a UX question for the HA
  panellist.

---

## 5. Recommendations by decision and question, with confidence

### Takeaway
One table for the report writer. Confidence reflects how far the evidence (experiments plus
the notes) would survive realistic hardware, other cars and a longer price record.

### Cited Findings
- The evidence for every row is in sections 1–4 and the experiments E1–E5.

### Inferences
All rows are reasoning on that evidence.

| ID | Recommendation | Confidence | What evidence would change it |
|---|---|---|---|
| D22 / C3 | Replace pass 2 (and pass 1 as an algorithm) with an exact DP over (slot, SoC grid 0.25 kWh, on-state), with backtracking. Keep the corrected greedy only as a test oracle | **Medium-high** | A Raspberry Pi timing far above about 150 ms for 168 slots. Or a decision to drop start costs, terminal value and wear, when the corrected greedy suffices (E1: exact without taper) |
| D12 | Keep the step simulation, but only to precompute reach per state and wall energy. The ramp enters as first-slot reach. Heat derating stays with the caller | High | Logged sessions showing derating within one session large enough to change plans |
| O8 | Moot as a speed knob. The precision knob is `soc_resolution_kwh` = 0.25, conservative rounding. Never coarser than 0.5 at 15-minute slots | High (E3) | A DP variant with interpolation that makes coarse grids exact enough |
| O11 | Variable slot length; mixed resolution. Hourly for hourly-billed users, quarters only for known prices on quarter products | High | Evidence that default products bill quarters |
| §7 budget | 50 ms desktop CPython, in the executor. 10 ms is reachable only at hourly slots, g = 0.5, no on-state | Medium | Pi timings. HA guidance on executor job length |
| D19 | `start_overhead_kwh` × price per start, with the on-state from `is_currently_charging`. No hard minimum | High (E4: starts 3.0 → 1.2 a night, +0.2 % cost) | Measured start energy far above 1 kWh |
| D16 / D26 | Add `charging_overhead_kw`. It costs nothing in the DP (Wall[b]) | Medium | Measurements showing overhead below 1 % at the user's power levels |
| D7 / D23 caps | A cap limits charging in the segment before its target (per-slot cap). Feasibility read from the DP | Medium | A maintainer use case where a cap must bound SoC *at* the target |
| D20 / O4 | Additive markup in price units, about 0.05–0.10 DKK/kWh including VAT at the first forecast day | Medium-low (21 decisions) | A year of forecast-archive replays with schedules |
| O1 | "Expected cost of the next days' need": daily demands across the forecast horizon (hard if configured, soft if assumed), a concave terminal value beyond it, a wear hold cost. Default with no terminal value and no assumed use = O1(a). Reject the flat threshold and the percentile rule as primary mechanisms | Medium (E5 robust across U, but one month) | A longer replay where the percentile or flat rule matches the chain. A wear cost large enough to erase the 66–78 % |
| C8a | Accept overdue targets: charge as soon as possible, capped, `TARGET_OVERDUE`. The integration persists the target until met, unplugged or dismissed. Reject O10's "skip past targets". Propose "inside the buffer and short → charge" as a D8 exception | High (engine side); medium (D8 exception) | The maintainer's ruling on D8 |
| C8b | Plan over all available slots. Unpriced slots at a pessimistic price. Pass tariff-only prices as forecasts. As soon as possible up to the floors with no prices at all | Medium | Evidence that late fallbacks rarely miss (logged under-delivery) |
| C8c | Assumed use as soft demands with a finite, lexicographically high penalty | Medium | Simulation with unannounced trips showing hard recurring targets are as good |
| C8d | Churn: a start cost in the engine (main fix). Hysteresis in the integration for actuation limits, never above deadline-critical needs | High | Rolling tests with forecast-to-known transitions showing large flips |
| D10 | Supported: every term above is an input or a cost, not memory | High | — |
| O9 | Drop `is_top_up`. Partial slots by window times. `SET_CHARGE_LIMIT` only as a ceiling, rounded up to the car's step | Medium-high | Chargers that cannot start late within an hour |

### Gaps
- No real-hardware timing. One car curve. DK1 only. E5 covers one month.
- The battery panellist's wear values and the HA panellist's actuation limits are needed to
  finish the objective. Their absence does not change the algorithm choice.
