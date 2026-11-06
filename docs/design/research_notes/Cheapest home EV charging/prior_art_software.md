# Prior art: how existing smart-charging software plans cheap EV charging

Research for `research.md` item S2 and open question O5, done on 2026-10-28. Compared against
ChargeSmarter's design (`docs/design/motor.md`, `decisions.md`).

**How the sources were read.** Open-source code was read in clones made on 2026-10-28; links point
at the exact commit read, so line numbers stay valid:

| Project | Commit read (default branch) | Newest release tag seen |
|---|---|---|
| evcc | `9404d825d6a6` (2026-10-28) | 0.318.1 |
| evcc optimizer service | `556dcbf0b705` (2026-10-28) | - |
| evcc docs | `6153b322799b` (2026-10-27) | - |
| emhass | `179cbc2b584b` (2026-10-28) | v0.18.7 |
| openWB core | `ed4b1210e61b` (2026-10-28, `master`, development) | stable 2.2.4; 2.3.0-RC.2 |
| OpenEMS | `2955d2c87e6a` (2026-10-25, `develop`) | - |
| EV Smart Charging (HACS) | `cb6cc76972ec` (2026-08-31) | v2.6.0 |
| Predbat (HACS) | `83a4adad48fa` (2026-10-28) | v9.6.2 |

GitHub search (API and GraphQL) was blocked in this session, so issues and discussions were found
through web search and read one by one with a fetch tool, or found through commit messages in the
cloned history. Commercial products: documentation pages only. Some could not be opened. Every
place where that happened is marked.

Abbreviations in links below:
`EVCC` = `https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0`,
`EVOPT` = `https://github.com/evcc-io/optimizer/blob/556dcbf0b70534787179a509c4b5e8da2ed0789f`,
`EVDOCS` = `https://github.com/evcc-io/docs/blob/6153b322799bc67ebda0eadc57a569ec61904d20/src/content/docs/en`,
`EMHASS` = `https://github.com/davidusb-geek/emhass/blob/179cbc2b584bd935c96ad679ec4f32f496f412fb`,
`OWB` = `https://github.com/openWB/core/blob/ed4b1210e61b150c158690377cf919b56a82307b`,
`OEMS` = `https://github.com/OpenEMS/openems/blob/2955d2c87e6a49ea77d35eb3137b48533ce8b668`,
`ESC` = `https://github.com/jonasbkarlsson/ev_smart_charging/blob/cb6cc76972ecf3e7098f26d273a9ebade9c7f062`,
`PB` = `https://github.com/springfall2008/batpred/blob/83a4adad48fa913bc70b726d19ddd701faf28981`.
Expand a prefix to get the full URL.

## evcc: how does its planner choose hours, and how does it handle deadlines, floors, limits, modes and re-planning?

### Takeaway
The evcc planner is a small, stateless, greedy function. It sorts the price slots between now and
the target by price, breaks ties toward later slots, and takes slots until the required charging
time is covered. The target is the departure time itself: there is no completion buffer. It plans
for **one** target at a time. Everything stateful lives in the loadpoint layer around the planner:
locking a goal during overrun, finishing a started slot, skipping short slots. That layer is
where most of the recent planner bugs were. A hosted MILP optimizer now exists. Since October 2026
it can control loadpoints, but evcc still sends it only one goal per vehicle.

