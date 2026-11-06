# Decisions

Every decision on the planning engine, with its reason. A decision is reopened only on the
maintainer's request. Open questions are at the end; answer them by ID.

## Taken

### Scope and principles

| ID | Decision | Reason |
|---|---|---|
| D1 | The engine imports only the standard library: no Home Assistant, no I/O, no calendars | It must become a library usable outside Home Assistant |
| D2 | Car- and charger-agnostic: every car and charger value arrives with each call | One engine for every car and charger |
| D3 | The engine works in kW, kWh, hours and SoC. Distance is converted by the caller; prices are opaque numbers | Miles and kilometres differ by market, and the caller knows consumption, temperature and the car's own estimate. A helper for the conversion may come later, outside the engine |
| D4 | No hardcoded domain values. Defaults only for algorithm tunables, all overridable per call | Battery, charger power and thresholds differ for every user |
| D5 | The engine never returns text: codes, typed values, structured parameters, references | Text is localised; codes are universal. The caller translates |
| D6 | Battery temperature, weather and altitude are folded into the curves by the caller | Keeps the engine blind to the environment and portable |
| D7 | Caps are hard. A target's own `max_charge_soc` wins over `default_target_soc`, up or down. Where a target needs more than its cap, the engine plans to the cap and reports `PARTIAL` | Setting a cap is an active choice, and the user may have a reason, such as charging on the way. Unset, the default applies |
| D8 | The completion buffer is absolute: no charging in the buffer before a target. Global, default 20 minutes | Charging can run late (cold, a tired battery), and the user may want to unplug and pack before leaving. Think of it as moving the departure earlier. Per target only if it proves needed |
| D9 | Best-effort: the engine charges in expensive hours when a target requires it, but never breaks a cap or the buffer; it reports the shortfall | Every home charger with trip planning does this; this one does it more intelligently |
| D10 | A pure function: no state, no remembered plan, no change detection. `ActivePlan`, plan stickiness, trip-set change detection and their tunables and codes are removed | A call is expected to decide afresh from the data given. Caching, debounce, hysteresis against replanning churn and persistence belong to the integration |
| D11 | Three layers: caller, API, core. The API layer validates, corrects what is safe to correct, and refuses the rest; the core trusts its input. Replaces "be forgiving on data quality" and the skip-with-warning rules | The engine is internal and fully under our control; a core that trusts its input is simpler to develop |
| D12 | The engine simulates the charge step by step with both curves; an approximation, kept light | The taper and heat depend on SoC and time inside the window, which the caller cannot know in advance. Precision is traded for speed |
| D13 | A planning function, not a policy engine: solar, load balancing, several cars, tariffs and V2G are outside it | Keeps the engine small and general |
| D14 | One module per concern (contract, validation, charging model, windows, scoring, trip chain, planner); no strategy objects until a second implementation exists | More logic will come, for charging behaviour, window search and weighting; it must not end as one lump where no one can see the combinations |

### Data model

| ID | Decision | Reason |
|---|---|---|
| D15 | `AbsenceWindow(start, end, energy_kwh)` and `ChargeTarget(at, target_soc, max_charge_soc)`, linked by the caller for a trip. Replaces `Trip` and `ScheduledTarget`; `CalendarEvent`, `EventType` and the no-charge event type are gone | An absence need not have a target (the workshop) and a target need not have an absence ("ready by Saturday"). The engine does not know about calendars |
| D16 | Two curves: `car_power_soc_steps` (the car, by SoC) and `charger_power_session_steps` (the charger, by minutes into the session). Power = the lower of the two × efficiency | The two come from different sources and change at different times. The charger curve covers a gentle start as well as derating from heat |
| D17 | `charger_max_session_kwh`, optional | Some chargers limit one session; the engine owns the window search, so it must know |
| D18 | `car_max_soc`, a hard ceiling for the car | Some cars refuse to charge above a level. Distinct from the user's soft target |
| D19 | `min_session_kwh` (soft, e.g. 2 kWh) replaces `min_session_minutes` (hard) | A few minutes of charging rarely makes sense, but the rule must give way when a target needs it, or when charging later costs more. Energy, not time, and one minimum, not two |
| D20 | Forecast prices carry a markup when hours are chosen; costs use raw prices. The linear markup (5 % plus 0.2 % per hour) is rejected as too simple; a stepped curve by hours ahead is proposed | A known price is certain; a forecast a week out may turn from cheap to expensive. The further out, the more a forecast must save before the engine waits for it |
| D21 | Every warning code has a fixed schema for its `params` | Callers must be able to read and translate warnings reliably |
| D24 | `energy_kwh` is required; 0 is allowed | 0 is a real value: a deadline with no consumption |
| D25 | Negative prices are supported and used | Grid-support hours |
| D26 | Not modelled: CC/CV transition (the SoC curve covers it), parasitic drain (fresh SoC each call), restart cost (seconds), charger offline (the caller sets the curve to 0 or does not call) | Each is covered elsewhere or too small to matter |

