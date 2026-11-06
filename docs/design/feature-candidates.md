# Feature candidates

Every feature considered for the charging logic, and where it stands. Status:

- **Accepted**: part of the engine as decided (`motor.md`).
- **Integration**: belongs in the Home Assistant integration around the engine, not in it.
- **Covered**: needs no feature; an existing mechanism handles it.
- **Deferred**: a later iteration, when a concrete need shows.
- **Rejected**: decided against.
- **Open**: waiting on a decision in `decisions.md`.

## Prices

| Feature | Status | Notes |
|---|---|---|
| Cheapest hours over the whole horizon | Accepted | D22 |
| Uncertainty markup on forecast prices | Accepted, shape open | D20, O4 |
| A confidence value per price (`confidence_upper`) | Open | Part of O4 |
| Negative prices | Accepted | D25 |
| Time-of-use tariffs with fixed blocks | Deferred | The integration can flatten them into hourly prices |
| Demand charges (cost per peak kW) | Deferred | Commercial tariffs |
| Grid stress signals ("don't charge now") | Covered | An absence, or a price spike |
| Carbon intensity, weighed against cost | Deferred | A second input series and a weight; a scoring concern (D14) |
| Price slots shorter than an hour | Open | O11 |
| Pluggable cost models (fixed fees and the like) | Deferred | |

## Battery and SoC

| Feature | Status | Notes |
|---|---|---|
| Idle floor `min_idle_soc` | Accepted | |
| Emergency floor `min_safety_soc` | Accepted | |
| Taper by SoC, charger ramp and heat by session time | Accepted | D12, D16 |
| Hard ceiling of the car `car_max_soc` | Accepted | D18 |
| A global hard cap set by the user over every target | Rejected | R1 |
| Forcing a top-up when SoC is near the requirement | Rejected | R2 |
| Charging above the required floor in cheap hours | Open | O1 |
| Prefer 80 % over 100 % unless a target needs more | Covered | The caps (D7) |
| Slower charging in the cold | Integration | Folded into the curves (D6) |
| Prefer shallow cycles (30–70 %) | Deferred | Trades against feasibility |
| A preferred and a minimum SoC per target | Deferred | Adds a dimension to every search |
| Flag whether the plan stays above `min_safety_soc` throughout | Deferred | L2 |
| Daily energy cap | Deferred | |
| Rest between sessions | Deferred | |
| Rounding targets to steps of N % | Deferred | The first prototype rounded up to 5 %, hardcoded |

## Schedule

| Feature | Status | Notes |
|---|---|---|
| Several trips and targets in one plan | Accepted | D15, D22 |
| Absences (trips, workshop, quiet hours) | Accepted | D15 |
| A target with no trip ("ready by Saturday") | Accepted | D15 |
| A charge-free period every night (noise) | Covered | An absence with no energy |
| Completion buffer before departure | Accepted | D8; per target deferred (L3) |
| Holiday, a week away | Covered | One long absence |
| Recurrence ("every weekday 07:00") | Integration | The integration expands it into targets (D27) |
| Charging stops on a long trip | Integration | `energy_kwh` net of the stop; advice about it is L1 |
| Uncertain trips with a probability | Deferred | |
| "Ready by X or Y", whichever is cheaper | Deferred | Compares several plans |
| A departure that may slip if it saves money | Deferred | Changes what a target means |
| Priority between trips | Deferred | |
| A cost cap per trip | Deferred | |
| Back to the idle floor after the last target | Deferred | L4 |
| Preconditioning before departure | Integration | |

## Charger

| Feature | Status | Notes |
|---|---|---|
| Leave low prices to the charger's own automation | Accepted | D28 |
| Session energy limit | Accepted | D17 |
| Variable current, minimum current | Covered | The charger curve |
| Solar surplus | Integration | A cheap synthetic price, or the auto threshold, during surplus |
| Load balancing against the household's mains limit | Integration | Caps the charger's power |
| Several chargers for one car | Covered | The integration sends the curves of the charger in use |
| Several cars on one charger | Integration | The engine runs once per car |
| V2G | Deferred | |
| Charger ramp-up rate limits | Covered | The charger curve |

## For the user

| Feature | Status | Notes |
|---|---|---|
| Force a charge now | Integration | O12 |
| Pause the plan ("not tonight") | Integration | An absence; O12 |
| Notify when the car should charge but does not | Integration | |
| Costs in the user's currency | Integration | |
| Why the plan is as it is | Accepted | Structured warnings and results per target (D5, D21, D29) |
| Advice: "charge on the way", "avoidable at 100 %" | Deferred | L1 |
| Savings against charging at once | Deferred | Needs a second plan |
| Statistics for dashboards | Integration | |

## Algorithm

| Feature | Status | Notes |
|---|---|---|
| Window strategies: lowest peak, prefer night, prefer day, earliest | Deferred | A scoring concern (D14) |
| Rounding mode of charging time | Deferred | |
| Exact optimisation (linear programming) | Deferred | Unless the greedy approach proves too far off; see `research.md` |
| A trace of what was considered and why | Deferred | |
| A plan ID or hash of the input | Deferred | |
| Remembering a plan between calls, invalidation predicates | Rejected | D10 |
