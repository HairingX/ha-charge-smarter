# Scheduling algorithm for one EV's cheapest home charging under deadlines

Researched 2026-10-28. Scope: is the planned two-pass greedy (motor.md §6.2, D22) optimal, how far
from optimal can it be, when does it fail, and which better standard-library alternatives exist.

**How to read these notes.** Claims marked with a link come from a page, file or source file that
was opened during this task. Claims marked **(experiment)** come from code written and run during
this task (CPython 3.13.17, x86-64). They are command output, not literature. The harness is
described closely enough to reproduce it. Claims marked **(reasoning)** are my own derivations.

**The experiment harness, in brief (experiment).** One car, slots with prices, targets with a
SoC floor, an optional cap and the consumption of the absence that follows. Absence slots are
unavailable. Four variants of D22 pass 2 were compared with an exact dynamic programme:

- **"cum" (D22 as written).** A target is "short" when the simulated SoC at its deadline is below
  its pass-1 floor.
- **"inc".** A target is "short" while the energy assigned to it is below its own increment over
  the previous floor. This is the textbook matroid / earliest-deadline greedy.
- **"chrono" trim.** Charge in time order until the floors are met, so the chronologically last
  slot is the partial one. This is what a single `SET_CHARGE_LIMIT` per target produces.
- **"price" trim.** Shrink the most expensive selected slot first.

