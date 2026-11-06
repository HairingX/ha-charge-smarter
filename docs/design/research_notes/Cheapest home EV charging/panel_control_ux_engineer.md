# Panel position paper: controlling the charge in practice, and what the user sees and sets

Panellist: Home Assistant control engineer, with a user-experience brief. Written 2026-10-28.

Scope: conflicts C5 (control reality), C7 (defaults and settings), O12 and the user side of C8
(manual controls, missed targets, missing prices, plan display), and O2 and O1 seen from the
user. All seven research notes in this folder were read in full: `price_composition_denmark.md`,
`price_forecast_uncertainty.md`, `charging_physics_battery.md`, `scheduling_algorithm.md`,
`prior_art_software.md`, `home_assistant_data.md`, `driver_behaviour_ux.md`. Design references:
`motor.md` §4–§6, `decisions.md` (D1–D29, O1–O12), `feature-candidates.md`.

How to read this paper:
- A finding cited to a **note and section** relies on the URL that note gives there.
- A finding cited to a **URL** was opened by me on 2026-10-28, mostly to check a fact the notes
  disagree on or leave open. Raw source files were fetched from `raw.githubusercontent.com`;
  documentation pages with a plain HTTP client. Where a page could not be opened, that is said.
- **Reasoning** marks my own engineering argument. Each conflict is steelmanned before I take a
  position.
- The maintainer's charger brand is unknown. Every recommendation is checked against Easee,
  Zaptec, Wallbox, OCPP, go-e and Monta, and the brand that cannot support a feature is named.

---

## 1. C5a: what can actually be actuated, and what the engine's actions should be

### Takeaway
No charger integration offers a clean, symmetric START/STOP. Each has a different "hold" primitive,
several reset it at plug-in or reboot, and Zaptec's Resume can only undo its own Stop. On the car
side, an Enyaq on core Home Assistant has no wake, refresh or charge-limit target at all. The
engine should therefore stop emitting edge-triggered car and charger commands. It should output
**when charging is permitted** (windows, and `should_charge_now`), and the integration should
**assert a level state, ALLOW or HOLD, idempotently on every cycle**, re-asserting it after
plug-in, reboot or session reset and verifying it by reading power back. `WAKE_UP_CAR`,
`REQUEST_SOC_REFRESH` and `SET_CHARGE_LIMIT` should leave the engine's action list.