### Planning

| ID | Decision | Reason |
|---|---|---|
| D22 | Cheapest first over the whole horizon, in two passes: required SoC per target working backwards, then the cheapest hours assigned to the earliest unmet target. Replaces planning gap by gap and the special main-plus-top-up branch | Charging enough for the next trip is not enough: a later trip may leave no time to charge between trips, and a cheap night after a trip may make charging before it a waste |
| D23 | The feasibility of the whole chain of targets is checked in pass 1, before searching | Cheap, and saves searching an impossible chain |
| D27 | Weekday patterns and recurrence are the caller's: it generates targets | The engine has no calendar logic |
| D28 | The charger's own low-price automation can be left to charge below `charger_auto_threshold`; `None` turns it off | Some chargers have it; not all |
| D29 | Output carries `feasibility` and a result per target: status and SoC figures only | A quick signal for the integration (a red badge) without advice the data cannot yet support |

### Rejected

| ID | Proposal | Reason |
|---|---|---|
| R1 | A global hard cap set by the user over every target | It would stop a long trip from charging to 100 %. A target that must not exceed a level sets its own cap |
| R2 | A threshold forcing a top-up when SoC is near the requirement | The arrival SoC already gives the margin |
| R3 | Text in the output, including a "Suggestion" field by that name | D5; the name also covers too many different things |
| R4 | Modelling temperature in the engine | D6 |

### Deferred

| ID | Item | Why not now |
|---|---|---|
| L1 | Advice in the output: "this trip needs a charge on the way", "avoidable at 100 %", how close the arrival comes to the buffer | Wanted, but only once the data model has proven itself. Must be codes and parameters, not text |
| L2 | `plan_guarantees_min_safety`: whether the plan keeps SoC above `min_safety_soc` throughout | Which combinations to handle needs more thought |
| L3 | A completion buffer per target | Global is enough until proven otherwise |
| L4 | Charging back to `min_idle_soc` after the last target | The next call catches it |

## Open

| ID | Question | Options, and the current lean |
|---|---|---|
| O1 | Charge beyond the required floors when hours are cheap? | a) never: `default_target_soc` applies only with no targets, and a user wanting margin raises `min_idle_soc` (lean); b) up to `default_target_soc` in hours below a price threshold the user sets; c) in hours below a percentile of the horizon's prices; d) always up to `default_target_soc` (loses the global optimisation) |
| O2 | Where is the arrival SoC stated now that a trip is an absence and a target? | On `AbsenceWindow` as `min_soc_at_end`, defaulting to `default_arrival_soc`; or global only |
| O3 | Naming pass over every type, field and enum value before the contract is built | Names that still say "trip" (`TripResult`, `next_trip`, the `TRIP_*` codes), `default_trip_buffer_soc`, the length of the curve names |
| O4 | Shape and defaults of the forecast markup | A stepped curve `[(hours_ahead, percent), ...]`, optionally a per-price `confidence_upper`; defaults only once calibrated against real price data (`research.md`) |
| O5 | What do existing open-source planners do, and what can be borrowed? | Research with web access, never from memory (`research.md`) |
| O6 | Per field: what the API layer corrects, and what it refuses | Rule so far: structurally recoverable is corrected and reported (order, duplicates); semantically broken is refused (naive datetime) |
| O7 | A stale SoC reading that is below `min_safety_soc`: wake first, or charge first? | Wake first today |
| O8 | Default of `simulation_step_minutes` | 6, or 3 for precision; to be measured against the 10 ms budget |
| O9 | With main and top-up no longer separate, is `is_top_up` on `ChargeWindow` still needed, and when is `SET_CHARGE_LIMIT` emitted? | |
| O10 | Further validation | Refuse `min_safety_soc > min_idle_soc`; warn on `min_idle_soc > default_target_soc` (forces charging above the default before every target); skip with a warning a target whose buffer starts in the past; bounds on the forecast markup |
| O11 | Price slots shorter than an hour | The contract assumes hourly slots |
| O12 | Manual controls: force a charge now, pause the plan | In the integration, not the engine; not designed |
