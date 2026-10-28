# Research

What has been investigated for the design, how far each finding can be trusted, and what is
still to be researched.

**Rule for all research:** a finding needs a source that was actually read: a fetched page, a
file, a command's output. Whoever cannot reach a source, or cannot find the answer, says so and
stops; nothing is filled in from memory. Reasoning, such as an argument about an algorithm, is
marked as reasoning.

## Findings

### Reviews of the requirements (reasoning)

Four reviews of the requirements as they stood on 2026-04-23. Their reports were not kept; their
conclusions were, and each led to a decision.

| Review | Finding | Outcome |
|---|---|---|
| Contradictions | The buffer was both "always respected" and "may be spent when time is short" | D8: always respected |
| Contradictions | The formula for a trip's target ignored its cap in one place and not in another | D7 |
| Contradictions | Detecting changed trips needs the earlier trip list, which the plan did not keep | D10: no state, no detection |
| Charging physics | The caller cannot fold the taper and heat into a fixed power, as they depend on SoC and time inside the window | D12: the engine simulates |
| Charging physics | Candidates: CC/CV transition, parasitic drain, minimum charging power, the car's own SoC ceiling, restart cost, charger offline | D18 and D19 taken in, the rest dropped (D26) |
| Parameter interactions | Combinations of settings that defeat each other | Validation, O10 |
| Usability for callers | The prototype was a version behind the requirements in nearly every type | The prototype is kept only as reference (`sources/`) |
| Not recorded | The warnings' `params` had no schema | D21 |

### Algorithm class (reasoning)

The problem is choosing hours under time-varying prices, with hard deadlines, for one car.
Exact optimisation (linear or integer programming) needs a solver, which does not fit a
standard-library engine running inside Home Assistant. A greedy choice of the cheapest hours,
checked by simulating the charge, is simple, fast and dependency-free; with up to 168 prices and
20 targets it runs well inside the 10 ms budget. How far greedy results fall from the optimum
for this problem has not been measured.

An up-front check that the whole chain of targets can be met is cheap and saves a pointless
search (D23).

The review that gave this also cited papers, repositories and an optimality gap. They were
written from memory, not looked up, and are not repeated here.

### Forecast uncertainty (reasoning, and one unconfirmed search)

Reasoning: errors in electricity price forecasts are unlikely to grow linearly with the hours
ahead. Prices revert towards a mean, so the error should level off, and a day-ahead price is
known exactly. A stepped curve lets the user express this (no markup for known prices, rising for
forecasts, levelling off) without the engine betting on one formula. It reuses the step-table
mechanism of the power curves. This led to D20 and O4.

A web search on 2026-04-23 reported hourly forecast errors (MAPE) of roughly 8–11 % for Nord Pool
prices. The sources were not recorded, so the figure is unconfirmed until they are found again.

### Prior art

Fetched on 2026-04-23: EVCC (github.com/evcc-io/evcc), MIT licence, describes itself as an
"extensible EV Charge Controller and home energy management system". Nothing more was examined.

## To research

| ID | Question | Feeds |
|---|---|---|
| S1 | How large are price forecast errors by hours ahead, for Nord Pool and the forecasts Home Assistant users have (Energi Data Service, Tibber and others)? Gives the default markup steps | O4 |
| S2 | How do EVCC, emhass, openWB and OpenEMS plan: price optimisation, deadlines, buffers, forecasts, charging curves, manual overrides? Source code where it is open | O1, O4, O5, O12 |
| S3 | How do the Home Assistant integrations for chargers and cars expose SoC, plugged-in state, charge limits and power, and how stale their SoC readings get | The adapters |
| S4 | How far does greedy selection fall from the optimum on real price series and schedules? | D22 |