### Cited Findings
**Chargers: the hold and release primitives, checked at source**
- **Zaptec.** "If the charger is configured to not require authentication, connecting the charger
  to the EV will by default start charging." Stop is the "Stop charging" button or the "Charging"
  switch; start is "Resume charging". Resume "will only start charging if the charger was stopped
  by a 'Stop charging' command". It does not start when the current was set to 0 A, when the car
  reached its own target, when the car's app stopped it, or outside the car's own schedule. "As a
  general rule: To start charging, you need to reverse what stopped it in the first place." To
  prevent auto-start: "Delay authorization of the charger" or set "Available current"
  (installation, affects all chargers) or "Charger max current" to 0 A. That "has no effect if the
  charger is in _stand-alone_ mode". "Zaptec will unlock the cable when charging is paused unless
  it is permanently locked." The 15-minute rule is scoped to current: "Many EVs don't like getting
  too frequent changes to the available charge current. Zaptec recommends not changing the values
  more often than every 15 minutes." Custom poll intervals "will have unexpected effects". The
  Energy Meter entity lags 1 hour; "Session total charge" is "more frequently updated" — [Zaptec
  README](https://raw.githubusercontent.com/custom-components/zaptec/master/README.md).
- **Easee.** "Pause and resume are the commands you should use, not start and stop. Start and stop
  controls authentication… If your charger is not set up with authentication enabled, start and
  stop will do nothing." The circuit dynamic limit below 6 A pauses, 6 A or more charges. The
  charger dynamic limit "is automatically reset when a new charging session is started". Only
  "dynamic" limits are for regular use; the others are written to flash. Setting a limit to the
  value already in the cloud makes no API call — [easee_hass wiki: ChargingControl](https://raw.githubusercontent.com/wiki/nordicopen/easee_hass/ChargingControl.md).
  Easee's own developer docs add: "When a charger is restarted, all dynamic values will be reset";
  `dynamicChargerCurrent` "is reset after plugging in a car or rebooting the charger. Some cars might
  get upset if the current is changed too frequently"; an "Offline Max Circuit Current" applies
  when the charger "looses connection with the Easee cloud" — [Easee developer: current limits and
  control](https://developer.easee.com/docs/current-limits-and-control). "Enabling the smart
  charging LED, will disable any basic or weekly plans" — [Easee developer: smart
  charging](https://developer.easee.com/docs/api-smart-charging). Data is pushed over SignalR, and
  "polling the API too often usually leads to being locked out for a time period" — [wiki:
  UpdateFrequency](https://raw.githubusercontent.com/wiki/nordicopen/easee_hass/UpdateFrequency.md).
  The `action_command` options are start, stop, pause, resume, toggle, override_schedule and
  plan enable/disable/delete — [easee services.yaml](https://raw.githubusercontent.com/nordicopen/easee_hass/master/custom_components/easee/services.yaml).
- **Wallbox (core).** A pause/resume switch, a max charging current number, and a "Resume
  schedule" button that "resumes the charger's programmed schedule and EcoSmart mode after a manual
  stop". "Data is refreshed once every 90 seconds for owners of 1 charger… Altering this refresh rate
  is not recommended" — [HA docs: Wallbox](https://www.home-assistant.io/integrations/wallbox/).
  Whether a Wallbox starts at plug-in by default is not stated there.
- **OCPP (HACS).** The Charge Control switch "Turning off ends the ongoing charging session (remote
  stop)… Turning the switch on again resets the session metrics; the charger returns to its previous
  state (this does not force a new session to start)." Maximum Current is station-wide; Session
  Current Limit is per connector and "limits only the running transaction". The Availability control
  "must be set to ON before EV is plugged in" — [OCPP user guide](https://home-assistant-ocpp.readthedocs.io/en/latest/user-guide.html).
  The linked "charge automation guide" (`charge-automation.html`) returned HTTP 404, so whether
  every charger accepts a 0 A limit was not confirmed.
- **go-e (HACS, APIv2/WebSocket).** A writable `frc` key, "forceState (Neutral=0, Off=1, On=2)";
  a writable `amp` (requested current); `acp` "allowChargePause (car compatiblity)"; a
  "minChargePauseDuration"; and a status reason enum that includes
  `NotChargingBecauseForceStateOff`, `ChargingBecauseChargePauseNotAllowed` and
  `NotChargingBecauseMinPauseDuration`; `wh` is a status key — [go-e integration keys.py](https://raw.githubusercontent.com/marq24/ha-goecharger-api2/main/custom_components/goecharger_api2/pygoecharger_ha/keys.py).
  With WebSocket the data arrives "as soon as something changes"; in polling mode with no car
  connected a full read happens only "every 5 minutes" — [go-e README](https://raw.githubusercontent.com/marq24/ha-goecharger-api2/main/README.md).
- **Monta (HACS).** Only `start_charging` / `stop_charging` services and one "Start/Stop" switch
  that calls them; no current-limit entity is listed. "Charge Energy is the energy delivered by
  the current charge, and resets when a new charge starts." The public API "is in BETA" — [Monta
  README](https://raw.githubusercontent.com/nickknissen/hass-monta/main/README.md),
  [services.yaml](https://raw.githubusercontent.com/nickknissen/hass-monta/main/custom_components/monta/services.yaml),
  [switch.py](https://raw.githubusercontent.com/nickknissen/hass-monta/main/custom_components/monta/switch.py).
  Poll every 120 s; Monta's own SmartCharge schedules the cheapest windows before departure —
  `home_assistant_data.md`, "Charger integrations".

**Car: what an Enyaq on core Home Assistant exposes, checked at source**
- `skoda` on `dev` has a sensor platform only, `UPDATE_INTERVAL = timedelta(minutes=5)`
  ([coordinator.py](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/skoda/coordinator.py)).
  Its sensors are mileage, fuel level, battery percentage, ranges, charging power, charging
  state, time to full, charge type, climate and auxiliary-heating values and licence plate. There
  is no charge-limit or target-SoC sensor, no plug sensor, and `car_captured_timestamp` is read only
  for auxiliary heating — [sensor.py](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/skoda/sensor.py).
- "The integration is read-only. It reports vehicle status but cannot start or stop charging,
  control climate, or lock or unlock the vehicle." It polls "every 5 minutes"; on the per-VIN rate
  limit it "waits before attempting to retrieve data again". If the API key "expires or is revoked,
  the integration can no longer retrieve data". "Introduced in Home Assistant 2026.11" — [HA next
  docs: Škoda](https://next.home-assistant.io/integrations/skoda/).
- The Škoda API has no wake or refresh endpoint, limits requests to 20 per hour per VIN, and
  accepts a charge limit of 50–100 % in steps of 10 — `home_assistant_data.md`, "Car integrations".
- `homeassistant.update_entity` refreshes only the cloud copy and costs quota; the built-in
  poll already uses 12 of the 20 per hour — `home_assistant_data.md`, "Car integrations", Inferences.

**Prior art on action semantics**
- evcc's loadpoint re-decides each cycle and keeps stateful rules (finish a running slot, avoid
  a restart within one slot, skip short slots); every missed-target bug found was in that layer —
  `prior_art_software.md`, "evcc", and "Ideas worth borrowing, and pitfalls to avoid".
- Predbat exposes only `binary_sensor.predbat_car_charging_slot` and leaves start/stop to a user
  automation; EV Smart Charging exposes a status enum and a schedule attribute —
  `prior_art_software.md`, "Home Assistant custom integrations"; `home_assistant_data.md`,
  "Manual controls".
- The engine plans at full curve power or not at all; below 6 A there is no charging, and slow
  charging is less efficient — `charging_physics_battery.md` §2–§3.

### Inferences
**Steelman for keeping edge actions (`START_CHARGING` at t1, `STOP_CHARGING` at t2).** They are
explicit, testable as data, and let a simple caller schedule `async_track_point_in_time` calls
without re-deriving anything. `motor.md` §5 already defines them, and D21-style typed params make
them translatable.

**Why I reject them as the primary contract (reasoning).**
1. An edge is fired once; every charger above can lose it. Easee resets the charger dynamic
   limit at plug-in and every dynamic value at reboot; Zaptec's Resume silently fails if
   anything other than its own Stop stopped the charge; OCPP's Charge Control "on" does not start a
   session. A level that is re-asserted every cycle survives all of these. A missed edge does not.
2. The most important action is not in the list at all: the charger auto-starts at plug-in
   (Zaptec stated; Easee implied by "start and stop will do nothing" without authentication), so
   the integration must actively **hold** whenever the car is plugged in and `should_charge_now`
   is false. The home_assistant_data note reached the same conclusion
   (`home_assistant_data.md`, mapping table, `START_CHARGING`/`STOP_CHARGING` row).
3. The engine is stateless (D10). Under rolling re-planning each call's edges supersede the
   last call's, so the caller has to diff edge lists anyway. The windows already carry the same
   information.

**Position.** Keep `windows` and `should_charge_now` as the control contract. Either drop
`START_CHARGING`/`STOP_CHARGING` from `actions`, or document them as *derived, informational*
edges of the windows that a caller is free to ignore. The integration owns one per-charger
adapter with three operations, `assert_allow()`, `assert_hold()` and `read_state()`, called on
every planning cycle and on every charger event (plug, unplug, status change, reboot). Proposed
mapping, all reasoning on the findings above:

| Charger | HOLD (plugged in, not in a window) | ALLOW (in a window) | Can it hold *before* plug-in? | Weak points |
|---|---|---|---|---|
| Easee | Circuit dynamic limit < 6 A, or `pause` after the session starts | Circuit dynamic limit ≥ 6 A and `resume` | Yes: the circuit dynamic limit survives plug-in (the charger one does not). Lost on charger reboot | Re-assert after reboot; offline fallback current applies if the charger loses the cloud; circuit limit affects all chargers on the circuit; never use start/stop or the "smart charging" switch |
| Zaptec | "Stop charging" button after auto-start | "Resume charging" | Only by 0 A ("Charger max current"); then ALLOW must restore the current, because Resume will not | Stand-alone mode defeats both; cable unlocks while paused; ≤ 1 current change per 15 min |
| Wallbox | Pause/resume switch to paused | Switch to resume | Not documented | 90 s refresh; the charger's own schedule/EcoSmart must be off, "Resume schedule" re-enables it |
| OCPP | Session Current Limit 0 A (charger-dependent, unverified) | Limit back to max | Maximum Current 0 A (charger-dependent) | **Do not** use Charge Control: off ends the transaction and on does not start a new one |
| go-e | `frc` = Off | `frc` = On (or Neutral) | Yes (`frc` is a setting) | Some cars need `acp`; min pause duration may delay ALLOW; local and push, so the best-behaved |
| Monta | `stop_charging` after the session starts | `start_charging` | **No primitive found** | 120 s poll; Monta's own SmartCharge must be off; beta API; whether start works after a stop on every charger model is unknown |

Each adapter verifies by reading back power: after ALLOW, power above a threshold within two
poll intervals (Easee and go-e push: about a minute; Wallbox 3 min; Monta 4 min); after HOLD,
power near 0 in the same time. On failure it applies the brand's "reverse what stopped it" rule
once, then raises a repair issue and a notification. The output of `read_state()` (allowed, held,
charging, car refused) feeds the next engine call's `is_currently_charging`.

**Reactive versus pre-emptive hold: a real trade-off.**
- *Steelman for pre-emptive hold* (0 A or circuit limit < 6 A kept while the car is away): no
  energy leaks at plug-in, and no cable-unlock moment.
- *Against it* (reasoning): it **fails dry**. If Home Assistant is down overnight, the charger
  stays held and the car is not charged by morning. A reactive hold (pause after the plug-in
  event) **fails wet**: with Home Assistant down, the charger behaves as without the integration
  and the car charges at whatever price. Arithmetic on the leak: 11 kW for 90–120 s of detection
  lag (Wallbox, Monta) is 0.28–0.37 kWh. At the largest Danish peak/night tariff swing of
  1.06 DKK/kWh incl. VAT (`price_composition_denmark.md` §1, Radius winter) that is at most about
  0.4 DKK per plug-in.
- **Position:** reactive hold by default for every brand; pre-emptive hold only as an opt-in
  for Easee, Zaptec and go-e, with the integration releasing it (ALLOW) on its own shutdown and
  documenting the dry-failure risk. Monta cannot do pre-emptive hold at all.

**Current limits.** The planner needs on/off only: below 6 A there is no charge, low current is
inefficient, and the engine plans full power (`charging_physics_battery.md` §2–§3). Current
modulation belongs to load balancing (D13). The Zaptec 15-minute rule concerns current, not
Stop/Resume, so it binds only if the adapter holds through 0 A. With 15-minute price slots (O11),
windows are naturally multiples of 15 minutes. The "start late in the hour" partial slot that the
scheduling note recommends (`scheduling_algorithm.md` §1, CE-B) is fine for Stop/Resume chargers.
On a Zaptec held by 0 A it must not be shorter than 15 minutes. Express this as a soft start cost
(D19, `scheduling_algorithm.md` §2), never as a hard minimum near a deadline: evcc's hard
minimum made a plan miss its target (`prior_art_software.md`, pitfalls 1).

**Car actions.**
- `WAKE_UP_CAR` and `REQUEST_SOC_REFRESH` have no target on core Škoda, and the cloud refresh does
  not reach the car. **Position:** remove both from the engine's actions. The engine instead
  reports SoC quality (section 2) and, where it matters, a warning code meaning "a fresher SoC
  before T would change the plan". The caller decides whether it has a means to refresh and the
  rate budget for it (Tesla Fleet has a wake button; core Škoda has nothing). This keeps D2: the
  engine never emits a command whose target may not exist.
- `SET_CHARGE_LIMIT`: no target on core Škoda. The scheduling note shows a charge limit must
  never be the means of cutting a partial slot (`scheduling_algorithm.md` §7, O9). **Position:**
  drop it from the engine (answers O9 with "never emitted"). The integration stops at the planned
  SoC through the charger (HOLD when the projected SoC reaches the window's planned level). The
  user's own limit in the MyŠkoda app is a backstop that the integration cannot read.
- Consequence for D18: the physics note says to read `car_max_soc` live each call
  (`charging_physics_battery.md` §6, §8). That is **impossible for core Škoda**: no limit sensor
  exists (sensor.py above). The integration must take it as configuration ("the limit set in your
  car's app") and detect a car-side stop. If the charger reports finished/`SuspendedEV`, or Škoda's
  `charging_state` is `conserving`, while the plan says charge, the integration infers that the car
  limit has been reached. It then passes `car_max_soc = current SoC` for the rest of the session and
  shows the warning "Car stopped at its own limit (≈ X %)".

### Gaps
- Command-to-power latency for each brand: not documented anywhere (the HA note found none; I
  found none). Read-back intervals above are poll or push intervals, not measured latencies.
- Whether Wallbox and Monta chargers auto-start at plug-in, and whether Monta's `start_charging`
  resumes a session it stopped: not found.
- Whether OCPP chargers accept a 0 A Session Current Limit: charger-dependent; the integration's
  charge automation guide returned 404.
- Whether an Enyaq accepts a long pause and resumes without a fresh wake: not found
  (`charging_physics_battery.md` §3, Gaps); MEB wake-up issues are reported and disputed (same, §3).

---

## 2. C5b: SoC without a timestamp, SoC from charger energy, O7, and whether D8's 20 minutes covers actuation lag

### Takeaway
For an Enyaq on core Home Assistant the caller can neither cure staleness (no wake) nor measure
it (no captured timestamp). It can do two things: **project** SoC during a session from the
charger's session energy, and **detect** a pre-drive reading by comparing it with the mileage
sensor. O7 should become "charge first": a low or unknown SoC triggers the safety floor at once.
The 20-minute buffer covers actuation and verification lag (minutes). The Octopus "30 minutes"
cited for it is a plug-in detection lag in a car-API product, not a deadline lag. What the buffer
does **not** cover is an error in the power model, such as 11 kW planned and 7.5 kW delivered.
That must be handled by conservative curves and by re-planning on projected SoC.

### Cited Findings
- `soc_last_updated` is not available for core Škoda; HA's `last_changed` records only when HA
  saw a change, wrong for an idle parked car — `home_assistant_data.md`, "Car integrations",
  Inferences, and mapping table row §4.1.
- The Škoda API's `ChargingStatus.state` is omitted "shortly after a drive", "treat an omitted
  state as unknown" — `home_assistant_data.md`, "Car integrations".
- The car reports SoC updates while active and during a charge, at its own pace — same note,
  Inferences ("SoC while charging").
- Session energy entities: Easee `session_energy` pushed over SignalR (`home_assistant_data.md`,
  "Charger integrations"); Zaptec "Session total charge", with the Energy Meter delayed 1 h ([Zaptec
  README](https://raw.githubusercontent.com/custom-components/zaptec/master/README.md)); Monta
  "Charge Energy", reset per charge ([Monta README](https://raw.githubusercontent.com/nickknissen/hass-monta/main/README.md));
  go-e `wh` ([keys.py](https://raw.githubusercontent.com/marq24/ha-goecharger-api2/main/custom_components/goecharger_api2/pygoecharger_ha/keys.py));
  Wallbox "added energy" ([HA docs](https://www.home-assistant.io/integrations/wallbox/)); OCPP
  `Energy.Active.Import.Register` where the charger supports it ([OCPP user guide](https://home-assistant-ocpp.readthedocs.io/en/latest/user-guide.html)),
  with the warning that some measurands "give erroneous readings" (`home_assistant_data.md`).
- Wall-to-battery efficiency: 87.2 % (3φ 16 A) and 87.0 % (3φ 10 A) for a Kia e-Niro; under 7 %
  loss at an 11/22 kW wallbox for five 2026 cars including the MEB ID.7; car-side counters miss
  the losses — `charging_physics_battery.md` §2, §6.
- evcc: "If the SoC is unknown at plug-in, the system assumes that your vehicle is empty" and
  charges to minimum SoC at once — `prior_art_software.md`, "evcc", Floors; `driver_behaviour_ux.md` §4.
- Octopus, checked at source: "Intelligent Octopus Go checks in on your car at regular intervals to
  monitor your charging status. If the car is plugged in just after one of these checks, it could
  mean up to 30-minute delay in us stopping the charge" — [Octopus Intelligent FAQs](https://octopus.energy/intelligent-faqs).
- Possible 11 → 7.5 kW drop on MEB cars, from a phase drop or an SoC-linked reduction, unverified
  for the Enyaq — `charging_physics_battery.md` §1.
- evcc overruns were blamed on power falling at the end, load management and cold batteries
  (issue #24339); openWB treats a target as missed only 20 minutes after it and may start
  10 minutes early — `prior_art_software.md`, "evcc" and "openWB".
- The physics note found nothing suggesting 20 minutes is too short at 11 kW AC, and nothing for
  or against — `charging_physics_battery.md` §4, §8 (D8 "Silent").

### Inferences
**SoC projection (reasoning; the caller owns it under D10).** Anchor on the last car-reported
SoC value whose *change* HA observed. Then `soc_est = soc_anchor + (E_session − E_session_at_anchor)
× η / capacity`, and re-anchor whenever the car reports a new value. Use a deliberately low η
(e.g. 0.85) so that errors make the projection *under*-estimate. The plan then charges slightly
more, never less. Error size: an η error of ±5 points over 20 kWh is ±1 kWh, under 1.5 % SoC on a
75 kWh pack, which is well inside the 20 % arrival margin. With Zaptec, use "Session total charge",
never the Energy Meter (1 h late).

**Detecting a pre-drive reading without a timestamp (reasoning).** If the mileage sensor's
`last_changed` is later than the battery sensor's, the SoC predates the latest drive and must be
treated as stale. While the car is parked, a stale SoC is nearly right: parked drain is small,
though unquantified (`charging_physics_battery.md` §6–§7). So "age" in minutes is the wrong test
for a parked car. "Read before or after the last drive" is the right one.

**Contract change (reasoning).** Replace `soc_last_updated` with an optional
`soc_source ∈ {CAR_REPORTED, PROJECTED, ASSUMED}` plus the age where known. The engine uses it
only to (a) choose O7's behaviour and (b) emit the "fresher SoC would change the plan" warning.
`soc_max_age_minutes` survives as a tunable for callers that do have timestamps (Tesla Fleet).

**O7. Steelman for "wake first":** a stale reading of 9 % may really be 40 %, and charging at
once may buy energy at peak price. **Against:** for core Škoda "wake first" never ends, because
nothing can wake the car. The HA note already concluded that this would never charge
(`home_assistant_data.md`, O7 row). The cost of being wrong is bounded. A 15 % floor on a 75 kWh
pack is about 11 kWh. Bought at the worst peak instead of at night, at a swing of 1.06 DKK/kWh,
that costs at most about 12 DKK. **Position: charge first.** If the last known SoC, however old, is
below `min_safety_soc`, charge at once while re-planning on the projection. If the SoC is
**unknown** (API key expired, first plug-in), assume 0 % for the safety rule only, as evcc does,
and charge `min_safety_soc × capacity` kWh at once, then plan normally. `STALE_SOC_NEEDS_WAKEUP`
should stop being a terminal reason that blocks planning.

**Does D8's 20 minutes cover actuation lag? Decomposition (reasoning).**
1. *Plug-in detection lag* (charger auto-starts before the hold lands): seconds for Easee and
   go-e push, at most 90 s for Wallbox and 120 s for Monta. It costs money, not readiness. The
   Octopus 30 minutes is this kind of lag, arising because Octopus watches the **car** API. It is
   irrelevant when control goes through the charger, and it should not be used to size D8. This
   corrects `driver_behaviour_ux.md` §7, D8 row.
2. *Start lag at a window* (ALLOW → current flowing): an unmeasured cloud round trip plus
   read-back within one or two polls, so about 1–4 minutes. Covered by 20 minutes.
3. *Failure to start* (car asleep, Zaptec resume refused, OCPP session ended): needs a human. No
   buffer covers it. It is caught by verifying at the **first** window of the night, typically
   hours before departure, and notifying then.
4. *Power-model error*: planning 11 kW and getting 7.5 kW over a 20 kWh need takes 1.82 h against
   2.67 h, 51 minutes late. That exceeds the buffer. Only two things help: curves built from the
   car's own observed session power (D6/D16, caller), and re-planning on the projected SoC, so
   that slowness seen in the first hour adds hours before the deadline.

**Tension with the battery note's "latest of equal-price hours" tie-break**
(`charging_physics_battery.md` §5, §8). It pushes the last window flush against the buffer,
leaving no later hour for re-planning to use. **Position:** accept the tie-break, but have the
caller build the power curve from a low percentile of observed session power rather than from
nameplate, and make deadline-critical windows immune to every hysteresis or anti-churn rule in
the integration. evcc's `planDeadlineCritical` is the model for this (`prior_art_software.md`,
"Ideas worth borrowing", final inference). Keep 20 minutes as the default, keep it absolute (D8),
and hide it as an advanced setting.

### Gaps
- No measured Enyaq SoC update cadence while parked or charging, and no measured parked drain.
  These must be logged on the maintainer's car after 2026.11 (`home_assistant_data.md`, Gaps).
- No measured command-to-power latency for any brand.
- Whether HA's `last_reported` (as opposed to `last_changed`) helps for the Škoda sensors was not
  checked.

---

## 3. C7: defaults, and how few settings the user sees

### Takeaway
The three evidence streams agree more than they appear to. Low storage SoC does not hurt the
battery: calendar fade is flat from 10 to 60 %. Users want a guaranteed minimum and an untouched
buffer of 20–25 %, and they rarely enter plans. The money cost of a floor is mainly timing, not
energy. Proposed defaults: `min_safety_soc` 15 %, `default_arrival_soc` 20 %, `min_idle_soc` 50 %
(applied as a floor at every departure and reached by the expected plug-out), `default_target_soc`
80 %, buffer 20 minutes. One coupling must be enforced: **`min_safety_soc` must be below
`default_arrival_soc`**, or every planned return triggers price-blind charging.

### Cited Findings
- Users' requested minimum range: mean 70 km, median 50 km; 77 % want one; 3–4 main features
  wanted, no "overly complex interaction" — `driver_behaviour_ux.md` §1, §4 (Will & Schuller 2016).
- 20–25 % of range is kept as a psychological buffer, shrinking with experience —
  `driver_behaviour_ux.md` §4 (TU Chemnitz, Franke).
- 80 % of Electric Nation participants entered SoC for fewer than 1 in 5 sessions; few used
  journey planning; the default used when nothing was entered was a conservative 50-mile
  journey — `driver_behaviour_ux.md` §3.
- Overrides are mostly about an extra trip today or a long trip tomorrow, and more frequent with
  large batteries — `driver_behaviour_ux.md` §1.
- Danish sessions: plug-in around 17, plug-out 7–8 on weekdays; 60 % of re-plugs are more than
  24 h apart; half of sessions need under 12 kWh — `driver_behaviour_ux.md` §2 (Ziras et al. 2024).
- Calendar ageing: NMC loses ≈3 % at 10–60 % SoC against ≈5.5 % at 70–95 % over 10 months at 25 °C;
  the step is at ~55–70 % cell SoC; "≤50 % when unused is beneficial"; 100 % is a further step;
  80 % and 70 % are in the same plateau — `charging_physics_battery.md` §5 (Keil et al. 2016).
- The step's position in *displayed* SoC for MEB is unknown — `charging_physics_battery.md` §5.
- Škoda's charge limit accepts 50–100 % in steps of 10 — `home_assistant_data.md`, "Car integrations".
- evcc and Tibber charge a minimum at once regardless of price — `driver_behaviour_ux.md` §4;
  `prior_art_software.md`, comparison table.
- EV Smart Charging defaults the target to 100 % when none is given — `prior_art_software.md`, D7.

### Inferences
**`min_safety_soc` = 15 %.** *Steelman for 10 %:* it fires less often, so less price-blind
charging, and experienced drivers run lower. *For 20 %:* the Franke buffer. **Position: 15 %**
(reasoning). The median 50 km requested is roughly 12–14 % of a 75 kWh pack at the driver note's
illustrative consumption, and the battery is indifferent below 55 %. Because typical Danish
arrivals are above 50 % (`driver_behaviour_ux.md` §2, UK comparison), the rule rarely fires. What
matters more than the value is the ordering. The plan aims to return with `arrival_soc`. If
`min_safety_soc ≥ arrival_soc`, a trip that goes exactly to plan lands at or under the safety floor
and charges at peak price on arrival. Add to O10: **warn when `min_safety_soc ≥
default_arrival_soc`**.

**`default_arrival_soc` = 20 %.** Agree with the driver note (`driver_behaviour_ux.md` §7). The
battery and economics notes are silent. Carrying 5 % more costs nothing in price per kWh, only in
how early it is bought. Advanced setting, not first-run.

**`min_idle_soc` = 50 %, reached within the current plug-in.**
- *Steelman for lower (the battery note's spirit, and O1 lean (a)):* every kWh carried above need
  is bought earlier than necessary and may be dearer.
- *Steelman for higher (driver evidence):* unplanned trips are the main reason for overrides,
  and users rarely enter plans.
- **Position (reasoning):** 50 % is the highest value that stays just under the plausible
  calendar-ageing step (55–70 %, unverified for MEB), so the driver evidence gets what it asks
  for at no measurable wear cost. It gives about 30 points (≈ 22 kWh, very roughly 120 km) above
  the arrival margin for unannounced driving.
- Two changes to how it applies:
  1. **Deadline:** "by the expected plug-out", meaning the next recurring departure or, without
     one, 07:00 (Danish plug-out peak 7–8, Ziras). Not "within 24 h", which often lands after
     the car has left (`driver_behaviour_ux.md` §7, `min_idle_soc` row). The caller can pass
     `idle_planning_horizon_hours` as the hours until that time, so no engine change is needed.
  2. **Also a floor at every target**: the required SoC at a departure becomes
     `max(target_soc, arrival + consumption, min_idle_soc)`, capped as usual. Otherwise a lean
     commute target (say 35 %) lets the car leave far below the floor the user set, and the evening
     unplanned trip, the main override trigger, finds it short. This is a change to pass 1
     (`motor.md` §6.2).

**`default_target_soc` = 80 %.** All streams support it: the battery note (100 % is a distinct
step; 80 and 70 share a plateau), product convention (Ohme's example; EV Smart Charging's 100 %
default is the outlier), and Škoda's 10 % steps. Keep it, as the cap for opportunistic and one-off
charging. Do **not** make it the nightly target. Nightly readiness comes from `min_idle_soc` and
the departures.

**Buffer 20 minutes.** Keep (section 2). Advanced setting.

**How many settings (reasoning, from Electric Nation and Will & Schuller).**
- **First run:** charger, car SoC entity, battery capacity, price source; one "usual departure"
  time with its weekdays (default 07:00, Mon–Fri); and the car's own limit (default 80 %, "as set
  in your car's app").
- **Everyday:** three numbers, named in the user's terms: "Charge at once below" (15 %), "Keep at
  least" (50 %), "Charge up to" (80 %). Show them in km as well (`driver_behaviour_ux.md` §4).
- **Advanced:** arrival margin, buffer, forecast premium, opportunistic ceiling (section 5).

### Gaps
- No source gives the MEB mapping from displayed to cell SoC, so "50 % is below the step" is
  plausible, not verified.
- No study measured which arrival SoC drivers pick when asked per trip
  (`driver_behaviour_ux.md` §4, Gaps).
- The cost of applying `min_idle_soc` at every target was not simulated. The scheduling note's
  harness (`scheduling_algorithm.md` §1–§2) could measure it.

---

## 4. O12 and C8 (user side): manual controls, weekday departures, missed targets, missing prices, and the plug-in display

### Takeaway
Every manual control maps onto existing engine inputs or onto one caller-side override, so O12
needs no engine change. The override is a trust device more than a used feature. It must be
session-scoped, visible and self-reverting. Two caller duties the notes leave open must be
designed in: what happens to a **missed** target (keep charging toward it while still plugged
in, and say so), and what happens with **missing** spot prices (plan on the known Danish grid
tariff, flagged as estimated). At plug-in the user must see four things: ready-by status, next
start, expected cost, and any shortfall with a one-tap remedy.

### Cited Findings
- Override use: 2.5–4.2 % of sessions; a third pressed it only to test it; it applied to one
  transaction and reverted — `driver_behaviour_ux.md` §1, §6 (Electric Nation).
- Session-scoped conventions: evcc's "1x" Always charge "switches off automatically when the
  vehicle is disconnected"; its temporary limit applies to the current session —
  `prior_art_software.md`, "Ideas", item 6; `driver_behaviour_ux.md` §6.
- Ohme Max Charge reverting at unplug: the driver note cites Ohme support pages as opened
  (`driver_behaviour_ux.md` §3, §6). The prior-art note says the same pages returned 403 and used
  the claim only as a snippet (`prior_art_software.md`, "Commercial products"). I got HTTP 403 from
  [ohme-ev.com/support/how-do-i-update-my-charging-target](https://ohme-ev.com/support/how-do-i-update-my-charging-target/)
  on 2026-10-28. **Unverified;** the convention rests on Electric Nation and evcc instead.
- EV Smart Charging: master switch, manual start/stop buttons "totally independent of the
  automatic charging", a status enum, and a schedule attribute — `home_assistant_data.md`, "Manual
  controls".
- HA entity platforms include button, datetime, number, select, sensor, switch and time; there is
  no EV platform — `home_assistant_data.md`, "Manual controls".
- Users rarely enter plans; commercial apps converge on one recurring "ready by" plus a target —
  `driver_behaviour_ux.md` §3.
- Dropping a missed target: evcc switched to the next day's plan and stopped at 70–90 %
  (#24339, fixed with a plan lock); its loadpoint "keeps charging after the target time if the goal
  was missed"; a stateless call after `target.at` no longer sees the target —
  `prior_art_software.md`, "evcc" and pitfall 2.
- Missing prices: evcc's "simple plan" charges just before the target; Tibber's fallback started
  6 h before departure; ChargeSmarter only warns `INSUFFICIENT_PRICE_DATA` —
  `prior_art_software.md`, "Ideas", item 4.
- Danish grid tariffs are published months ahead in DataHub, hourly, and make up roughly half the
  smart-charging saving (a midnight timer captures it) — `price_composition_denmark.md` §1, §5, §7.
- Plan visibility (hours, cost) is what apps ship for trust; Danish drivers are confused by slow
  or late charging — `driver_behaviour_ux.md` §5.
- Calendars are read every 15 minutes — `home_assistant_data.md`, "Departure schedules".

### Inferences
**The manual controls (all reasoning). Engine mapping in brackets; none needs an engine change.**

| Control | HA entity | Behaviour | Engine mapping |
|---|---|---|---|
| **Charge now to X %** | `button` "Charge now" + `number` "Charge now to" (default = "Charge up to", 80 %) | Charges at once, price ignored, until the projected SoC reaches X, then hands back to the plan. Ends at unplug. Banner and cost estimate | Session-scoped override of `min_safety_soc` to X. The existing rule "below the safety floor → charge now" does exactly this. A target "at now", as the driver note suggests, would fall inside its own buffer and be refused (O10) |
| **Pause until** | `select` (1 h / until 06:00 / until unplug) or `datetime` | HOLD regardless of plan, always with an expiry. Shows the resulting shortfall at once | Caller-side HOLD, not an absence. An absence would still let the safety rule charge, and an explicit pause should win. The banner says so when SoC is below the safety floor |
| **One-off ready-by** | `datetime` + `number` target | A dated target; cleared after it passes (kept visible as met/missed until unplug) | `ChargeTarget`, with an optional cap |
| **Smart charging off** | master `switch` | Hands off: ALLOW permanently, so the charger behaves as without the integration (evcc "Fast"). Never "off = held" | Engine not called |
| **Usual departure** | `time` + weekday `select`/switches (default 07:00 Mon–Fri) | Expanded by the caller into targets over the whole price horizon (D27) | `ChargeTarget(at, target_soc = min_idle_soc)` per day, with an absence and learned consumption (section 5) |

Seven per-weekday `time` entities (as the HA note sketches) are more than users will set. One
time plus a weekday choice, with a calendar for exceptions, covers the Danish pattern of
consistent weekday plug-out (Ziras).

**Missed target.**
- *Steelman for "the engine has moved on, so drop it":* D10, and if the car is still plugged in
  after its departure time, the user evidently did not leave.
- **Position:** the caller keeps a small session memory. "Target at T for X % not met by T"
  stays active while the car remains plugged in and keeps charging, price-blind, up to X. This is
  evcc's post-fix behaviour, implemented as the same session-scoped safety-floor override as
  "Charge now to X". It ends at unplug or at X.
- Notify twice:
  1. **At plug-in**, if the plan already reports `PARTIAL`/`INFEASIBLE`, while the user can still
     act: "Ready 07:00 at 64 % of 80 % — 12 kWh short: not enough time" with buttons [Charge now]
     [Raise limit]. The cause comes from the D29 status and the warning code.
  2. **At T**, if it was missed.

**Missing prices.**
- *Steelman for evcc's "simple plan" (charge just before the deadline):* simple and predictable.
- *Against it, for Denmark:* it lands right in the 06–07 high-load tariff or, for an evening
  target, the 17–21 peak.
- **Position:** the caller fills the gap with the **known tariff + a spot proxy** (the forecast if
  any, else the last known daily mean), marked `is_forecast=True`. The engine then plans in the
  00–06 low-tariff block, which captures about half the value (`price_composition_denmark.md` §5).
  With no tariff either, a flat synthetic price plus the latest-slot tie-break reproduces evcc's
  simple plan.
- The display says "Planned on estimated prices". The engine needs no fallback mode.

**What the plan display must show at plug-in.** A `sensor` whose state is the translated
`PlanReason`/status, with these attributes or companion entities:
1. Ready-by status per next target: "Ready 07:00 at 80 % ✓" or the shortfall in % and km.
2. **Next charging start**, e.g. "next charge 01:15". A plan that starts at 03:00 otherwise looks
   broken at 22:00 (`driver_behaviour_ux.md` §5).
3. Expected cost of the plan, raw prices (`motor.md` §5), and, cheaply, the cost if charged now.
   The caller can price "charge now" from the same price list without a second plan.
4. SoC shown with its source ("62 % · estimated from charger", or "from car, before last drive").
5. Warnings in words: car stopped at its own limit, charger did not start, prices estimated.

Plus a `binary_sensor` "charging permitted now" and a `calendar` entity of planned windows,
which Home Assistant renders natively. All texts are translated from codes (D5), with Danish and
English kept in step as the repository requires.

### Gaps
- Ohme, Easee and Zaptec app conventions could not be opened (403/404/429 in both notes and for
  me), so commercial practice for "pause" and missed-target messages remains undocumented.
- No study measures whether a shown cost or savings figure changes override behaviour
  (`driver_behaviour_ux.md` §5, Gaps).

---

## 5. O2 and O1 from the user side, and the maintainer's trend-based view of charging extra

### Takeaway
O2: a global arrival margin, with an optional per-absence override in the engine that the
interface does not ask for. O1: the maintainer's trend intuition is right in direction. But the
forecast note shows that the **day ranking** inside the ordinary cheapest-first search beats a
trend switch. That ranking happens on its own once the integration expands the usual departures
over the full forecast horizon with learned daily consumption. So O1 can stay at "(a) floors only"
**in the engine**, with three conditions: recurring targets across the horizon, a small additive
forecast premium, and any opportunistic surplus beyond that kept below the ageing step.

### Cited Findings
- Users rarely enter per-trip data; a global default with an optional per-absence value is
  supported — `driver_behaviour_ux.md` §7, O2 row.
- Forecasts rank coming days well (Spearman ≈0.7–0.8, the actual cheapest of 6 days picked
  50–71 % of the time against 17 % by chance). Direction is reliable only for moves above about
  200–300 DKK/MWh. "Forecast next-cheaper" recovered 80–97 % of perfect-foresight savings against
  62–80 % for a trend switch. The premium should be about 50–100 DKK/MWh, additive, never above
  one MAE. The rule "needs an assumed daily consumption beyond the known targets, which the engine
  does not have" — `price_forecast_uncertainty.md` §7.
- A percentage markup misbehaves near zero and below; an additive markup in price units fits
  the evidence — `price_forecast_uncertainty.md` §4, §6; `price_composition_denmark.md` §7.
- The ageing step argues against surplus above ~55–60 % — `charging_physics_battery.md` §5, O1.
- Negative prices: a floors-only plan lost up to ~0.9 EUR/week of spot value, but the household
  total was negative in only 2 DK1 quarter hours in 13 months — `scheduling_algorithm.md` §7;
  `price_composition_denmark.md` §4.
- Prior art favours a user price threshold (option b), and EV Smart Charging has an
  "opportunistic" relative variant — `prior_art_software.md`, O1.
- Unplanned trips drive overrides; a modest fill buys trust — `driver_behaviour_ux.md` §7, O1 row.

### Inferences
**O2. Position:** add optional `min_soc_at_end` to `AbsenceWindow`, defaulting to
`default_arrival_soc`. The interface exposes only the global value. A calendar event may carry an
override later, but nothing asks the user for it. Cheap in the engine and consistent with D15.
High confidence.

**O1, steelmen.**
- (a) never: less wear, no surplus bought on a bad forecast. The battery note's view.
- (b) a user threshold: transparent, and what prior art ships. But an absolute DKK/kWh threshold
  goes stale every 1 October and 1 April when tariffs move (`price_composition_denmark.md` §1).
- (c) a percentile: needs no input. But it is not tied to whether the coming days are actually
  dearer.
- The maintainer's trend switch: intuitive. But it is dominated in simulation.

**Position (reasoning).** The forecast note's winning rule is "buy now what the coming days would
otherwise buy dearer". That is exactly what D22 does when the coming days' needs are in the input
as targets. The missing ingredient is not an O1 rule but **targets beyond tonight**. The
integration should therefore:
1. Expand the usual departures as targets over the whole price-plus-forecast horizon (up to
   7 days, D27), each with an absence whose `energy_kwh` is learned from history (charger kWh
   per weekday trip). Until learned, use one configured "typical daily driving (km)" setting.
2. Pass forecast hours with the small additive premium (O4; the economist's call on the value).
3. Then the engine, still floors-only, charges extra tonight exactly when tonight is cheaper than
   the forecast nights by more than the premium, and only as much as those days need. That is
   the maintainer's trend view, done properly.

Beyond that, for genuinely free energy (household total ≤ 0, or below a percentile), allow an
"opportunistic ceiling" capped at **60 %** by default rather than 80 %. That respects the ageing
step and gives the driver note's trust margin. It is advanced, off for consumer totals that are
never negative in DK2.

**What the user sees.** "Charging to 63 % tonight: Thu–Sat forecast ≈0.4 DKK/kWh dearer". The
trend reasoning should be visible because it is the reason the car charges more than the next
trip needs. This is a candidate L1 code with parameters (D5).

### Gaps
- Not simulated with the real engine: recurring targets over 7 days with learned consumption
  (`price_forecast_uncertainty.md` §7, Gaps). The scheduling harness could run it.
- Carnot, the forecast most Danish Home Assistant users have, is untested for day ranking.
- How well daily consumption can be learned from charger energy alone, for a car whose SoC
  reports are sparse, is unknown.

---

## 6. Where the notes contradict each other on facts, checked at source

### Takeaway
Six factual disagreements or mis-scopings matter for control and UX. Two change a recommendation:
the Octopus 30-minute figure is not a deadline lag, and `car_max_soc` cannot be read live from
core Škoda. The rest are scope corrections or unverified claims.

### Cited Findings
1. **Octopus "stop/start lag up to 30 min"** (`driver_behaviour_ux.md` §5, §7 D8 row). The source
   says the delay is in *stopping* a charge right after plug-in, caused by Octopus checking the
   **car** "at regular intervals" — [Octopus Intelligent FAQs](https://octopus.energy/intelligent-faqs).
   It is plug-in detection through a car API, not actuation lag at a deadline.
2. **Zaptec's 15-minute rule** (`home_assistant_data.md`, "Charger integrations"; the task brief:
   "change at most every 15 minutes"). The README scopes it to "the available charge current",
   because "Many EVs don't like getting too frequent changes". It does not cover Stop/Resume —
   [Zaptec README](https://raw.githubusercontent.com/custom-components/zaptec/master/README.md).
3. **Reading `car_max_soc` live** (`charging_physics_battery.md` §6, §8) against core Škoda: no
   limit or target-SoC sensor exists — [skoda sensor.py](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/skoda/sensor.py).
4. **Ohme support pages**: opened per `driver_behaviour_ux.md` §3/§6; 403 per
   `prior_art_software.md`; 403 for me today — [Ohme support](https://ohme-ev.com/support/how-do-i-update-my-charging-target/).
5. **Easee rate limits**: the HA note found none on developer.easee.com. I found none either, but
   the developer docs add two facts the notes lack: all dynamic values reset on charger reboot, and
   frequent current changes may upset some cars — [Easee developer: current limits](https://developer.easee.com/docs/current-limits-and-control).
6. **When core Škoda arrives**: MySkoda's README says 2026.10 (`home_assistant_data.md`), while the
   next-docs page says "introduced in Home Assistant 2026.11", and the current release is
   2026.10.4 — [HA next docs: Škoda](https://next.home-assistant.io/integrations/skoda/). The core
   docs are the later and more authoritative source.
- Not a factual contradiction but a value conflict: O1 is (a) in the battery note, (c) or (b) in the
  driver and price notes, "next-cheaper day" in the forecast note, and "fill when the total is
  ≤ 0" in the scheduling note. Section 5 reconciles them.

### Inferences
- Reasoning: items 1 and 3 change recommendations (D8 sizing; D18 as configuration plus
  car-stop detection). Item 2 means a Zaptec adapter that holds through Stop/Resume rather than
  0 A is free of the 15-minute constraint. Item 5 adds "re-assert after reboot" to the Easee
  adapter.

### Gaps
- GitHub issue trackers were not reachable for any integration, so known bugs in hold/resume
  behaviour per brand were not reviewed.

---

## 7. Recommendations by decision and question ID

### Takeaway
The engine changes little: drop car commands from its actions, accept an SoC quality flag, apply
`min_idle_soc` at every target, add an optional `min_soc_at_end`, and add two validations. The
integration grows: per-charger ALLOW/HOLD adapters with read-back, SoC projection, session-scoped
overrides, missed-target continuation, a tariff-based price fallback, and a plug-in display.

### Cited Findings
- Evidence for each row is cited in sections 1–6.

### Inferences
All recommendations below are reasoning on the cited findings.

| ID | Recommendation | Confidence | What evidence would change it |
|---|---|---|---|
| C5 actions (`START/STOP_CHARGING`) | Control contract = `windows` + `should_charge_now`. The caller asserts ALLOW/HOLD as a level, idempotently, every cycle and on every charger event, and verifies by reading power back. Edge actions become informational or are removed | High | A charger whose only reliable control is a one-shot timed command (none found) |
| C5 hold at plug-in | Reactive HOLD by default for all brands. Pre-emptive hold opt-in for Easee (circuit dynamic < 6 A, re-assert after reboot), Zaptec (0 A, release by current not Resume) and go-e (`frc` Off). Not possible on Monta | Medium | Measured plug-in leak much larger than 2 min; or a charger offering a hold with an expiry (fails wet) |
| C5 current limits | Planning needs on/off only; current is for load balancing (D13). A Zaptec held through 0 A gets windows ≥ 15 min through a soft start cost, never a hard rule | Medium | Evidence that the Enyaq tolerates frequent current changes, or Zaptec docs applying the 15-min rule to Stop/Resume |
| C5 `WAKE_UP_CAR`, `REQUEST_SOC_REFRESH` | Remove from engine actions. Engine reports SoC quality and a "fresher SoC before T would change the plan" warning; caller maps it to whatever its car offers, within a rate budget (Škoda: none useful) | Medium-high | Core Škoda adding wake or refresh, or a car fleet where waking is the norm |
| O9 / `SET_CHARGE_LIMIT` | Never emitted by the engine. Stop at planned SoC via charger HOLD on projected SoC; the car's own limit is a backstop | Medium | Core Škoda adding a limit `number` (then optional, rounded up to 10 % steps, as a ceiling only) |
| D18 `car_max_soc` | Configuration ("limit in your car's app"); detect car-side stop (charger finished/`SuspendedEV`, Škoda `conserving`) and pass current SoC as `car_max_soc` for the session | Medium | A readable limit sensor upstream |
| §4.1 `soc_last_updated` | Replace with optional `soc_source` (CAR_REPORTED / PROJECTED / ASSUMED) and age if known. The caller projects SoC from charger session energy at a low η (≈0.85) and flags pre-drive readings via the mileage sensor | High (projection), medium (field shape) | Upstream `carCapturedTimestamp` sensor; measured SoC update cadence |
| O7 | Charge first: last known SoC < `min_safety_soc` → charge at once. Unknown SoC → assume 0 for the safety rule only (charge `min_safety_soc × capacity` kWh). Staleness never blocks planning | High | Evidence that low-SoC false alarms are frequent and costly (unlikely: bounded at ~12 DKK per event) |
| D8 buffer | Keep 20 min, absolute, advanced setting. It covers actuation and verification lag (minutes). Power-model error is handled by conservative learned curves and re-planning; start failure by verification at the first window. Octopus 30 min does not apply | Medium | Measured Enyaq end-of-charge overruns > 20 min with learned curves; measured command latency > 10 min |
| D8 vs late tie-break | Accept "latest of equal hours" only with curves built from observed low-percentile power, and deadline-critical windows exempt from all hysteresis | Medium | Logged sessions showing the last window regularly running short |
| `min_safety_soc` | 15 % default, shown in km too | Medium | Danish data on arrival SoC; user feedback that it fires too often |
| O10 (new) | Warn when `min_safety_soc ≥ default_arrival_soc` (planned returns would trigger price-blind charging); keep the existing proposals | High | — |
| `min_idle_soc` | 50 % default; deadline = expected plug-out (next usual departure, else 07:00), not 24 h; also a floor at every target in pass 1 | Medium | MEB SoC mapping placing the ageing step below 50 % displayed; simulation showing material cost |
| `default_arrival_soc` | 20 % default, advanced | Medium | Per-trip choice data; experienced-user feedback |
| `default_target_soc` | 80 %; cap for opportunistic and one-off charging, not a nightly target | High | Manufacturer guidance for the Enyaq pointing elsewhere (not verified in any note) |
| Settings count | First run: charger, SoC entity, capacity, price source, usual departure, car's limit. Everyday: three SoC numbers. The rest advanced | Medium | Usage telemetry or user tests showing the three numbers are misunderstood |
| O12 charge now | "Charge now to X %" = session-scoped `min_safety_soc` override to X (default 80), ends at unplug, banner + cost | High | — |
| O12 pause | "Pause until" = caller HOLD with mandatory expiry; wins over the safety floor, with a visible warning | Medium-low | Maintainer preference that safety should beat an explicit pause |
| O12 ready-by, smart off | One-off `datetime` + target → `ChargeTarget`; smart off = ALLOW permanently (hands off), never held | High | — |
| Weekday departures | One time + weekday choice (default 07:00 Mon–Fri), calendar for exceptions; expanded over the full horizon | Medium | Users needing different times per weekday in practice |
| C8 missed target | Caller keeps "missed target" while plugged in and continues price-blind to its SoC; notify at plug-in if `PARTIAL`, and at T if missed | Medium | Maintainer preference to stop at departure; evidence that a late car is usually already gone |
| C8 missing prices | Caller fills with known grid tariff + spot proxy, `is_forecast=True`; display "estimated prices"; no engine fallback mode | Medium | A price source that already provides totals for the whole horizon |
| Plug-in display | Ready-by status and shortfall, next charge start, expected cost (and cost if charged now), SoC with source, warnings; plus a `calendar` of windows and a "permitted now" binary sensor | High | — |
| O2 | Optional `min_soc_at_end` on `AbsenceWindow`, default `default_arrival_soc`; interface exposes the global only | High | — |
| O1 | Engine floors-only (a), **provided** the caller expands usual departures over the whole forecast horizon with learned consumption and forecasts carry a small additive premium. That reproduces the maintainer's trend view as day ranking. Separate opportunistic surplus only for free energy, capped at 60 % | Medium-low | Simulation of the real engine on a year of forecasts; Carnot ranking quality; a calendar-ageing step found above 60 % displayed for MEB |
| D28 `charger_auto_threshold` | Off by default; prefer dropping it and modelling free energy as cheap slots. Two controllers fight: Zaptec resume semantics, Easee LED disabling plans, Monta's own SmartCharge | Medium | A charger exposing a readable total-price threshold |

### Gaps
- No live test was possible: no charger and no Enyaq on core 2026.11. Before the defaults above
  are adopted, log on the maintainer's car: SoC update cadence, mileage-versus-SoC timestamps,
  plug-in auto-start and hold lag, command-to-power latency, and session power against SoC.