### Cited findings
**Inputs and the core algorithm**
- `Planner.Plan(requiredDuration, precondition, targetTime, continuous)` is the entry point. It
  gets rates from the tariff and returns a list of slots. It holds no plan between calls; its only
  fields are a logger, a clock and the tariff — [EVCC/core/planner/planner.go#L14-L19, #L97](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/planner/planner.go#L97).
- The "cheapest" strategy is a greedy selection. `optimalPlan` walks rates that are "sorted in
  ascending order by cost and descending order by start time (prefer late slots)". It appends
  slots until the required duration is used up. A partial last slot is shortened, and the first
  slot "should start as late as possible" — [EVCC/core/planner/planner.go#L35-L66](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/planner/planner.go#L35); tie-break in [EVCC/core/planner/sort.go](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/planner/sort.go).
- The "continuous" strategy slides a window over the slots. It picks the cheapest window of the
  required length and prefers the later start when costs are equal — [EVCC/core/planner/helper.go#L174](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/planner/helper.go#L174). The docs describe the choice: "_cheapest_ selects the cheapest hours, which may result in multiple starts and stops, while _continuous_ charges in one uninterrupted block just in time for departure" — [EVDOCS/features/plans.mdx](https://github.com/evcc-io/docs/blob/6153b322799bc67ebda0eadc57a569ec61904d20/src/content/docs/en/features/plans.mdx).
- Price slots are 15 minutes (`SlotDuration = 15 * time.Minute`) — [EVCC/tariff/slots.go#L11](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/tariff/slots.go#L11).
- Required duration comes from SoC, capacity and power. The estimator assumes
  `ChargeEfficiency = 0.85` and models a linear taper above a computed `taperSoc` — [EVCC/core/soc/estimator.go#L11, #L61-L78](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/soc/estimator.go#L61). Power is `EffectiveMaxPower`: the charger, vehicle, phase and circuit limits — [EVCC/core/loadpoint_effective.go](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/loadpoint_effective.go).

**Departure time, horizon and missing prices**
- When there is no tariff, no rates, or rate coverage too small for the required duration, the
  planner falls back to a "simple plan": one block from `targetTime - requiredDuration` to
  `targetTime` — [EVCC/core/planner/planner.go#L104-L127, #L162-L166](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/planner/planner.go#L104).
- When time is short (`Until(targetTime) <= requiredDuration`), it charges continuously from now —
  [planner.go#L134-L138](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/planner/planner.go#L134). The planner doc says: "If time goal can not be met, the planner creates a continuous plan until up to required duration" — [EVCC/core/planner/planner.md](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/planner/planner.md).
- **Target beyond the known prices.** If the time after the last known rate is enough for the
  whole charge, the planner returns no plan, so it waits. Otherwise it plans only the shortfall
  inside the known rates: `requiredDuration -= durationAfterRates` — [planner.go#L143-L158](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/planner/planner.go#L143).
- No completion buffer was found. The plan's horizon ends at `targetTime`.

**Preconditioning ("late charging")**
- `precondition` reserves the last part of the charge to run right before the target. The
  precondition slots are split off and appended whatever their price — [planner.go#L171-L201, splitPreconditionSlots #L208](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/planner/planner.go#L171). The docs give the purposes as a warm car in winter, climate control covered by the charger, and less time at high SoC. The late portion is "from 15 minutes up to 2 hours, or to _everything_" — [EVDOCS/features/plans.mdx](https://github.com/evcc-io/docs/blob/6153b322799bc67ebda0eadc57a569ec61904d20/src/content/docs/en/features/plans.mdx).

**Multiple plans**
- A vehicle has one static plan (id 1) and any number of repeating weekday plans (id 2+).
  `nextVehiclePlan` computes each plan's latest start (`End - requiredDuration`) and sorts by it.
  It returns the first plan whose SoC is not yet reached. Only that one plan is planned —
  [EVCC/core/loadpoint_effective.go#L38-L104](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/loadpoint_effective.go#L38). The docs say: "When multiple plans are active, the next matching time will be used" — [EVDOCS/features/plans.mdx](https://github.com/evcc-io/docs/blob/6153b322799bc67ebda0eadc57a569ec61904d20/src/content/docs/en/features/plans.mdx).
- The MILP optimizer models a per-slot goal vector (`s_goal: Optional[List[float]]`), with a
  penalty variable per slot for a goal it does not reach — [EVOPT/src/optimizer/optimizer.py#L235, #L394-L402, #L530-L541](https://github.com/evcc-io/optimizer/blob/556dcbf0b70534787179a509c4b5e8da2ed0789f/src/optimizer/optimizer.py#L394). evcc fills that vector with a single goal at the slot of the effective plan time — [EVCC/core/site_optimizer.go#L1585-L1611](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/site_optimizer.go#L1585).

**Floors, limits, modes and cost limits**
- Modes. A commit dated 2026-09-02, "Mode Redesign: rename pv to smart, replace minpv with always
  charge (BC) (#32490)", replaced the old off/now/minpv/pv modes. `Normalize` "maps deprecated
  pv/minpv to smart and the equivalent always charge state" — [EVCC/api/chargemodestatus.go#L13-L29](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/api/chargemodestatus.go#L13); commit seen in `git log`. The docs now list **Off / Smart / Fast**. "In these modes no rules apply, so an EV charger in **Fast** mode behaves like a charger without evcc." "All automatic decisions happen in **Smart** mode" — [EVDOCS/features/modes.mdx](https://github.com/evcc-io/docs/blob/6153b322799bc67ebda0eadc57a569ec61904d20/src/content/docs/en/features/modes.mdx).
- The decision order in `Loadpoint.Update`:
  1. not connected → off;
  2. welcome charge;
  3. `ModeOff` → off;
  4. `minSocNotReached || plannerActive` → `fastCharging()`;
  5. limit energy / limit SoC reached → stop;
  6. `ModeNow` → fast;
  7. `ModeSmart`: optimizer suggestion, else smart cost limit → fast, else smart feed-in, else PV surplus.

  — [EVCC/core/loadpoint.go#L2648-L2745](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/loadpoint.go#L2673).
- **Minimum SoC (emergency floor).** Below `minSoc` the car charges at full power "as quickly as
  possible", "If necessary, also with energy from your home battery or from the power grid". If
  the SoC is unknown at plug-in, "the system assumes that your vehicle is empty" — [EVDOCS/features/limits.mdx](https://github.com/evcc-io/docs/blob/6153b322799bc67ebda0eadc57a569ec61904d20/src/content/docs/en/features/limits.mdx); code in `minSocNotReached` — [EVCC/core/loadpoint.go#L1212](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/loadpoint.go#L1212).
- **Limit SoC (cap).** "if you select a limit of 80%, charging stops as soon as this charge level is
  reached" — [EVDOCS/features/limits.mdx](https://github.com/evcc-io/docs/blob/6153b322799bc67ebda0eadc57a569ec61904d20/src/content/docs/en/features/limits.mdx). With the optimizer in charge, the code says "a plan goal above the session limits is the optimizer's to reach" — [EVCC/core/loadpoint.go#L2640](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/loadpoint.go#L2640).
- **Smart cost limit.** Independent of any plan, in Smart mode the car charges at full power
  whenever the current rate is `<= limit` — [EVCC/core/loadpoint_smartcost.go](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/loadpoint_smartcost.go); "the vehicle charges from the grid whenever the price or CO₂ intensity is below it" — [EVDOCS/features/modes.mdx](https://github.com/evcc-io/docs/blob/6153b322799bc67ebda0eadc57a569ec61904d20/src/content/docs/en/features/modes.mdx). It stops at the limit SoC (decision order above).
- **Solar.** "The planner is only active in **Smart** mode. Self-produced solar energy continues to
  be preferred. If your own energy is not enough, the rest is charged from the power grid" — [EVDOCS/features/plans.mdx](https://github.com/evcc-io/docs/blob/6153b322799bc67ebda0eadc57a569ec61904d20/src/content/docs/en/features/plans.mdx).
- **Forecast prices.** A `merged` tariff appends a secondary (forecast) tariff where the primary
  ends ("Primary rates are used where available, secondary fills gaps after primary ends"). Both
  are returned as plain `api.Rates`, with no markup and no flag — [EVCC/tariff/merged.go](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/tariff/merged.go). The `stekker` tariff reads "epex-forecast" — [EVCC/tariff/stekker.go](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/tariff/stekker.go).

**Re-planning and hysteresis (all in the loadpoint layer, not the planner)**
- `plannerActive()` calls the planner on every cycle and then applies stateful rules:
  - a slot shorter than one slot minus 1 minute is skipped when the plan was not already active
    and a later slot follows ("short slots cost an extra start/stop cycle");
  - once active, it continues until the end of the running slot;
  - it continues when the remaining duration is under one slot;
  - it avoids a restart when the next start is within one slot;
  - it keeps charging after the target time if the goal was missed.

  — [EVCC/core/loadpoint_plan.go#L151-L286](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/loadpoint_plan.go#L245).
- `PlanLock` "caches the goal a soc-based plan has committed to, so that an overrunning plan keeps
  charging towards that goal instead of jumping to the next plan" — [EVCC/core/loadpoint_plan.go#L17-L26](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/loadpoint_plan.go#L17).
- The optimizer is re-solved every 5 minutes in automatic mode (`optimizerInterval = 5 * time.Minute`)
  — [EVCC/core/site_optimizer.go#L480](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/site_optimizer.go#L480). The docs describe the service as "**stateless**", calling `optimizer.evcc.io` and needing a sponsorship. They also say it is "currently informational only" — [EVDOCS/features/optimizer.mdx](https://github.com/evcc-io/docs/blob/6153b322799bc67ebda0eadc57a569ec61904d20/src/content/docs/en/features/optimizer.mdx). The code contradicts the last point: commit `f0569795` "Optimizer: add automatic mode (#32881)", dated 2026-10-11, lets an optimizer suggestion drive start/stop. The planner then only "backstops" it through `planDeadlineCritical` — [EVCC/core/loadpoint_optimizer.go#L104-L136](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/loadpoint_optimizer.go#L104), [EVCC/core/loadpoint.go#L2641-L2649](https://github.com/evcc-io/evcc/blob/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/loadpoint.go#L2641). The docs page has probably not caught up with the code.
- The optimizer's own explanation text: "The solver picks the cheapest slots before that time, in
  any order: among equally cheap slots which one it takes is arbitrary, except that fewer charge
  starts are preferred". "Breaking a goal ... costs a penalty far above any price, so it only
  happens when there is no other way" — [EVOPT/src/optimizer/explain.py#L46-L50](https://github.com/evcc-io/optimizer/blob/556dcbf0b70534787179a509c4b5e8da2ed0789f/src/optimizer/explain.py#L46).

**Known problems (issues, discussions, commits)**
- Issue #24339, "Repeating plans: charging stops on plan overrun" (Oct 2025 – Feb 2026). A plan
  overran its deadline. The planner then selected the next day's plan, which had no remaining need,
  and stopped charging at 70–90 % instead of 100 %. Suspected reasons for the overrun: power
  falling at the end of the charge, home load management, cold batteries. A maintainer: "Prio 1
  muss aber sein, dass der Planner das Ziel trifft" ("the first priority has to be that the planner
  hits the target"). Fixed by the plan lock in PR #26529 — [issue #24339](https://github.com/evcc-io/evcc/issues/24339), [PR #26529](https://github.com/evcc-io/evcc/pull/26529).
- Discussion #33936 (Sep–Oct 2026). A plan needing about 7 minutes was skipped repeatedly as "slot
  too short", even after "insufficient time until target". The car reached its goal about 7
  minutes late. Bug #34466 followed: "every plan needing less than 14m is a single trimmed slot
  without successor, so it was always skipped". The fix in PR #34604 skips a short slot only if a
  later slot follows — [discussion #33936](https://github.com/evcc-io/evcc/discussions/33936), [PR #34604](https://github.com/evcc-io/evcc/pull/34604).
- Planner commit history includes:
  - "fix plan charging too early when preconditioning" (#27299);
  - "allow skipping single expensive slot" (#27298);
  - "add tolerance for single slot use" (#26814);
  - "continue a 100% plan as long as the vehicle is connected" (#26203);
  - "send notification when plan overrun is detected" (#26054);
  - "guard against incomplete rates" (#26324);
  - "recompute charge plan immediately on vehicle-side plan changes" (#33467).

  — `git log -- core/planner core/loadpoint_plan.go` in the clone (commit subjects only; the
  linked PR bodies were not all read).
- Issue #14077, as summarised in a web-search result (not opened): overlapping plans on two
  loadpoints ignore a shared circuit limit, so the plans fail — [issue #14077](https://github.com/evcc-io/evcc/issues/14077) (**not opened; search snippet only**).

### Inferences (reasoning)
- evcc puts ChargeSmarter's D10 split into practice. `Planner.Plan` is pure apart from the clock
  and the tariff. All stickiness (plan lock, slot continuation, short-slot skip, restart
  avoidance, overrun) is in the caller. The bug list shows that this caller-side logic is where
  missed targets came from. ChargeSmarter's integration will need equally careful tests.
- evcc has no completion buffer. Its overrun rescue is reactive: keep charging after the deadline
  while connected. ChargeSmarter's D8 buffer is the proactive alternative.
- evcc's "target beyond prices" rule (wait if the time after the known rates is enough) is an
  implicit bet that unknown hours will be no worse. ChargeSmarter's D20 markup makes that bet
  explicit and tunable.

### Gaps
- The bodies of most planner PRs were not read; only commit subjects.
- No evcc issue or discussion asking for a completion buffer was found. Web search did not surface
  one, and GitHub search was not available.
- The evcc optimizer's full MILP (constraints for minimum SoC, charge power, start penalty) was
  only skimmed.

## emhass: how does it plan an EV as a deferrable load (LP formulation, MPC)?

### Takeaway
emhass solves one MILP over the whole household: PV, a home battery and deferrable loads. An EV is
modelled as a deferrable load that must receive a fixed energy (`hours × nominal power`) inside a
time window. emhass has no notion of SoC, departure buffer, minimum SoC or charge curve for the
EV; the caller converts all of these into energy and a window on every model predictive control
(MPC) call. That is a stateless "re-plan from fresh inputs" design like D10. The maintainer
declined a built-in EV module.

### Cited findings
- **Cost functions.** "profit", "cost" or "self-consumption". The objective sums
  `unit_LoadCost[i]*P_gridPos[i]` (and sell revenue) over the horizon — [EMHASS/docs/advanced_math_model.md](https://github.com/davidusb-geek/emhass/blob/179cbc2b584bd935c96ad679ec4f32f496f412fb/docs/advanced_math_model.md). The solver defaults to HiGHS: "Default to Highs for speed" — [EMHASS/src/emhass/optimization.py#L255-L259](https://github.com/davidusb-geek/emhass/blob/179cbc2b584bd935c96ad679ec4f32f496f412fb/src/emhass/optimization.py#L255).
- **A deferrable load** has a window mask (`mask[t] = 0 means load must be off`), a target energy
  in Wh with a Big-M on/off flag, and required timesteps for binary loads — [EMHASS/src/emhass/optimization.py#L648-L700](https://github.com/davidusb-geek/emhass/blob/179cbc2b584bd935c96ad679ec4f32f496f412fb/src/emhass/optimization.py#L648). Windows are set by `start_timesteps_of_each_deferrable_load` and `end_timesteps_of_each_deferrable_load`. The docs show "the example of two electric vehicles that need to charge, but which are not available during the whole prediction horizon" — [EMHASS/docs/advanced_math_model.md](https://github.com/davidusb-geek/emhass/blob/179cbc2b584bd935c96ad679ec4f32f496f412fb/docs/advanced_math_model.md).
- **The EV recipe.** "EMHASS treats an EV charger as a windowed deferrable load: a fixed energy
  amount that must be delivered before some end time". On each MPC call the caller computes
  `def_total_hours = kWh_remaining / charger_kW` and `end_timesteps = (deadline - now) / step` — [EMHASS/docs/study_cases/ev.md](https://github.com/davidusb-geek/emhass/blob/179cbc2b584bd935c96ad679ec4f32f496f412fb/docs/study_cases/ev.md).
- **Known limits, as the project documents them** — [EMHASS/docs/study_cases/ev.md](https://github.com/davidusb-geek/emhass/blob/179cbc2b584bd935c96ad679ec4f32f496f412fb/docs/study_cases/ev.md):
  - "Power modulation is not supported": a load is on at nominal power or off.
  - "Mid-session state is not forced": the optimizer may plan to stop and restart a charge already
    running; issue #605.
  - "No native vehicle-API integration".
  - "Opportunistic / surplus-only charging is awkward ... the optimizer treats the kWh-target as
    mandatory".
  - If the window cannot hold the energy, "EMHASS returns `optim_status: "Infeasible"` and
    publishes nothing".
- **Mid-session pin.** `def_current_power` pins timestep 0 to the charger's actual power and
  suppresses the "phantom startup penalty", so a manual or running charge is not planned off
  (#605 / PR #982) — [EMHASS/docs/cookbook/ev_evcc_executor.md](https://github.com/davidusb-geek/emhass/blob/179cbc2b584bd935c96ad679ec4f32f496f412fb/docs/cookbook/ev_evcc_executor.md).
- **Missed deadline.** "Once 05:00 passes, the Step 2 template sets the deadline to the next 05:00
  ... the leftover energy carries a next-day deadline" — [same cookbook](https://github.com/davidusb-geek/emhass/blob/179cbc2b584bd935c96ad679ec4f32f496f412fb/docs/cookbook/ev_evcc_executor.md).
- **Anti-fragmentation options**: `set_deferrable_startup_penalty` (cost per start),
  `set_deferrable_load_single_constant` (one block), minimum on and off times — [EMHASS/docs/config.md#L121-L147](https://github.com/davidusb-geek/emhass/blob/179cbc2b584bd935c96ad679ec4f32f496f412fb/docs/config.md).
- **Optional loads.** `deferrable_load_max_cost`: "A value above `0` makes the load **optional**:
  the optimizer schedules it only when its complete run can be done for less than that amount ...
  The cap is an all-or-nothing budget for the load's entire run, not a per-timestep price limit" — [EMHASS/docs/config.md#L188](https://github.com/davidusb-geek/emhass/blob/179cbc2b584bd935c96ad679ec4f32f496f412fb/docs/config.md).
- **MPC.** "Perform an optimization on the prediction horizon. Apply the first element ... Repeat
  at a relatively high frequency, ex: 5 min." On uncertainty: "The quality and accuracy of the
  optimization results will be inevitably linked to the quality of the forecast" — [EMHASS/docs/advanced_math_model.md](https://github.com/davidusb-geek/emhass/blob/179cbc2b584bd935c96ad679ec4f32f496f412fb/docs/advanced_math_model.md). Prices arrive as `load_cost_forecast` lists, for example from Nord Pool `raw_today` + `raw_tomorrow` — [EMHASS/docs/forecasts.md](https://github.com/davidusb-geek/emhass/blob/179cbc2b584bd935c96ad679ec4f32f496f412fb/docs/forecasts.md). No price-uncertainty markup was found.
- **Determinism.** "HiGHS is a MILP solver and stops once it is within lp_solver_mip_rel_gap of
  that optimum (default 0.01) ... strict run-to-run determinism needs a tight (or zero)
  lp_solver_mip_rel_gap" — [EMHASS/src/emhass/optimization.py#L66-L71](https://github.com/davidusb-geek/emhass/blob/179cbc2b584bd935c96ad679ec4f32f496f412fb/src/emhass/optimization.py#L66).
- **Discussion #789** (Apr–Jul 2026):
  - users want SoC targets at set times from a calendar, and surplus-only charging;
  - "Modeling the EV as a deferrable load does not map well to multi-day deadlines";
  - the maintainer: "They should remain separate tools that talk to each other through a generic
    agnostic layer"; the issue was labelled "wontfix" and moved to discussion #1033.

  — [discussion #789](https://github.com/davidusb-geek/emhass/discussions/789) (read through a fetch tool's summary).

### Inferences (reasoning)
- emhass shows the cost of exact optimisation: a solver dependency, a 1 % MIP gap by default
  (non-deterministic plans), and an "Infeasible" result with no fallback plan. ChargeSmarter's
  greedy, best-effort design (D9, D22) avoids all three.
- Several EV deadlines are separate deferrable loads with separate energies. No SoC chain links
  them. That is the gap D22's pass 1 fills.

### Gaps
- The exact constraint code for target energy with Big-M was not read line by line.

## openWB: how does "Zielladen" (scheduled charging) choose price-based hours?

### Takeaway
openWB plans for one plan at a time: the plan with the nearest end time. Without price data it
starts at the latest possible moment. With price-based charging on (`et_active`) it takes the
`1 + ceil(duration/slot)` cheapest slots before the target. Outside chosen slots it falls back to
PV surplus. When time runs out it raises the current. There is no buffer before the target time.
It may start up to 10 minutes before the latest start, and it treats a target as missed only 20
minutes after it.

### Cited findings
- **Plan data.** Each plan has a `time`, a frequency (once / daily / weekly), `limit` (`amount` in
  Wh, or `soc_scheduled` = the target and `soc_limit` = the maximum for surplus charging), a
  current, phases, and `et_active` — [OWB/packages/helpermodules/abstract_plans.py#L55-L95](https://github.com/openWB/core/blob/ed4b1210e61b150c158690377cf919b56a82307b/packages/helpermodules/abstract_plans.py).
- **Choosing the plan.** `_find_recent_plan` takes the active plan with the smallest remaining
  time to its end, skipping plans more than 20 minutes past. Constants: `BUFFER_AFTER_END_TIME =
  -1200  # nach mehr als 20 Min Überschreitung wird der Termin als verpasst angesehen` ("after
  more than 20 minutes over, the appointment counts as missed") and `BUFFER_START_EARLIER = 600  #
  10 Min vor dem geplanten Start kann begonnen werden` ("charging may begin 10 minutes before the
  planned start") — [OWB/packages/control/ev/charge_template.py#L347-L401](https://github.com/openWB/core/blob/ed4b1210e61b150c158690377cf919b56a82307b/packages/control/ev/charge_template.py#L347).
- **Duration.** `missing_amount = ((soc_scheduled - soc)/100) * battery_capacity / (efficiency/100)`.
  Duration = `missing_amount / (current * phases * 230)`. With switchable phases and no price
  tariff, it prefers 1 phase when 1-phase charging still fits in time — [charge_template.py#L445-L569](https://github.com/openWB/core/blob/ed4b1210e61b150c158690377cf919b56a82307b/packages/control/ev/charge_template.py#L445). Efficiency was added in 2026-05 ("scheduled charging: consider efficiency (#3393)", from `git log`).
- **Decision in `scheduled_charging_calc_current`** — [charge_template.py#L571-L725](https://github.com/openWB/core/blob/ed4b1210e61b150c158690377cf919b56a82307b/packages/control/ev/charge_template.py#L571):
  - SoC within [soc_scheduled, soc_limit]: charge on surplus only.
  - Within 10 minutes of the latest start (plus the SoC request interval): charge at the plan
    current.
  - Past the latest start: raise the current to `missing_amount / remaining time`, up to the
    maximum.
  - Otherwise, with `et_active`: charge now if the current slot is among the selected cheap
    slots, else surplus.
  - Without `et_active`: surplus until the computed start.
- **Choosing the cheap slots.** `ep_get_loading_hours(duration, remaining_time)` filters slots
  between now and the target. It orders them newest-first, then sorts stably by price, so ties go
  to later slots. It takes `1 + ceil(duration/slot)` slots and drops the extra one when it is not
  needed — [OWB/packages/control/optional.py#L227-L282](https://github.com/openWB/core/blob/ed4b1210e61b150c158690377cf919b56a82307b/packages/control/optional.py#L227).
- **Eco mode (price threshold).** Charge at full current when the current price is
  `<= eco_charging.max_price`, otherwise surplus, until an SoC or amount limit — [charge_template.py#L304-L345](https://github.com/openWB/core/blob/ed4b1210e61b150c158690377cf919b56a82307b/packages/control/ev/charge_template.py#L304).
- **Minimum SoC in PV mode.** `pv_charging.min_soc`: below it, charge at once at `min_soc_current`
  (instant charging) — [charge_template.py#L256-L302](https://github.com/openWB/core/blob/ed4b1210e61b150c158690377cf919b56a82307b/packages/control/ev/charge_template.py#L256).
- **Modes**: `scheduled_charging`, `time_charging`, `instant_charging`, `pv_charging`,
  `eco_charging`, `bidi_charging`, `stop` — [OWB/packages/control/chargemode.py](https://github.com/openWB/core/blob/ed4b1210e61b150c158690377cf919b56a82307b/packages/control/chargemode.py).
- **History of fixes**, from `git log` of these files: "handle concurrent plans" (#2458, 2025-06);
  "set next plan as active if current plan is fulfilled" (#2450); "fix plan selection" (#3024);
  "fix missed once plan" (#3012); "ignore passed plans" (#2955); "scheduled charging: increase
  buffer time by soc request interval after charge start" (#3160, 2026-03); "Refactor fix hour
  tariff price calculation for quarter hours" (#3145); "electricity pricing: update prices 4 times
  per day" (#3083).

### Inferences (reasoning)
- openWB's 10-minute early start and its SoC-request-interval widening are small, implicit
  buffers. They cover the same risks D8 names explicitly (stale SoC, slow finish). openWB does not
  forbid charging near the deadline.
- Like evcc, it plans one target at a time and repeats the selection on every control cycle. The
  only memory it uses is the plan list and the current SoC.

### Gaps
- No openWB forum thread or GitHub issue on Zielladen problems was read. Web search returned none,
  and GitHub search was blocked.
- The stable 2.2.4 code was not compared with `master`.
- Whether the new PV forecast feature (#3782) feeds scheduled charging was not found in
  `charge_template.py`.

## OpenEMS: how do its time-of-use and EV controllers plan?

### Takeaway
OpenEMS schedules **modes** per 15-minute period with a genetic algorithm (Jenetics). The modes for
an EV controller are ZERO, MINIMUM, SURPLUS and FORCE. Manual tasks pin a mode for a period. The
fitness function adds a run-length cost that penalises frequent mode changes. A "Smart" task with
`sessionEnergyMinimum` exists in the data model, but this code read found no use of it in the
fitness function.

### Cited findings
- **Energy scheduler terms**: a Mode is a Jenetics `Gene`, a Schedule a `Genotype`, an
  Optimization a `Population`. The global context "is typically recreated once per 15-minutes" — [OEMS/io.openems.edge.energy/readme.adoc](https://github.com/OpenEMS/openems/blob/2955d2c87e6a49ea77d35eb3137b48533ce8b668/io.openems.edge.energy/readme.adoc).
- **EVSE single controller modes**: `ZERO, MINIMUM, SURPLUS, FORCE` — [OEMS/io.openems.edge.controller.evse/src/io/openems/edge/controller/evse/single/Mode.java](https://github.com/OpenEMS/openems/blob/2955d2c87e6a49ea77d35eb3137b48533ce8b668/io.openems.edge.controller.evse/src/io/openems/edge/controller/evse/single/Mode.java). Params include session energy, session energy limit, and "scheduled tasks from JS Calendar" — [OEMS/io.openems.edge.controller.evse/readme.adoc](https://github.com/OpenEMS/openems/blob/2955d2c87e6a49ea77d35eb3137b48533ce8b668/io.openems.edge.controller.evse/readme.adoc).
- **Tasks.** `Payload.Manual(Mode)` and `Payload.Smart(int sessionEnergyMinimum)` — [OEMS/.../single/Types.java#L457-L492](https://github.com/OpenEMS/openems/blob/2955d2c87e6a49ea77d35eb3137b48533ce8b668/io.openems.edge.controller.evse/src/io/openems/edge/controller/evse/single/Types.java#L457). Tasks are expanded into 15-minute periods. Only controllers with Smart tasks are optimised. SURPLUS is the default mode. Mode priority per period: "TODO 1st Priority: One-Shot", then manual mode, then the simulated mode, then the configured mode — [OEMS/.../cluster/EshUtils.java#L200-L288](https://github.com/OpenEMS/openems/blob/2955d2c87e6a49ea77d35eb3137b48533ce8b668/io.openems.edge.controller.evse/src/io/openems/edge/controller/evse/cluster/EshUtils.java#L200).
- **Simulation.** FORCE gives the maximum energy per period, MINIMUM the minimum-power energy, and
  SURPLUS/ZERO nothing from the grid. Energy is capped by `min(EV capacity, sessionEnergyLimit)`
  minus the session energy already charged — [EshUtils.java#L49-L80, #L140-L150](https://github.com/OpenEMS/openems/blob/2955d2c87e6a49ea77d35eb3137b48533ce8b668/io.openems.edge.controller.evse/src/io/openems/edge/controller/evse/cluster/EshUtils.java#L49).
- `sessionEnergyMinimum` appears only in the record and its serializer: `grep` over
  `io.openems.edge.controller.evse/src` and `io.openems.edge.energy/src` found no other use.
- **Fitness**: grid buy cost and sell revenue per period, hard-constraint violations, a mode
  preference penalty, and a run-length cost: "Schedules that frequently change modes incur a
  higher cost" (`1/runLength²` per run). The search stops on `Limits.bySteadyFitness(500)` — [OEMS/io.openems.edge.energy/src/io/openems/edge/energy/optimizer/Simulator.java#L85-L446](https://github.com/OpenEMS/openems/blob/2955d2c87e6a49ea77d35eb3137b48533ce8b668/io.openems.edge.energy/src/io/openems/edge/energy/optimizer/Simulator.java#L403).

### Inferences (reasoning)
- From the code alone, OpenEMS's EV scheduling is cost minimisation over modes, with no
  enforced deadline. A deadline-meeting "Smart" payload looks unfinished. It is weak prior art for
  deadlines, but its run-length penalty is a clean way to discourage fragmented plans.

### Gaps
- The time-of-use controller for the home battery (`controller.ess.timeofusetariff`) was not read.
- Neither the OpenEMS user documentation nor FENECON's product docs for EV smart charging were
  read. Any deadline handling that lives outside the code read here is unknown.

## Home Assistant custom integrations: EV Smart Charging, Predbat and others

### Takeaway
EV Smart Charging (334 stars) is the closest prior art to ChargeSmarter. It is a Home Assistant
integration that picks the cheapest 15-minute slots before a daily ready time. It has a
price-independent minimum SoC, a price limit, "opportunistic" lower limits, immediate low-SoC and
low-price charging, and manual start/stop buttons. It re-plans only when the car is not charging.
Predbat (362 stars) plans the car only inside "low-rate" windows before one ready time, so it can
fall short. Neither has a completion buffer, multiple targets or forecast markup. A project
called "Nordpool planner" was not found.

### Cited findings
**EV Smart Charging** (jonasbkarlsson/ev_smart_charging; 334 stars and 55 forks on the repo page, fetched 2026-10-28 — [repo](https://github.com/jonasbkarlsson/ev_smart_charging))
- **Inputs**: a price sensor (Nord Pool, Energi Data Service, Entso-e and others), EV SoC, target
  SoC ("If not provided, 100 is assumed"), and a charging speed in % per hour. "Supports price
  information given with 15 minutes and 60 minutes intervals" — [ESC/README.md](https://github.com/jonasbkarlsson/ev_smart_charging/blob/cb6cc76972ecf3e7098f26d273a9ebade9c7f062/README.md).
- **Quarters needed**: `ceil((target - soc) / pct_per_hour * 4)`, capped at 96 — [ESC/custom_components/ev_smart_charging/helpers/coordinator.py#L214](https://github.com/jonasbkarlsson/ev_smart_charging/blob/cb6cc76972ecf3e7098f26d273a9ebade9c7f062/custom_components/ev_smart_charging/helpers/coordinator.py#L214).
- **Non-continuous mode**: sort the quarters between the start time and the ready time by price
  and take the cheapest N. Among equally priced quarters in the same hour as the most expensive
  one chosen, it moves the choice next to the neighbouring selected quarters. When too few quarters
  remain, it takes all of them — [coordinator.py#L39-L113](https://github.com/jonasbkarlsson/ev_smart_charging/blob/cb6cc76972ecf3e7098f26d273a9ebade9c7f062/custom_components/ev_smart_charging/helpers/coordinator.py#L39). Continuous mode slides a window to the minimum sum — [#L116-L170](https://github.com/jonasbkarlsson/ev_smart_charging/blob/cb6cc76972ecf3e7098f26d273a9ebade9c7f062/custom_components/ev_smart_charging/helpers/coordinator.py#L116).
- **Minimum SoC**: a second schedule to `min_soc` is computed. The price limit is not applied to
  it (`apply_limit=False`), and it is used when it has more quarters than the price-limited main
  schedule — [coordinator.py#L296-L392](https://github.com/jonasbkarlsson/ev_smart_charging/blob/cb6cc76972ecf3e7098f26d273a9ebade9c7f062/custom_components/ev_smart_charging/helpers/coordinator.py#L296). README: "minimum State-of-Charge level that should be reached by scheduled charging, independently of the electricity price" — [ESC/README.md](https://github.com/jonasbkarlsson/ev_smart_charging/blob/cb6cc76972ecf3e7098f26d273a9ebade9c7f062/README.md).
- **Price limit**: "charging will not be performed when the electricity price is above this limit.
  NOTE that this might lead to that the EV will not be charged to the target State-of-Charge".
  **Opportunistic**: the limit is lowered when "the last available price" is low. Type 2 sets the
  limit to a percentage of the last available price — [ESC/README.md](https://github.com/jonasbkarlsson/ev_smart_charging/blob/cb6cc76972ecf3e7098f26d273a9ebade9c7f062/README.md).
- **Immediate charging**: "Low SOC charging" ("charging will be done immediately if the EV SOC is
  below this level") and "Low price charging". "A typical use case is to charge the EV directly
  when returning home to a minimum level, and then do a complete charging using the scheduled
  charging when the price is lowest" — [ESC/README.md](https://github.com/jonasbkarlsson/ev_smart_charging/blob/cb6cc76972ecf3e7098f26d273a9ebade9c7f062/README.md).
- **Ready time**: "The latest time of the day for charging to reach the target State-of-Charge. If
  `None` is selected, charging will be optimized using all available price information" — [ESC/README.md](https://github.com/jonasbkarlsson/ev_smart_charging/blob/cb6cc76972ecf3e7098f26d273a9ebade9c7f062/README.md). There is one ready time per day, and no buffer.
- **Manual controls**: `button.manually_start_charging` and `button.manually_stop_charging`,
  "totally independent of the automatic charging". "Keep charger on" after completion enables
  preconditioning from the grid — [ESC/README.md](https://github.com/jonasbkarlsson/ev_smart_charging/blob/cb6cc76972ecf3e7098f26d273a9ebade9c7f062/README.md).
- **Re-planning**: the base schedule is rebuilt only when the SoC has risen above the SoC before the
  last charge, **and** the target is reached or (tomorrow's prices are valid or it is before the
  ready time) **and** (not currently charging, or the configuration changed) — [ESC/custom_components/ev_smart_charging/coordinator.py#L1056-L1077](https://github.com/jonasbkarlsson/ev_smart_charging/blob/cb6cc76972ecf3e7098f26d273a9ebade9c7f062/custom_components/ev_smart_charging/coordinator.py#L1056).

**Predbat** (springfall2008/batpred; 362 stars and 195 forks on the repo page, fetched 2026-10-28 — [repo](https://github.com/springfall2008/batpred))
- `plan_car_charging(car_n, low_rates)`. "Smart" mode sorts the low-rate windows by price
  (`reverse_time=True`). It takes windows clamped to [now, ready time] and skips those above
  `car_charging_plan_max_price`. It stops when SoC + 0.1 kWh reaches the limit, shortens the last
  window to 5-minute multiples, and applies `car_charging_loss` — [PB/apps/predbat/plan.py#L6226-L6305](https://github.com/springfall2008/batpred/blob/83a4adad48fa913bc70b726d19ddd701faf28981/apps/predbat/plan.py#L6226). A car is planned only when plugged in, using `low_rates_tariff` — [PB/apps/predbat/fetch.py#L1835-L1850](https://github.com/springfall2008/batpred/blob/83a4adad48fa913bc70b726d19ddd701faf28981/apps/predbat/fetch.py#L1835).
- **Shortfall, in the project's own words**: "`plan_car_charging()` stops at the ready time and can
  therefore return a plan short of `car_kwh` if the cheap-rate windows before then cannot hold it
  all" — [PB/apps/predbat/annual.py#L1332-L1360](https://github.com/springfall2008/batpred/blob/83a4adad48fa913bc70b726d19ddd701faf28981/apps/predbat/annual.py#L1332).
- **Low-rate threshold**: by default Predbat "will automatically look at the future import rates in
  the plan and determine the import rate threshold below which a slot will be considered" — [PB/docs/customisation.md](https://github.com/springfall2008/batpred/blob/83a4adad48fa913bc70b726d19ddd701faf28981/docs/customisation.md). With `car_charging_plan_smart` off, "all low-rate slots will be used in time order" — [PB/docs/car-charging.md](https://github.com/springfall2008/batpred/blob/83a4adad48fa913bc70b726d19ddd701faf28981/docs/car-charging.md).
- Predbat exposes `binary_sensor.predbat_car_charging_slot`. The user writes the automation that
  starts and stops the charger. With Octopus Intelligent, Octopus owns the car plan and Predbat
  reads its dispatches — [PB/docs/car-charging.md](https://github.com/springfall2008/batpred/blob/83a4adad48fa913bc70b726d19ddd701faf28981/docs/car-charging.md).

**Others**
- "nordpool_planner" or a similar planner by that name: **not found**. The web search did not
  return it. It returned generic cheapest-hours tools (kotope/aio_energy_management,
  TheFes/cheapest-energy-hours, jpulakka/nordpool_diff), which were not opened.

### Inferences (reasoning)
- EV Smart Charging's two schedules (a price-independent floor, plus a price-limited target)
  already put O1 option b into practice: charge beyond the floor only below a user threshold.
  Its README warning shows the trade-off users accept.
- Re-planning only when not charging is a simple hysteresis rule. It belongs in ChargeSmarter's
  integration layer, as D10 says.

### Gaps
- No issues or discussions of EV Smart Charging or Predbat were read.
- HACS install counts were not checked; the star counts come from the GitHub pages.

## Commercial products: what do Tibber, Octopus/Ohme, Easee, Zaptec and Monta claim?

### Takeaway
All of them claim the same basic contract: departure time plus target, charged in the cheapest
known hours. If time is short, they fall back to charging at once. Several have a minimum level
charged immediately, a price cap that may miss the target, and a manual "max/charge now" override
that ends when the car is unplugged. None of the pages read mentions a completion buffer, several
targets per car, or how forecast prices are handled.

### Cited findings
- **Tibber.**
  - A plan "is always set up based on how much energy your car needs, the historical charging
    speed, the departure time and the spot prices for the upcoming hours".
  - Departure time and battery level are set per car.
  - "if your car's current battery is lower than the minimum in the app, the car will always be
    charged right away until it reaches your minimum battery level".
  - Integrated cars are polled "every 15 minutes".

  — [Tibber Magazine, Smart Charging 2.0 (2024-09-27)](https://tibber.com/en/magazine/news/smart-charging-2.0).
  Norwegian product page: prices are known "opp til 36 timer i forveien" ("up to 36 hours ahead").
  If the charging current is low, the battery very low, or the driver home too late, "så blir det
  ingen smartlading, men i stedet full lading hele veien" ("there is no smart charging; it charges
  at full power all the way instead") — [tibber.com/no (redirected to /no/powerup/nio-lading)](https://tibber.com/no/store/produkt/nio-lading).
  Status incident (2025-04-16): a disruption "may have caused fallback schedules to be created,
  initiating charging 6 hours before the set departure time without optimization" — [status.tibber.com](https://status.tibber.com/incidents/rrll3y4fnrws). The English help-centre articles (support.tibber.com/en/articles/5597987, /8565405) returned **404: could not access**.
- **Octopus Intelligent Go with Ohme.** "Ensure Dynamic Charging is on with the amount of charge
  you'd like to add or the target you want to reach and a Ready by time". "Ohme and Octopus will
  work to charge at the cheapest and greenest times". The ready time must be "between 4am - 11am".
  Override: "tap Max Charge: Any charge added during a Max Charge in peak times will be billed at
  the peak rate". Six hours of cheap charging every night — [Octopus FAQ](https://octopus.energy/blog/intelligent-ohme-faqs/). The Octopus help article only says "use the app to tell us when you need the car charged and how much charge you need" — [Octopus help](https://octopus.energy/help-and-faqs/articles/how-does-intelligent-octopus-go-work/). Ohme's own support pages returned **403: could not access**. Statements about Ohme's price cap and Max Charge reverting on unplug came only from a search snippet and are not used here.
- **Easee.** Product page: "Set when the electric car is to be charged, for example when the
  electricity is cheapest". "Start and stop charging at any time". "Smart Charging (available in
  the UK, Norway and Denmark)" — [easee.com app page](https://easee.com/en/products/services/app/). Easee help-centre articles returned **403: could not access**, so whether Easee has a departure deadline is not established.
- **Zaptec.** Help article 9556497060753 ("Eco Mode") returned **404**, and zaptec.com returned
  **429: could not access**. A search snippet described Eco Mode as charging in the cheapest time in
  the next 24 hours, from departure time and kWh needed. That is **unverified** and not used as a
  finding.
- **Monta.** "SmartCharge schedules charging to use the cheapest electricity hours. Set a departure
  time and target battery level ... Requires a car integration". "Charging rules" work separately:
  "charge only between 23:00 and 06:00, or only when electricity costs less than 0.15 €/kWh".
  There is an optional "Delayed start", a slider "balancing between low electricity cost, reduced
  CO₂ emissions, and use of renewable energy", and spot prices "60-minute or 15-minute
  intervals" — [Monta help centre](https://monta.com/help/en_US/charging-at-home/smart-charging-explained).

### Inferences (reasoning)
- The commercial products state D9's best-effort rule outright (Tibber: full charge when time is
  short). A minimum level charged at once is common (Tibber), matching `min_safety_soc`.
- Tibber's fallback in the incident (charge 6 hours before departure without optimisation) is a
  degraded mode a stateless engine could also offer for "no price data". evcc's "simple plan" is
  the same idea.

### Gaps
- Ohme, Easee and Zaptec primary documentation could not be accessed.
- No vendor documents the algorithm, buffers or forecast handling.

## Comparison against ChargeSmarter's decisions: what does prior art support or contradict for D7, D8, D10, D19, D20, D22, O1, O12?

### Takeaway
Prior art strongly supports D9 (best-effort), the emergency floor, a user price threshold for O1,
keeping manual modes in the integration (O12), and a stateless planner with hysteresis in the
caller (D10). D22 (several chained targets) and D20 (a forecast markup) have **no** precedent in the
rule-based tools read. Only LP optimizers can express several goals: evcc's optimizer accepts a goal
per slot, but evcc sends one. D8 (an absolute buffer) also has no direct precedent. The evidence
shows the problem it addresses: late finishes and overruns. It also conflicts with the popular
"late charging / preconditioning" feature.

### Cited findings

**Comparison table** (sources are in the sections above)

| Aspect | ChargeSmarter | evcc | emhass | openWB | OpenEMS | EV Smart Charging | Predbat | Commercial |
|---|---|---|---|---|---|---|---|---|
| Algorithm | Greedy cheapest-first, simulated with curves (D12, D22) | Greedy sort by price, ties → later; or cheapest continuous window; MILP optimizer (hosted) | MILP (HiGHS default) over the whole house | Greedy: cheapest `ceil(d/slot)+1` slots | Genetic algorithm over modes | Greedy cheapest quarters, or continuous window | Greedy over "low-rate" windows only | Not documented |
| Stateless call | Yes (D10) | Planner yes; loadpoint keeps lock and slot state | Yes per MPC call | Recomputed each cycle | Re-optimised each 15 min | No: keeps a schedule, re-plans only when not charging | Recomputed each cycle | Unknown |
| Targets | Many, chained (D22) | One at a time (earliest latest-start); optimizer accepts a goal per slot but gets one | One window per deferrable load, no SoC chain | One (nearest end time) | Session energy limit; Smart minimum unused | One daily ready time | One ready time per car | One departure per car (Tibber per car) |
| Completion buffer | Absolute, 20 min (D8) | None; "late charging" does the opposite | None (caller sets end step) | None; may start 10 min early; missed after 20 min | None | None | None | None stated |
| Cap / target | Per-target cap, soft default 80 % (D7) | Limit SoC (session/vehicle) plus plan SoC | Energy only | `soc_scheduled` (target) and `soc_limit` (surplus cap) per plan | Session energy limit | Target SoC entity (default 100) | `car_charging_limit` | Target per car |
| Emergency floor | `min_safety_soc` | `minSoc` → full power now | None | PV `min_soc` → instant | MINIMUM mode | Low-SoC charging | Not found | Tibber minimum → at once |
| Idle floor in cheap hours | `min_idle_soc` | Not found | Not found | Not found | Not found | `min_soc` scheduled in cheapest quarters, price-independent | Not found | Not found |
| Forecast prices | Markup by hours ahead (D20) | `merged` tariff, treated as known | Inputs as given | Not found | Not found | Today and tomorrow only | Not found | Tibber: known up to 36 h |
| Minimum session | Soft `min_session_kwh` (D19) | Skip slot < 14 min if a later slot follows | Startup penalty, minimum on/off, single block | Not found | Run-length cost | Not found | 5-minute rounding | Unknown |
| Price limit beyond need | Open (O1) | Smart cost limit | `deferrable_load_max_cost` (optional load) | Eco `max_price` | Not found | Price limit, opportunistic, low-price charging | `plan_max_price` (also limits the target) | Monta price rules; Ohme price cap (unverified) |
| Manual override | Integration (O12) | Modes Off / Smart / Fast | `def_current_power` pin | Modes instant / stop / ... | Manual tasks pin a mode | Start/stop buttons | Automation on slot sensor | Max Charge (Ohme), start/stop (Easee) |
| Solar | Integration (D13) | Smart mode: surplus first, plan fills the rest | In the LP with a PV forecast | Surplus outside cheap slots | SURPLUS mode | Not found | Whole-house plan | Tibber Solar Charging (snippet only) |
| No prices / infeasible | Plans as far as it can, reports | "simple plan" (latest start); continuous from now when late | "Infeasible", publishes nothing | Raises current past latest start | - | Takes all remaining quarters | Shortfall (logged) | Tibber: full charge |

**Per decision**
- **D7 (hard caps per target, soft default 80 %).**
  - *Supports*: openWB keeps a target (`soc_scheduled`) and a separate cap (`soc_limit`) on each
    plan. evcc has a limit SoC distinct from the plan SoC.
  - *Contradicts in part*: when evcc's optimizer is in control, "a plan goal above the session
    limits is the optimizer's to reach". There, the plan beats the limit, where in ChargeSmarter
    the target's cap wins.
  - The default target is 100 % in EV Smart Charging ("If not provided, 100 is assumed"). evcc's
    docs use 80 % only as an example.
- **D8 (absolute 20-minute buffer).**
  - *No precedent found* in evcc, emhass, openWB, OpenEMS, EV Smart Charging, Predbat, or the
    commercial pages read.
  - *Evidence of the need*: evcc #24339 (overruns blamed on the power drop at the end, load
    management, cold batteries), evcc #33936 (7 minutes late), openWB's 10-minute early start and
    SoC-interval widening (#3160), evcc's overrun notification and "continue after target".
  - *Tension*: evcc's "late charging" deliberately charges right before departure for
    preconditioning and battery care. EV Smart Charging's "keep charger on" also targets
    preconditioning. An absolute no-charge buffer rules this out unless the integration handles
    preconditioning separately, as feature-candidates.md already says.
- **D10 (a pure function).**
  - *Supports*: evcc's `Planner.Plan` is a function of rates, duration, target and clock. The
    evcc optimizer service is "**stateless**". emhass re-solves from fresh runtime parameters on
    each MPC call. In all of these, stickiness lives in the caller: evcc's plan lock, slot
    continuation and short-slot rules; EV Smart Charging's re-plan only when not charging.
  - *Caution*: in evcc that caller-side state is where the missed-target bugs were (#24339,
    #33936).
- **D19 (soft minimum session energy).**
  - *Supports softness*: evcc's short-slot rule had to gain exceptions twice (#26814, #34604). Its
    hard form made a 7-minute plan miss its target. emhass and OpenEMS express the same wish as a
    cost (start penalty, run-length cost) rather than a hard rule.
  - No project uses an energy threshold. evcc uses time (one slot minus a minute).
- **D20 (forecast markup).**
  - *No precedent found.* evcc merges forecast and known prices without telling them apart.
    emhass relies on frequent re-solving (MPC). EV Smart Charging uses only published day-ahead
    prices. Tibber states it uses prices known up to 36 hours ahead.
  - The closest idea: when the target lies beyond the known prices and there is enough time after
    them, evcc's planner simply waits.
- **D22 (cheapest first over the whole horizon, several targets).**
  - *Supports the greedy core*: evcc, openWB, EV Smart Charging and Predbat all sort slots by price
    and take the cheapest.
  - *No rule-based precedent for chained targets*: evcc picks the plan with the earliest latest
    start, openWB the nearest end time, the others have one ready time. emhass has several windows
    but no SoC chain. evcc's optimizer can take a goal per slot (`s_goal` vector) but evcc fills
    only one.
- **O1 (charge beyond the floors when cheap).**
  - *Prior art favours option b*, a user price threshold: evcc's smart cost limit (up to limit
    SoC), openWB's eco `max_price`, EV Smart Charging's price limit and low-price charging, Monta's
    "charging rules", emhass's optional load under a cost budget.
  - EV Smart Charging adds "opportunistic" variants tied to the last available price, which is
    close to option c (a relative threshold).
- **O12 (manual controls in the integration).**
  - *Supports*: every project keeps manual control outside the planner. evcc: Off / Fast modes, and
    "Fast mode behaves like a charger without evcc". EV Smart Charging: start/stop buttons
    "totally independent of the automatic charging". Octopus/Ohme: Max Charge. Easee: "Start and
    stop charging at any time". emhass: a `def_current_power` pin so a manual charge is not
    planned off.

### Inferences (reasoning)
- ChargeSmarter's chained multi-target planning is its main difference from every rule-based tool
  read. It needs its own tests against an exact optimum (S4). No prior project can serve as an
  oracle, except an LP like emhass or evcc-io/optimizer run offline.
- D8's buffer and preconditioning can both stand if the integration treats preconditioning as a
  separate load in the last minutes. This is reasoning; no project combines the two.

### Gaps
- No study was found that measures how often greedy single-target planners miss their deadline.
  The issues show that it happens, not how often.

## Ideas worth borrowing, and pitfalls to avoid

### Takeaway
Borrow these: a later-slot tie-break, a start/fragmentation cost rather than a hard minimum, a
fallback plan when prices are missing, a price-independent floor schedule beside a price-limited
target, and session-scoped manual overrides. Avoid these: hard minimum-run rules near a deadline,
dropping a missed target on the next cycle, treating forecasts as known, price caps that silently
miss targets, and an optimizer that returns nothing when infeasible.

### Cited findings
**Ideas**
1. **Tie-break toward later slots.** evcc sorts equal prices by later start, and its first slot
   "should start as late as possible". openWB orders by date in reverse before a stable sort by
   price. Both are cited above.
2. **Penalise fragmentation instead of forbidding it.** OpenEMS's run-length cost
   (`1/runLength²`), emhass's `set_deferrable_startup_penalty`, and evcc optimizer's "fewer charge
   starts are preferred" (cited above). For ChargeSmarter's `scoring` module this could be a
   tie-break among equal-cost choices (reasoning).
3. **"Continuous" as an option.** evcc and EV Smart Charging both offer cheapest-continuous next to
   cheapest-fragmented (cited above). This fits the deferred "window strategies".
4. **Fallback when prices are missing.** evcc's "simple plan" charges at the latest start before
   the target. Tibber's fallback starts 6 hours before departure (cited above). ChargeSmarter now
   only warns `INSUFFICIENT_PRICE_DATA`; a defined fallback would make the warning actionable
   (reasoning).
5. **Floor and price-limited target as two schedules.** EV Smart Charging computes a
   price-independent `min_soc` schedule and a price-limited target schedule, and uses whichever
   charges more (cited above). This is a concrete pattern for O1 option b together with
   `min_idle_soc`.
6. **Session-scoped overrides.** evcc's "Always charge" has a "1x" button that "switches off
   automatically when the vehicle is disconnected" — [EVDOCS/features/modes.mdx](https://github.com/evcc-io/docs/blob/6153b322799bc67ebda0eadc57a569ec61904d20/src/content/docs/en/features/modes.mdx). A model for O12's "charge now" and "pause".
7. **Account for a stale SoC in timing.** openWB widens its start window by the SoC request interval
   (#3160). Tibber polls the car every 15 minutes (cited above). This supports keeping
   `soc_max_age_minutes` and the buffer.
8. **Pin a charge already running.** emhass's `def_current_power` prevents planning a running
   manual charge off (cited above). The integration can do the same by treating a manual charge as
   an override, not as a plan input (reasoning).

**Pitfalls**
1. **A hard minimum slot length near a deadline** made evcc miss a target by about 7 minutes
   (#33936, #34466, fix #34604).
2. **Dropping a missed target.** After an overrun, evcc switched to the next day's plan and
   stopped (#24339). emhass's template rolls a missed deadline to the next day (cited above). A
   stateless ChargeSmarter call after `target.at` will no longer see that target. The integration
   must decide what happens to the shortfall. This is not covered by D10, L4 or O12 today
   (reasoning).
3. **Price caps that silently miss targets.** EV Smart Charging warns the car may not reach its
   target. Predbat's planner "can therefore return a plan short of `car_kwh`" (cited above).
   ChargeSmarter's D9 (never sacrifice a target for price) avoids this, as long as O1 thresholds
   apply only to charging *above* the floors (reasoning).
4. **Forecasts as known prices.** evcc's `merged` tariff gives no signal that the later prices are
   forecasts (cited above). D20's markup, and `is_forecast` in the output, fill that gap (reasoning).
5. **An infeasible optimizer publishes nothing.** emhass returns "Infeasible" and publishes
   nothing (cited above). ChargeSmarter's best-effort plan with `PARTIAL` or `INFEASIBLE` per
   target is safer (reasoning).
6. **15-minute prices.** evcc, EV Smart Charging, Monta and openWB (quarter-hour tariff commits)
   all handle 15-minute slots (cited above). O11 ("sub-hour slots later") is behind the prior art
   (reasoning).
7. **Docs that lag the code.** evcc's optimizer page says "informational only", while the code
   already controls loadpoints (cited above). Read code, not only docs, when checking a claim.

### Inferences (reasoning)
- The strongest single lesson: every missed-target bug found was in code that adds hysteresis or
  efficiency rules on top of the plan. ChargeSmarter's integration layer should give the
  deadline-critical case priority over every such rule, as evcc's `planDeadlineCritical` now
  does.

### Gaps
- Quantitative savings or optimality gaps for any project were not found in the sources read.