The exact reference is a DP over (slot, SoC on a grid), with fractions of a slot allowed. Real
prices are DK1 day-ahead spot prices for Jan–Sep 2025 from
[Energi Data Service, Elspotprices](https://api.energidataservice.dk/dataset/Elspotprices), 6,527
hourly records, of which 411 hours (6.3 %) were negative.

---

## 1. Constant power: is "cheapest hours first" optimal for one deadline, and for a chain of nested deadlines?

### Takeaway
With constant power, whole slots and non-negative prices, the cheapest-first greedy is provably
optimal for one deadline and for a chain of deadlines. This holds only if each target's need is
counted as its own increment, a slot is given to the earliest-deadline target it can serve, and
the partial slot is the most expensive one chosen. Matroid theory gives the proof, and both
experiments found zero gap. D22 as literally written (cumulative "short" plus charging in time
order up to a floor) is not optimal. Binding SoC caps also break the matroid structure.

### Cited findings
- The greedy algorithm (sort by weight, add an element if the set stays independent) returns an
  optimal subset of any weighted matroid. Unit-time tasks with deadlines form a matroid: a set is
  independent ("good") when it can be ordered so that every task meets its deadline. Minimising
  the total penalty reduces to the greedy max-weight problem on that matroid —
  [Gildea, Rochester CSC 282 slides "Matroids / task-scheduling problem"](https://www.cs.rochester.edu/~gildea/csc282/slides/C17-amortized.pdf)
- evcc's single-target planner is exactly the single-deadline greedy. It sorts the rates in the
  window [now, target] by price, ascending, breaking ties toward later slots. It takes slots until
  the required duration is covered, and it shortens the last one taken (the most expensive) so
  that it "start[s] as late as possible" —
  [evcc core/planner/planner.go `optimalPlan`](https://github.com/evcc-io/evcc/blob/master/core/planner/planner.go),
  [evcc core/planner/sort.go `sortByCost`](https://github.com/evcc-io/evcc/blob/master/core/planner/sort.go)
- evcc's MILP optimiser service reproduces the same result in its README example: "The EV takes
  its 30 kWh in the eight cheapest hours before the deadline … and stops exactly at the goal" —
  [evcc-io/optimizer README](https://github.com/evcc-io/optimizer/blob/main/README.md)
- **(experiment)** Exp 1 used 4,000 random small instances (4–9 slots, 1–3 targets, constant
  1 kW, integer needs and consumption, no binding caps). The incremental-EDF greedy was
  suboptimal in 0 of 4,000. "cum" plus price-ordered trimming was suboptimal in 0. "cum" plus
  chronological trimming was suboptimal in 109 (2.7 %), with a worst gap of +60 %.
- **(experiment)** In the same experiment with random per-target caps (4,000 instances), the
  incremental-EDF greedy returned an infeasible plan in 15 instances (0.4 %) where a feasible one
  existed. "cum" plus price trimming failed in 2, and both of those were the cap-semantics case
  in §7 (D23). Inspection showed the mechanism: with a cap, a cheap slot's energy assigned to a
  later target is later displaced by charging for an earlier target (the car is already at its
  cap in that slot), so the incremental bookkeeping goes stale.
- **(experiment)** Exp 3 used 60 real DK1 weeks with constant 11 kW, a 75 kWh battery cap,
  weekday commutes plus one long trip, and negative prices clipped to 0. "cum" plus price trim
  had a gap of 0 in 60 of 60 weeks. "inc" plus price trim returned an infeasible plan in 4 of 60
  (the stale bookkeeping above, triggered by the battery cap). "cum" plus chrono trim had a median
  gap of +7.6 %, a p90 of +52 % and a maximum of +63 %, or up to 1.78 EUR a week in spot cost.

### Inferences
- **(reasoning) Why the greedy is exact here.** Split each target's need into unit jobs with
  that target's deadline. A slot can serve any job whose deadline it precedes, so the slots that
  can serve a given job are nested by deadline. A set of slots is feasible exactly when it is
  independent in the resulting transversal matroid. Cheapest-first selection with an exact
  independence test therefore gives a minimum-cost basis, using the greedy-on-matroids theorem
  cited above. "Give the slot to the earliest-deadline target with need left" is an exact
  independence test when the sets are nested. Suppose an augmenting path could free a later job
  for a new slot. That path would need an earlier slot that was matched to a later job while an
  earlier-deadline job was free, which the earliest-deadline rule never allows. Fractional energy
  needs give the same result through the LP view: the constraints are prefix sums over nested
  sets, an interval matrix, whose LP optimum the same greedy reaches. The partial unit must then
  go to the most expensive slot chosen.
- **(reasoning) Counterexample CE-B: chronological fill is wrong even for one target.** Power
  is a constant 2 kW, start SoC is 4 kWh, and the target needs 6.4 kWh at the end of h2 (2.4 kWh
  to buy). Prices are h0 = 5, h1 = 5 and h2 = 4.
  - Optimum: h2 in full (2 kWh × 4 = 8) plus 0.4 kWh in h0 or h1 (× 5 = 2), so 10.0.
  - Greedy picks h2 then h1. Charging in time order with a charge limit of 6.4 runs h1 in full
    (2 × 5 = 10) and stops after 0.4 kWh in h2 (1.6), so 11.6, or +16 %. The harness confirmed
    both figures.
  - The fix is what evcc does: shorten the most expensive chosen slot, starting it late within
    its hour, rather than letting a charge limit cut the last one.
- **(reasoning) Counterexample CE-A: cumulative "short" over-selects.** "A target is short while
  its simulated SoC is below its floor" can take a cheap slot for a later target before the
  earlier target's mandatory energy (which carries over) is counted. The slot is then
  redundant. Price-ordered reverse-delete removes it; chronological trimming may instead remove
  a cheap late slot and keep an expensive early one. The harness found this smallest instance:
  - Prices [8, 9, 9, 1], start 3 kWh. Target A at slot 2 needs 5 and uses 2. Target B at slot 4
    needs 4 and uses 1. Power is 1 kW.
  - Optimum 18; cum plus chrono 26.
- **(reasoning) Two correct implementations.**
  - Per-target increments with earliest-deadline assignment, no caps binding, price-ordered
    partial slot.
  - Cumulative check followed by a price-ordered reverse-delete. This one was robust to the
    battery cap in Exp 1 and Exp 3.
- With per-target caps the problem is a min-cost flow with upper bounds on inventory, the SoC
  (see §3). Greedy then needs augmenting paths, or an exact method.

### Gaps
- No published proof was found stating "cheapest-first is optimal for nested EV deadlines". The
  argument above is my derivation from the matroid theorem; the experiments support it.
- The Buffalo lecture notes (Ngo) and the UT Dallas matroid notes appeared in search results;
  the first returned 404 and the second 503, so they were not used.

---

## 2. SoC taper, session-time power, partial hours and minimum session size: what breaks? Is a DP over (slot, SoC) exact enough and fast enough?

### Takeaway
Ranking hours by price is no longer exact once the energy an hour delivers depends on when it is
charged. With a realistic taper on real prices the loss is small: a median of 0.01 %, a p90 of
1.9 % and a maximum of 5.4 % over 60 weeks. Session-start ramps and minimum session sizes are
fixed costs that a price ranking cannot see. A DP over (slot, SoC grid, charging-in-previous-slot)
is exact for all of these, up to the grid. Done well it runs in O(slots × SoC states):
5.7 ms for 168 hourly slots at a 0.5 kWh grid, and 21–43 ms for 672 quarter-hour slots in pure
CPython.

### Cited findings
- **Taper in the literature and in other tools.**
  - Ignoring CC/CV tapering "in planning models can lead to undersized batteries and potential
    reliability issues"; the authors model it as SoC-dependent tapered power limits —
    [Butt & Li, arXiv 2507.18853 (2025)](https://arxiv.org/abs/2507.18853)
  - emhass models a SoC-dependent charge-power ceiling with one binary indicator per derating
    step and big-M constraints, so the taper turns its LP into a MILP —
    [emhass src/emhass/optimization.py, "SOC-dependent charge power ceiling (issue #807)"](https://github.com/davidusb-geek/emhass/blob/master/src/emhass/optimization.py)
  - evcc does not schedule under a taper. It only estimates the duration, with a linear taper
    from a computed taper SoC down to 1 kW at 100 %, and an assumed 85 % efficiency. The
    planner then treats the duration as constant-power slot time —
    [evcc core/soc/estimator.go `remainingChargeDuration`](https://github.com/evcc-io/evcc/blob/master/core/soc/estimator.go),
    [evcc core/loadpoint_plan.go `getPlanRequiredDuration`](https://github.com/evcc-io/evcc/blob/master/core/loadpoint_plan.go)
- **Restart and fragmentation in evcc.** The loadpoint layer ignores a short active slot when a
  later slot follows ("short slots cost an extra start/stop cycle"). It also continues instead of
  restarting when the next planned start is less than a slot away —
  [evcc core/loadpoint_plan.go `plannerActive`](https://github.com/evcc-io/evcc/blob/master/core/loadpoint_plan.go).
  The evcc optimiser has a separate "continuity" stage: "Fewest charge starts for batteries with
  `c_min > 0` … A device reported as charging (`c_active`) enters the horizon switched on, so
  keeping it on costs no start" —
  [evcc-io/optimizer README](https://github.com/evcc-io/optimizer/blob/main/README.md)
- **(experiment) Exp 2, synthetic small instances, deliberately severe curves** (600 instances
  each; power 2 kW below SoC 6, 1 kW from 6, 0.5 kW from 8.5 on a capacity of 10):

  | Case | Variant | Worse than optimum by >0.5 % | Mean gap when worse | Max gap |
  |---|---|---|---|---|
  | Constant power, fractional needs | cum + chrono | 45 % of instances | 20.6 % | 333 % |
  | Constant power, fractional needs | cum + price | 0 % | — | — |
  | Taper | cum + price | 9.8 % | 5.0 % | 25.6 % |
  | Taper | inc + price | 10.8 % | 4.2 % | 23.1 % |
  | Ramp (first 0.5 h of a session at 0.5 kW) | cum + price | 21.8 % | 4.9 % | 19.5 % |

  These curves are much harsher than real ones, so the magnitudes are upper-bound illustrations.
- **(experiment) Smallest counterexamples found by search, all checked against the exact DP.**
  - **Taper, one target (CE-C).** Prices [7, 3, 8, 7], start 3.4, need 8.4 by the end of slot 3.
    Optimum 29.2, greedy plus price trim 30.1 (+3 %).
  - **Ramp, one target (CE-D).** Prices [8, 3, 9, 8], start 1.1, need 3.5. Optimum 13.0, greedy
    13.75. The greedy took two separate one-hour sessions (h1 and h3), each paying the ramp,
    instead of the contiguous h0+h1. The harness handles a partial hour inside a ramp crudely, so
    the exact figure is indicative.
- **(experiment) Exp 3 on real DK1 weeks** (75 kWh, 11 kW to 60 kWh, 7 kW to 67.5 kWh, 3.5 kW
  above; battery cap 75 kWh; prices clipped at 0):
  - cum + price trim: median gap 0.01 %, p90 1.93 %, max 5.44 %. The largest absolute gap was
    0.16 EUR for the week, against a mean optimum of about 2.7 EUR in spot cost.
  - inc + price trim: max 21.8 %, and 4 infeasible weeks.
- **(experiment) Exp 5: an exact O(T·S) DP.** Within one slot the cost is linear in the energy
  bought, so each SoC state's best predecessor is a sliding-window minimum of
  `V[b] − price·g·b`, kept with a monotone deque. This needs `b + emax(b)` to be non-decreasing
  in b, which holds for a physical taper. It agreed with the brute-force O(T·S·E) DP to 1e-10 on
  40 real weeks.
- **(experiment) Exp 4/5, timings in CPython 3.13, best of 3–5 runs.**

  | Algorithm | 168 × 1 h, 20 targets | 672 × 15 min, 20 targets |
  |---|---|---|
  | Exact energy DP, grid 0.5 kWh (150 states) | 5.7 ms | 21 ms |
  | … with a session-start state (2×) | 10.6 ms | 35 ms |
  | Exact energy DP, grid 0.25 kWh | 16 ms | 43 ms |
  | Exact energy DP, grid 0.1 kWh | 33 ms | 107 ms |
  | Whole-slot on/off DP, 200 SoC buckets | 2.2 ms | 7.8 ms |
  | Whole-slot on/off DP, 400 SoC buckets | 4.7 ms | 17 ms |
  | Experimental greedy (O(T²) re-simulations, unoptimised) | 28 ms | 799 ms |

  The greedy figure is an upper bound for a careless implementation, not for D22 itself.

### Inferences
- **(reasoning) Why taper breaks the price ranking.** An hour's cost is price × energy
  delivered, and with a taper the energy depends on the SoC at that hour, which depends on every
  earlier charging decision. Shrinking the most expensive hour can move the high-power phase into
  a different hour. The exchange argument behind the matroid proof needs each element's weight
  to be fixed, and here it is not.
- **(reasoning) Session-start ramp and `min_session_kwh` (D19).** Both are fixed costs per
  session start. With a fixed cost per start the problem becomes a lot-sizing problem with setup
  costs, the class solved by DP (Wagner–Whitin). A per-slot price ranking cannot weigh a fixed
  cost, so D19's soft minimum should be a start penalty inside an exact method. In the DP that
  costs one extra boolean state, about 1.6–1.9× the run time (measured above).
- **(reasoning) Heat derating.** Power falling with minutes into a session favours several short
  sessions, the opposite pull to a ramp. Modelling it exactly needs session age in the state,
  for example 0/1/2+ hours (a few states). A pure greedy cannot represent it.
- **(reasoning) Recommended DP.** State (slot t, SoC on a 0.25–0.5 kWh grid, charging in the
  previous slot). Per slot, any energy from 0 up to `emax(SoC)` under the taper and the slot's
  charger power, never above the cap. Deadlines become state filters (V = ∞ below the floor),
  absences become a shift by the consumption, and the session start pays a penalty. For 168
  hourly slots this fits the 10 ms budget at 0.5 kWh. For 672 quarter-hour slots it does not fit
  at 10 ms in CPython (21–35 ms), so either the budget becomes about 50 ms or the grid becomes
  coarser. Backtracking the argmin is a second pass of the same size; that is an estimate, not
  measured.
- The DP also makes pass 1 (D23) unnecessary as a separate algorithm. V = ∞ at the start state
  means infeasible, and "reach as far as possible" is the same DP with a penalty per kWh of
  shortfall, the soft-constraint approach the evcc optimiser and emhass use (§6).

### Gaps
- How much real taper curves (per car model) and real ramp and derating behaviour change the gap
  was not measured. Exp 3 used one assumed taper and no ramp.
- The fast DP was timed only on CPython 3.13 on this container's CPU, not on a Raspberry Pi-class
  Home Assistant host. Expect several times slower there (unmeasured).
- The 2-minute soft start in motor.md's example (`[(0, 3.3), (2, 6.6), (5, 11.0)]`) costs about
  0.6 kWh of lost delivery per start at 11 kW **(reasoning)**. Its effect on plan cost was not
  measured.

---

## 3. Small exact formulations (LP / min-cost flow) a pure-Python solver could handle

### Takeaway
With constant power the problem is a min-cost flow, a transportation or lot-sizing network, and
an LP with an integral optimum. With a taper it is an LP only if the power limit is concave in
SoC; the step curves in the contract make it a MILP. No standard-library LP solver exists. The
pure-Python network simplex in networkx solves the flow in 5–15 ms for 168 slots but
106 ms for 672 slots with 20 targets. The specialised DP is simpler, exact for the step taper,
and as fast or faster.

### Cited findings
- networkx `network_simplex` "finds a minimum cost flow satisfying all demands in digraph G"
  with a primal network simplex. It "is not guaranteed to work if edge weights or demands are
  floating point numbers", so integer scaling is advised —
  [networkx docs, network_simplex](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.flow.network_simplex.html)
- **(experiment)** networkx 3.7 installed from PyPI with no dependencies and contains no compiled
  extension files (checked: 0 `.so` files). On the transportation model (slots → targets,
  0.1 kWh units) `network_simplex` took:
  - 168 slots: 5 ms with 6 targets (698 arcs), 15 ms with 20 targets (1,888 arcs).
  - 672 slots: 34 ms with 6 targets, 106 ms with 20 targets (7,580 arcs).

  networkx is not in the standard library, so D1 would require vendoring.
- PuLP is not a pure-Python solver. The current PuLP "includes a Rust extension
  (`pulp._rustcore`)", "CBC is not included inside the PuLP wheel", and without a solver it
  raises "PulpError: No solver available" —
  [PuLP installation docs](https://www.coin-or.org/pulp/main/installing_pulp_at_home.html)
- emhass depends on `cvxpy` and `highspy` (HiGHS), not PuLP —
  [emhass pyproject.toml](https://github.com/davidusb-geek/emhass/blob/master/pyproject.toml),
  [emhass optimization.py, `import cvxpy as cp`, default `lp_solver` "Highs"](https://github.com/davidusb-geek/emhass/blob/master/src/emhass/optimization.py)

### Inferences
- **(reasoning) Two flow formulations of the constant-power problem.**
  - *Path form*: nodes per slot. The grid → slot t arc has capacity `P·L` and cost `p_t`. The
    inventory arc t → t+1 carries the SoC with lower bound = floor at a deadline and upper bound =
    cap. Consumption is a demand at the deadline node.
  - *Transportation form*: slot → target arcs where the slot precedes the deadline. It cannot
    express caps.

  Both are totally unimodular, so integer data give integer optima. The path form has O(T) arcs,
  and successive shortest paths on it is essentially the DP.
- **(reasoning) Taper in an LP.** A concave piecewise-linear taper, `P(s) ≤ a_i − b_i·s` for
  each piece, keeps an LP, though evaluated at the slot's start SoC, an approximation. The step
  curves in `car_power_soc_steps` are not concave, so binaries are needed (emhass's approach).
  The DP handles any monotone curve with no such restriction.
- For a standard-library engine the DP dominates an LP: no solver to write, exact for step
  curves, deterministic, and easy to backtrack into windows. A pure-Python dense simplex for about
  700 variables is feasible to write but would be slower and has numerical-tolerance problems.
  That is a judgement; no pure-Python simplex was benchmarked.

### Gaps
- No pure-Python general LP solver (other than networkx's flow) was looked up or benchmarked.
- The source of networkx was not read to confirm that `network_simplex` is pure Python. The
  installed package simply had no compiled extensions.

---

## 4. Model predictive control / rolling horizon: re-planning on every call, plan churn and its remedies

### Takeaway
Recomputing from scratch on each new price or SoC reading is standard receding-horizon MPC, and
in the literature it performs close to the best online policy. Churn (start/stop chattering) is
handled in practice by two kinds of measure:
1. Stateless inputs and costs inside the optimiser: the device's current on-state, a cost per
   start, a terminal value of stored energy.
2. Stateful rules in the controller layer: do not stop a running slot, ignore short slots, lock
   the goal once a plan starts.

Both fit D10 if the engine takes the current state as input, which it already does with
`is_currently_charging`.

### Cited findings
- Tang & Zhang propose an MPC-based EV charging scheduler with O(T³) complexity. "Extensive
  simulations show that the proposed online algorithm performs very closely to the optimal
  online algorithm", with a gap "smaller than 0.4 % in most cases" —
  [Tang & Zhang, arXiv 1502.01456](https://arxiv.org/abs/1502.01456)
- emhass's `naive-mpc-optim` re-runs "the optimization on a rolling window every N minutes,
  using the latest measurements as the new initial state". The example uses a 24 h horizon every
  30 min ("solver time typically 0.1–0.5 s"). Each call passes the remaining
  `def_total_hours`, `soc_init` and `soc_final`. The page gives no warning about plan
  instability —
  [emhass docs, Rolling-horizon control with naive-mpc-optim](https://emhass.readthedocs.io/en/latest/study_cases/mpc.html)
- evcc's planner is recomputed on every control loop, and its loadpoint layer adds stateful
  anti-churn rules —
  [evcc core/loadpoint_plan.go](https://github.com/evcc-io/evcc/blob/master/core/loadpoint_plan.go):
  - "don't stop an already running slot if goal was not met"
  - "avoid re-start within [slot duration]"
  - "slot too short- ignoring remaining …" when a later slot follows
  - goal locking: "It caches the goal a soc-based plan has committed to, so that an overrunning
    plan…"
- The evcc optimiser makes continuity a cost-bounded secondary objective ("Fewest charge
  starts … a preference, not a guarantee: prices … still win"). It feeds the current on-state in
  as input, so continuing costs no start. Its objective includes "the value of the energy left in
  the batteries at the end", a terminal value —
  [evcc-io/optimizer README](https://github.com/evcc-io/optimizer/blob/main/README.md)
- The Caltech Adaptive Charging Network's scheduler is "based on convex optimization and model
  predictive control" and handles "quantized control signals" and "non-ideal battery charging
  behavior" as practical challenges —
  [Lee et al., arXiv 2012.02636](https://arxiv.org/abs/2012.02636)

### Inferences
- **(reasoning) Sources of churn in a stateless engine.**
  1. Ties and near-ties between hours flip with tiny input changes such as the SoC reading
     changing by 1 %. Fix: a deterministic tie-break (evcc prefers later slots) and a small
     epsilon preference for continuing.
  2. The partial hour moves.
  3. Forecast prices replaced by day-ahead prices change the ranking (D20 markup).
  4. A fresh SoC reading that disagrees with the simulation changes the remaining need.
- **(reasoning) What belongs in the engine (still a pure function, D10 kept).**
  - A start cost: D19's soft minimum session as a cost per session start.
  - "Currently charging" as the initial on-state, so the running session pays no start.
  - A deterministic tie-break.
  - Optionally a terminal value of stored energy (§5, O1).

  These are inputs and costs, not memory.
- **(reasoning) What belongs in the integration.**
  - Hysteresis on acting, for example do not stop a session that started less than N minutes ago
    unless the plan's saving exceeds X.
  - Debounce of calls.
  - Committing to the current slot, as evcc's loadpoint does.

  These need memory of what was actually done, which D10 rightly keeps out of the engine.

### Gaps
- A 2026 paper on a hierarchical stochastic MPC with switching-cost hyperparameters
  (arXiv 2607.25421) and Shi et al.'s on/off MPC for EV charging appeared only in search
  results. They were not opened and are not used as evidence.
- No study was found that quantifies chattering or plan churn for a single home EV under rolling
  re-optimisation.

---

## 5. Uncertainty: robust vs stochastic vs deterministic with a markup

### Takeaway
The rolling-horizon evidence found shows only a small gain from scenario-based stochastic MPC
over a deterministic point-forecast MPC (about 1 %). The gap to perfect information is larger
(13 %). For a standard-library engine that re-plans on every call, deterministic optimisation on
marked-up forecasts (D20) is a reasonable choice. The forecast's quality matters more than the
optimiser's treatment of uncertainty.

### Cited findings
- Fernández-Zapico, Hofman & Salazar ran a scenario-based stochastic MPC for an EV charging hub
  (PV, storage, day-ahead prices) in a 280-day closed loop. The stochastic MPCs were "13 % more
  expensive" than a perfect-forecast benchmark and "1 % better than their deterministic
  point-forecast counterpart" —
  [arXiv 2504.00685 (v2, Aug 2025)](https://arxiv.org/abs/2504.00685).
  A search-result summary quoted 11 %; the abstract that was opened says 13 %.
- Lemos-Vinasco et al. evaluated stochastic home energy management in a realistic rolling
  horizon with real Danish data and real-time prices. Their abstract reports that "a combination
  of optimization-based and naive control strategy presents the best overall results". The
  abstract gives no stochastic-versus-deterministic magnitude —
  [arXiv 2203.08639](https://arxiv.org/abs/2203.08639)
- Tang & Zhang's MPC (deterministic re-solve with expected arrivals) stays within about 0.4 % of
  the optimal online algorithm in most cases —
  [arXiv 1502.01456](https://arxiv.org/abs/1502.01456)

### Inferences
- **(reasoning) Robust vs deterministic.** For one car the binding uncertainty is mostly on the
  deadline side (consumption, cold, departure time), not price. Robustness there is already
  expressed by deterministic margins: the arrival SoC, the completion buffer (D8) and the cap
  semantics. On the price side, a markup that rises with lead time (D20) acts like a
  deterministic certainty-equivalent with a risk premium. It is cheap and transparent and
  compatible with the DP, which ranks by marked-up price and reports raw cost.
- **(reasoning) Why stochastic optimisation adds little here.** Re-planning on every new
  day-ahead publication corrects decisions before most of them are executed. Only the energy
  charged now is irrevocable, which is presumably why stochastic gains are small in rolling
  settings.

### Gaps
- No EV-specific study measuring the value of a lead-time markup versus scenario optimisation
  was found.
- Full texts of 2504.00685 and 2203.08639 were not read, only their abstracts.
- Price forecast error by lead time (S1) is outside this note.

---

## 6. How existing open-source optimisers do it (emhass, evcc)

### Takeaway
evcc's built-in planner is the single-deadline cheapest-slots greedy:
- constant power,
- the partial slot at the most expensive chosen slot,
- ties to later slots,
- an optional cheapest contiguous window,
- rolling re-computation with stateful anti-churn rules.

evcc's separate optimiser service and emhass both use MILP solvers: CBC via PuLP, and HiGHS via
cvxpy. Both use soft constraints with penalties, terminal values and binaries for discrete
behaviour. Neither has a standard-library-only engine.

### Cited findings
- **The evcc planner.** `Plan(requiredDuration, precondition, targetTime, continuous)` clamps
  the rates to [now, target]. If time is insufficient it charges continuously from now. If rates
  are missing it falls back to a "simple plan" (charge just before the target). It sorts by cost,
  takes slots and shortens the last. `continuous=true` instead picks the cheapest contiguous
  window (`findContinuousWindow`) —
  [planner.go](https://github.com/evcc-io/evcc/blob/master/core/planner/planner.go),
  [helper.go](https://github.com/evcc-io/evcc/blob/master/core/planner/helper.go)
- **One target, constant power.** The evcc planner takes one target time per plan. The required
  duration comes from energy and a constant `maxPower`, adjusted by a linear taper estimate —
  [evcc core/loadpoint_plan.go](https://github.com/evcc-io/evcc/blob/master/core/loadpoint_plan.go),
  [evcc core/soc/estimator.go](https://github.com/evcc-io/evcc/blob/master/core/soc/estimator.go)
- **The evcc optimiser.** evcc calls an external optimiser (`github.com/evcc-io/optimizer/client`,
  default `https://optimizer.evcc.io`). When that plan is present it overrides the planner
  ("While in control the optimizer schedules the plan itself") —
  [evcc core/site_optimizer.go](https://github.com/evcc-io/evcc/blob/master/core/site_optimizer.go),
  [evcc core/loadpoint_plan.go `EffectivePlan`](https://github.com/evcc-io/evcc/blob/master/core/loadpoint_plan.go).
  Its README says:
  - "The problem is expressed as a Mixed Integer Linear Program and solved with CBC via PuLP".
  - EV goals ("reach a given state of charge by a given time step") are soft constraints backed
    by penalties, so it "Never returns 'infeasible'".
  - It has a continuity stage that minimises charge starts.

  [evcc-io/optimizer README](https://github.com/evcc-io/optimizer/blob/main/README.md)
- **emhass.** It "uses a Linear Programming approach"
  ([README](https://github.com/davidusb-geek/emhass/blob/master/README.md)). Its implementation
  is cvxpy with HiGHS as the default solver, with binaries for semi-continuous deferrable loads
  and for SoC derating. A soft terminal-SoC target with a penalty factor of 100 avoids
  infeasibility ("a contradictory target relaxes to the closest reachable SoC instead of
  returning infeasible"). The source notes that HiGHS stops within a 1 % MIP gap by default, so
  "strict run-to-run determinism needs a tight (or zero) lp_solver_mip_rel_gap" —
  [emhass optimization.py](https://github.com/davidusb-geek/emhass/blob/master/src/emhass/optimization.py)

### Inferences
- **(reasoning) The task brief's premise.** It said "emhass uses LP via PuLP". Current emhass
  master uses cvxpy and HiGHS, with no PuLP dependency in `pyproject.toml`. It is evcc's
  optimiser that uses PuLP and CBC.
- **(reasoning) What to borrow.**
  1. evcc's "shorten the most expensive chosen slot, start it late" for the partial hour.
  2. Ties broken to later slots.
  3. Soft goals with a large shortfall penalty, which maps onto D9 best-effort: the DP with a
     shortfall penalty returns the best reachable plan and the shortfall.
  4. Current on-state as input so continuing is free.
  5. A terminal value of stored energy, relevant to O1.
- **(reasoning) Determinism.** emhass's MIP-gap note shows that a MILP solver gives no
  guarantee of run-to-run identical plans. An exact DP with a fixed tie-break is deterministic, a
  plus for D10's "same input, same output".

### Gaps
- evcc's `findContinuousWindow` and the optimiser's Python model were not read in full.
- The docs.evcc.io planner pages were not opened.
- openWB and OpenEMS were not examined (S2).

---

## 7. Verdict per decision (D10, D12, D22, D23, O1, O8, O9, S4)

### Takeaway
The architecture holds: a pure function re-run as MPC, simulation of the taper, an up-front
feasibility check. The core of D22 needs to change. Either make pass 2 an exact DP over
(slot, SoC grid, on-state), which is standard-library-only and about 6–11 ms for 168 hourly
slots, or keep the greedy with three fixes (below) and accept a measured gap of a few percent
with a taper. O1 should not stay at "never" while D25 promises to use negative prices.

### Cited findings
The evidence is in §1–§6. Summary per decision:

| ID | Verdict | Evidence | What should change |
|---|---|---|---|
| **D10** pure function, no state | **Supported** | Rolling re-solve is standard MPC and near-optimal online ([1502.01456](https://arxiv.org/abs/1502.01456); [emhass MPC](https://emhass.readthedocs.io/en/latest/study_cases/mpc.html)). evcc keeps commitment rules in the stateful loadpoint ([loadpoint_plan.go](https://github.com/evcc-io/evcc/blob/master/core/loadpoint_plan.go)) and passes the on-state into the optimiser ([optimizer README](https://github.com/evcc-io/optimizer/blob/main/README.md)) | Keep. Use `is_currently_charging` as the initial on-state so a running session pays no start cost, and add a deterministic tie-break (later slot first, as [evcc sort.go](https://github.com/evcc-io/evcc/blob/master/core/planner/sort.go)). Hysteresis on acting stays in the integration |
| **D12** simulate taper and session step by step | **Supported in intent; method should change** | Taper matters in planning ([2507.18853](https://arxiv.org/abs/2507.18853)); emhass models it with binaries ([optimization.py](https://github.com/davidusb-geek/emhass/blob/master/src/emhass/optimization.py)). A greedy that only simulates its choices cannot optimise over the taper (Exp 2/3) | Fold the curves into the DP transition (`emax(SoC)` per slot, precomputed with the 6-minute sub-step simulation). The simulation remains for reporting expected kWh and cost per window. Session-time effects become an on-state and start cost (the ramp) or a small session-age state (derating) |
| **D22** two-pass greedy | **Partly supported; contradicted as written** | Exact for constant power, non-negative prices, no binding caps, *if* increments are counted correctly and the partial slot is the most expensive one (matroid theorem, [Rochester slides](https://www.cs.rochester.edu/~gildea/csc282/slides/C17-amortized.pdf); Exp 1/3: 0 gap). As written (cumulative "short" plus charging in time order to a floor): median +7.6 %, max +63 % on real weeks (Exp 3). With a taper, best greedy variant: median 0.01 %, p90 1.9 %, max 5.4 %. With binding caps the incremental variant went infeasible in 4 of 60 real weeks. Ramps and minimum session are not representable | **Preferred:** replace pass 2 by the exact DP (§2): about 6 ms for 168 × 1 h at a 0.5 kWh grid, 11 ms with the on-state. **Minimum fix if the greedy stays:** (1) the partial slot is the most expensive chosen one, shortened by starting late (evcc's rule), never cut by a charge limit in time order; (2) after selection, reverse-delete in descending price; (3) re-simulate after each addition, never trust per-target counters when caps bind. Keep the DP as the test oracle either way |
| **D23** feasibility of the whole chain in pass 1 | **Supported; can be absorbed** | A cheap up-front check is sound. In the DP, infeasibility is V = ∞ and best effort is a shortfall penalty (the soft-goal approach of [evcc-io/optimizer](https://github.com/evcc-io/optimizer/blob/main/README.md) and [emhass](https://github.com/davidusb-geek/emhass/blob/master/src/emhass/optimization.py)) | (reasoning) Clarify cap semantics: does a target's `max_charge_soc` cap the SoC *at* the target, or only charging before it? A harness instance (Exp 1) showed that clamping a pushed floor at an intermediate target's cap makes a later target PARTIAL, though the car could carry more SoC through that target if the cap only limited charging in that segment |
| **O1** charge beyond the floors when cheap | **Lean (a) "never" contradicted when prices go negative** | DK1 Jan–Sep 2025: 411 of 6,527 hours negative ([Energi Data Service](https://api.energidataservice.dk/dataset/Elspotprices)). With negative spot prices the exact optimum charges beyond the floors. A floors-only plan lost up to 0.86 EUR a week of spot value (best greedy variant, realistic taper, 75 kWh cap, unclipped prices: median 0.47 %, p90 8.9 %, max 48 % of the week's optimum, against p90 1.9 % with prices clipped at 0, so the negative hours cause most of the gap, Exp 3). evcc's optimiser values the energy left at the end ([README](https://github.com/evcc-io/optimizer/blob/main/README.md)) | At minimum: always fill up to `default_target_soc` (or the cap) in hours whose *consumer* price is ≤ 0, so D25 holds. Better: a terminal value per kWh above the floors, which the DP handles natively; option (c) or (b) becomes a value function rather than a rule. **(reasoning)** With Danish consumer tariffs and taxes added, consumer prices are rarely negative, so the realised gap is smaller than these spot-only figures; unmeasured |
| **O8** default `simulation_step_minutes` | **Mostly moot under a DP** | Exp 4/5 timings above | Use the sub-step only to precompute `emax(SoC)` per slot length and for reporting. The cost is O(SoC states × sub-steps), done once per call, so 3 minutes is affordable. The precision knob that matters is the SoC grid: 0.5 kWh fits 10 ms at 168 slots; 672 slots need about 20–35 ms or a coarser grid |
| **O9** `is_top_up`, when to emit `SET_CHARGE_LIMIT` | **Reasoning only** | CE-B (§1): a charge limit that cuts the chronologically last window makes the cheap hour partial (+16 % in the example). evcc shortens the most expensive chosen slot instead ([planner.go](https://github.com/evcc-io/evcc/blob/master/core/planner/planner.go)) | Drop `is_top_up`; every window is just a window. Implement partial slots by window start and end times (start late in the hour). Emit `SET_CHARGE_LIMIT` only as a safety ceiling: the planned SoC at the end of the plan, or the cap, never as the means of cutting a partial hour |
| **S4** greedy vs optimum on real prices | **Answered for DK1 2025 with an assumed driver profile** | Exp 3: 60 random weeks, 168 h, exact DP reference | Constant power, prices ≥ 0: fixed greedy exact, literal D22 median +7.6 % (max +63 %). Realistic taper: fixed greedy median 0.01 %, p90 1.9 %, max 5.4 %. Negative prices: floors-only loses up to about 0.9 EUR a week (0.75–0.95 EUR in the constant-power runs, 0.86 EUR with the taper). Absolute amounts are small: mean optimum about 2.7 EUR a week in spot cost |

### Inferences
- **(reasoning) DP sketch for `planner`, stdlib only, O(T·S).**
  1. Precompute per SoC state b and slot length L: `top[b]`, the highest SoC reachable in one
     slot under the car curve, at the slot's charger power, by sub-step simulation.
  2. Backward or forward pass over slots, with V indexed by (b, on).
     - At a deadline: `V[b] = ∞` for b below the floor (with a shortfall penalty instead, when
       best effort), then shift by the consumption.
     - In an available slot: `V_on[nb] = min over b ≤ nb ≤ top[b] of V[b] + p_t·g·(nb−b)`
       (+ start penalty if the previous state is off), by monotone deque, and
       `V_off[b] = min(V_on[b], V_off[b])`.
     - In an unavailable slot: off only.
  3. Backtrack the argmin to energy per slot. Shorten each slot's window to that energy, starting
     late.
  4. Windows are maximal runs of on-slots. Report raw-price cost.
  5. Rank by the marked-up price (D20) inside the DP, report with raw prices.
- **(reasoning)** Even if the maintainer keeps the greedy for its simplicity, the DP is the right
  test oracle for property-based tests, since it is exact by construction. The repository's
  "every problem found gets a test" rule fits CE-A, CE-B, CE-C and CE-D as regression cases.

### Gaps
- S4 used one market (DK1), Jan–Sep 2025 hourly spot only (no tariffs, no 15-minute prices), one
  assumed taper, and synthetic commute and trip schedules. Other markets, 15-minute day-ahead
  prices (Energi Data Service's `DayAheadPrices` dataset has them for 2026; checked but not used)
  and real calendars were not tested.
- Back-tracking time and the memory of the DP were not measured; only the value pass was timed.
- Timings are for this container's CPU, not for typical Home Assistant hardware.
