# Panel position paper: battery and EV-charging engineer (charging physics, battery wear, safety levels)

Written 2026-10-28 for the ChargeSmarter planning engine (`docs/design/motor.md`,
`docs/design/decisions.md`). It reviews the seven research notes in this folder from the battery
and charging side and takes a position on conflicts C1/O1, C6 and C7, and on what the Škoda data
reality means physically.

How to read it:
- A claim with a URL was checked on a page I opened during this task.
- A claim citing a note (for example `charging_physics_battery.md §5`) rests on that note's
  source. Where I could not open the original myself, I say so.
- **(reasoning)** marks my own engineering judgement or arithmetic. It is not a sourced fact.
- Money: EUR figures are converted at an **assumed** 7.46 DKK/EUR, which is roughly Denmark's
  ERM II central rate. I did not open a primary page for that rate in this task, so treat it as
  an assumption.
- Car: the maintainer's Škoda Enyaq is MEB-platform, charges at home on 11 kW three-phase AC, and
  he reports 11 kW falling to about 7.5 kW above 60–70 % SoC.

---

## 1. C1 / O1 from the battery side: what is the wear worth, where is the break-even, and is "charge as late as possible among equal-cost options" sound?

### Takeaway
The two notes conflict less than they seem to.
- The driver note's **idle floor of 40–50 %** sits *below* the calendar-ageing step (about
  55–70 % cell SoC). Volkswagen itself advises parking at 30–80 %. The battery side accepts it.
- The real conflict is O1: **filling to ~80 % in cheap hours and parking there**.

The money:
- I value 1 percentage point of lost capacity at **about 1,000–3,700 DKK** (central 2,000).
- Parking above the step rather than below it costs roughly **0.5–1.5 points a year** in a
  Nordic climate. That is **about 500–5,500 DKK a year** (central ≈2,000), or about **5.5 DKK
  per day** spent above the step.
- This is the same size as the *whole* multi-day saving O1 could earn: roughly 330–420 DKK a year
  in the Swedish study, and up to about 1,000–1,600 DKK a year in an optimistic Danish October
  sample.
- It is small next to the within-night savings, 600–3,000 DKK a year. Those cost no wear at all.

Break-even, central case: storing energy above the step pays only if the expected price
difference is at least **≈0.3 DKK/kWh for every day the energy is held** (range 0.07–0.8).

Position:
- **O1: charge beyond the floors only up to a ceiling below the step (default 55 %)**, using the
  forecast note's next-cheaper-day rule.
- Go above that ceiling only for a target that needs it.
- Among equal costs, charge late. This is sound, and it suits winter: the pack is warm at
  departure, and the after-arrival hours are the dearest tariff hours anyway. The price of late
  charging is readiness risk, which the completion buffer and the caller's verification must
  carry.

### Cited Findings
**What the notes claim**
- Driver note:
  - Make `min_idle_soc` high enough for an unplanned round trip, "~40–50 %".
  - Prefer O1 (c), a percentile of the horizon's prices, "up to `default_target_soc`" (80 %).
  - Reason: users rarely enter trips, and overrides come from unplanned trips.
  — `driver_behaviour_ux.md §7` (Electric Nation, Ziras et al. 2024, Will & Schuller).
- Battery note:
  - Calendar ageing runs in plateaus, with a step at about 55–70 % SoC. 70–95 % is one
    "high-fade" plateau.
  - It "supports option (a), never". If (b) or (c) is adopted, "the surplus should be capped
    below the step (e.g. ≤ 55–60 %)".
  — `charging_physics_battery.md §5, §8` (Keil et al. 2016, J. Electrochem. Soc. 163 A1872;
  ECS IMLB 2016 abstract).
- Forecast note: O1 is best served by charging beyond the floors "only for days whose forecast
  price, plus the markup, is higher than the known price now … up to `default_target_soc`".
  The simulation had no wear term — `price_forecast_uncertainty.md §7.6`.
- Scheduling note: lean (a) is "contradicted when prices go negative" (DK1 Jan–Sep 2025, 411 of
  6,527 spot hours negative). At minimum, fill up to `default_target_soc` when the *consumer*
  price is ≤ 0 — `scheduling_algorithm.md §7`.

**Ageing magnitude**

These are all as read by the battery note. I could not open the Keil PDF myself (bot wall).
- Keil et al., NMC cells, about 10 months of storage, relative capacity read from Fig. 2b:

  | Storage SoC | 25 °C | 40 °C |
  |---|---|---|
  | 10–60 % | ≈0.97 | ≈0.93–0.95 |
  | 70–95 % | ≈0.94–0.945 | ≈0.89–0.90 |
  | 100 % | ≈0.935 | ≈0.81 |

  At 50 °C, ≈0.88–0.90 at 10–60 % and ≈0.83 at 70–95 % — `charging_physics_battery.md §5`.
- Werner, Paarmann & Wetzel (KIT 2021, graphite/NCA): "A large impact of the storage state of
  charge at 100% is evident, whereas the influence is small below 80%" —
  `charging_physics_battery.md §5`.
- Real-world fleet (Geotab, 22,700+ EVs, 21 models):
  - 2.3 %/year on average; mainly AC-charged cars about 1.5 %/year; DC-heavy cars up to
    3.0 %/year; hotter regions +0.4 %/year.
  - A wider SoC range "did not materially increase degradation, unless they spent extended
    periods close to full or empty charge".
  — [Yahoo Finance on Geotab, 2026-01-13](https://finance.yahoo.com/news/geotab-data-points-modest-rise-141059571.html) (opened).

**Money: what a point of capacity is worth**
- New MEB (ID.3/ID.4) battery pack: about **10,000–15,000 EUR** "nach Informationen von
  Autobild"; VW gave no exact prices. Installation is extra, at labour rates of up to 200 EUR/h.
  Most manufacturers prefer replacing single modules —
  [ecomento.de, 2022-02-24](https://ecomento.de/2022/02/24/elektroauto-batterie-ersatz-ist-teuer/) (opened).
- VW (sister MEB brand) warranty: the high-voltage battery "is warranted for 8 years or
  160,000 kilometres", covering a "net capacity loss below 70%" —
  [Volkswagen Canada, battery tech and maintenance](https://www.vw.ca/en/electric-vehicles/about-electric-vehicles/battery-tech-and-maintenance.html) (opened).
  Škoda's own warranty document was not opened. UK used-car listings state 70 % for the Enyaq,
  but those are search snippets only (see Gaps).
- Enyaq 85 (MY27):
  - 82.0 kWh nominal, **77.0 kWh usable**, NMC.
  - 11 kW on-board charger.
  - German list price 50,450 EUR.
  — [EV Database, Škoda Enyaq 85](https://ev-database.org/car/3570/Skoda-Enyaq-85) (opened).

**Savings to compare against** (from the notes)
- Within-night smart charging against plugging in at 17:00: about 1,400–3,000 DKK/yr. Against a
  fixed midnight timer: about 600 DKK/yr — `price_composition_denmark.md §5` (own calculation on
  Energi Data Service data).
- Multi-day forecasts in Sweden (SE3, 50 km/day, 7.4 kW): the extra saving "above and beyond
  within-day optimisation" is **44–56 EUR per vehicle per year** —
  `price_forecast_uncertainty.md §5` (Kjellergren & Lindqvist Sabel 2026).
- Danish October 2026 simulation (23 decisions, 10 kWh/day), average spot price paid:

  | Battery | Floor-only | Forecast next-cheaper rule |
  |---|---|---|
  | 50 kWh | 718 DKK/MWh (DK1) | 372 DKK/MWh (DK1) |
  | 30 kWh | 718 DKK/MWh (DK1) | 499 DKK/MWh (DK1) |

  — `price_forecast_uncertainty.md §7.6`.
- Mean absolute day-to-day change of the DK1 daily mean in that window: 344 DKK/MWh. Direction
  forecasts are reliable only for predicted moves above about 200–300 DKK/MWh —
  `price_forecast_uncertainty.md §7, §7.3`.

**Timing, warmth and readiness**
- Škoda's representative: "Always set your departure time". While charging at a station the
  battery is heated "to 23 degrees" and "the charging speed is bit lower". The thread does not
  separate AC and DC — `charging_physics_battery.md §4` (Rehak thread).
- ADAC: in winter, charge right after driving while the battery is warm —
  `charging_physics_battery.md §2, §4` (autohaus.de on ADAC 2022).
- VW: "Before long trips, Volkswagen recommends setting the charging target at 100%", and
  "driving off as soon as possible after charging is completed" —
  [VW Canada](https://www.vw.ca/en/electric-vehicles/about-electric-vehicles/battery-tech-and-maintenance.html).
- evcc's "late charging" reserves 15 min to 2 h of the charge for just before departure, for a
  warm car and less time at high SoC. Its planner breaks price ties toward later slots —
  `prior_art_software.md` (evcc planner.go, plans.mdx); `scheduling_algorithm.md §1`.
- Winter grid tariff (Radius): 0.106 DKK/kWh at 00–06 against 0.956 at 17–21, excl. VAT —
  `price_composition_denmark.md §1`.
- Overruns have been blamed on power falling at the end of a charge, load management and cold
  batteries — `prior_art_software.md` (evcc #24339).

### Inferences
**(reasoning) Value of one point of capacity (V1).**
- Replacement view: 10–15 kEUR ≈ 74,600–111,900 DKK for a pack that the warranty treats as
  "worn" after 30 points. That is 2,500–3,700 DKK per point.
- This overstates the cost in practice:
  - At the fleet's AC rate of ~1.5 %/yr, an Enyaq reaches only about 85 % SoH after 10 years, so
    a replacement is unlikely within the car's life.
  - Pack prices have probably fallen since 2022.
  - The resale effect of SoH looked threshold-like in the material I saw, but I could not open a
    per-point price study (Gaps).
- I therefore use **1,000–3,700 DKK per point, central 2,000**. No Danish figure was found.

**(reasoning) Extra fade from parking above the step.**
- At 25 °C, Keil's NMC data give about 2.5 points more loss in ~10 months in the 70–95 % plateau
  than at 10–60 %. That is ≈3 points a year *if parked high all the time*.
- Keil's own low-SoC figures fall by about half from 40 °C to 25 °C. Extrapolating the same factor
  down to a Danish pack at roughly 5–15 °C gives about 1–1.5 points a year. The pack temperature
  range is an assumption, not sourced.
- Calendar fade also slows with time.
- Geotab finds SoC habits "not material" unless extended periods are spent near full, and the
  whole AC fleet loses only ~1.5 %/yr. A policy effect of ≥1.5 points a year would be visible
  there.
- I take **0.5–1.5 points a year** for "parked above the step" against "parked below it". This is
  an engineering range, not a measurement.

**(reasoning) Annual wear cost of an O1 "fill to 80 % and park" policy.**
- 0.5–1.5 pt/yr × 1,000–3,700 DKK/pt = **500–5,550 DKK/yr**, central ≈2,000 DKK/yr.
- Per day above the step: 1.4–15 DKK, central **≈5.5 DKK/day** (≈0.23 DKK/h).

**(reasoning) What O1 can earn.**
- The Danish simulation's saving of 0.35 DKK/kWh (50 kWh) or 0.22 DKK/kWh (30 kWh) spot on
  3,650 kWh/yr is ≈1,000–1,600 DKK/yr incl. VAT. That assumes October 2026's volatility all year,
  which is optimistic.
- Lund's 44–56 EUR ≈ 330–420 DKK/yr is the more robust figure.
- Both are gross, before wear. The simulation's 30–50 kWh "stock" is exactly energy held at high
  SoC.

**(reasoning) Break-even per kWh.** Storing E kWh above the step for d days pays when
Δp × E > 5.5 DKK × d.
- For the Enyaq from 55 % to 80 %, E ≈ 19 kWh, so Δp must be at least
  **≈0.29 DKK/kWh per day held** (range 0.07–0.8).
- In the October sample the mean day-to-day move was 0.34 DKK/kWh excl. VAT (0.43 incl. VAT).
  So holding above the step for one day before a clearly forecast rise roughly breaks even.
  Holding for several days, or for a small forecast rise, loses.
- This lines up with the forecast note's finding that direction is noise below about
  0.1–0.3 DKK/kWh.

**(reasoning) Filling *below* the step is free from the battery side.**
- Keil's 10–60 % band is one plateau, so 30 % → 55 % adds no extra calendar fade.
- On a 77 kWh Enyaq, 30 → 55 % is about 19 kWh, roughly two days of a 10 kWh/day commute.
- That covers most of the "buy before a dearer day" value the forecast note found, without wear.
- Hence: **O1 = the next-cheaper-day rule, capped at an opportunistic ceiling of 55 % by default**.
  Targets may go higher under their own caps (D7).
- The driver note's 40–50 % idle floor fits under that ceiling.

**(reasoning) Negative prices.**
- At a consumer total ≤ 0, buying more costs nothing but wear. Above the step, wear is ≈5.5 DKK
  per day for the whole pack.
- The DK consumer total was negative in only 2 quarter-hours in 13 months in DK1, and never in
  DK2 (`price_composition_denmark.md §4`).
- Rule: fill to the opportunistic ceiling at a total ≤ 0. Above it, only when a target follows
  within about a day. The spot-only negative hours in `scheduling_algorithm.md §7` overstate the
  opportunity, because Danish tariffs keep the total positive.

**(reasoning) Late tie-break: sound, free, and it suits winter.**
- Among equal (or within-ε) marked-up prices, the latest slot minimises hours at high SoC, and in
  winter leaves a warmer pack at departure (Škoda's own advice).
- The ADAC's "charge right after driving" competes with the 17–21 peak tariff. That costs about
  0.85 DKK/kWh more excl. VAT (Radius) for an efficiency gain that no source quantifies for AC.
  For the cost of a cold start to win, cold charging would have to lose more than half its
  energy. Nothing found suggests that for AC. Price wins.
- **Readiness risk** is the real cost of "late". The last slot is the one with no recovery if:
  - the car does not start (MEB wake-up reports, `charging_physics_battery.md §3`);
  - a cloud charger lags (Octopus up to 30 min, `driver_behaviour_ux.md §5`);
  - the cold slows the charge.

  Mitigations:
  - keep the late tie-break for *ties only*, with a small ε;
  - keep D8's absolute buffer, and let the caller raise it in winter or for slow-acting chargers;
  - the caller verifies that a planned window actually started, and re-plans at once if not.
- **For 100 % targets:** VW says charge to 100 % and leave soon after. The energy above ~80–90 %
  should therefore be the last energy delivered. A tie-break alone does not guarantee this. A
  SoC-dependent holding cost in scoring does (see §7).

### Gaps
- No Danish battery-replacement price for the Enyaq. No regression of Danish used-EV prices
  against SoH. A Recurrent/Recharged-type "price per % SoH" appeared only in search summaries,
  which suggested a threshold effect around 80–90 % SoH; these pages were not opened.
- Škoda's own warranty terms (70 %?) were not opened. The UK listings' "70 % guaranteed" is a
  snippet only.
- Keil et al.'s PDF could not be opened (Anubis bot wall); the figures rely on the battery note's
  reading. No temperature-scaling constant (Arrhenius activation energy) for MEB-type NMC cells
  was opened. A secondary paper using Schmalstieg's model gives only the form
  `Q_loss,cal = α_cal(T,V)·t^0.75` without constants —
  [EV-EcoSim, arXiv 2401.04705](https://arxiv.org/pdf/2401.04705) (opened).
- Where the anode step falls in the Enyaq's *displayed* SoC is unknown: MEB cell balancing was
  not found, and the net/gross mapping is only 77 of 82 kWh.

---

## 2. C6: the charging model, the caller's inputs, single-phase hours, AC taper, the 11 → 7.5 kW cause, 6 A and phase switching, and cold weather

### Takeaway
- **Efficiency model.** Keep one constant efficiency, plus an optional fixed overhead in kW. This
  is simpler than an efficiency-by-power curve and good enough:
  - It reproduces every measurement in the notes: flat at three-phase 10–16 A, a penalty for
    single-phase and 6 A.
  - At 11 kW and 7.5 kW on an Enyaq, the two models differ by under 1 point.
- **Phase switching** on MEB means stopping and restarting the session (one forum report).
- **Partial hours:** charge at full power for part of the slot, not at a low current for all of
  it. The minimum is 6 A, about 4.1 kW three-phase.
- **Cold weather:** belongs in the caller's per-call efficiency or overhead (D6). Its size for AC
  on the Enyaq was not found.
- **The 11 → 7.5 kW drop:** most likely a **car-side current reduction on all three phases**
  (about 16 → 11 A). Possibly it is temperature-linked rather than purely SoC-linked. A phase
  drop is a close second, and charger load balancing is the third candidate.
  - Per-phase current and voltage logged in Home Assistant can tell these apart in 2–3 sessions.
  - Do not put `[(65, 7.5)]` into `car_power_soc_steps` until they have.

### Cited Findings
**Efficiency and overhead**
- Kia e-Niro, wall to battery, 21–23 °C (one car, one dyno study):

  | Supply | Efficiency |
  |---|---|
  | 3-phase 16 A | 87.21 % |
  | 3-phase 10 A | 86.98 % |
  | 1-phase 16 A | 80.32 % |
  | 1-phase 10 A | 79.58 % |

  — `charging_physics_battery.md §2` (Reick et al. 2021).
- ADAC 2022, losses at a household socket against an 11 kW wallbox: **VW ID.3 13.6 % vs 9 %**.
  Control units draw an estimated 100–300 W while charging — `charging_physics_battery.md §2, §7`
  (autohaus.de on ADAC).
- ADAC 2026 (incl. **VW ID.7, MEB**): wallbox 11/22 kW "under 7 %" loss for all five cars;
  9.1–12.8 % at reduced wallbox power for four of them — `charging_physics_battery.md §2`
  (firmenauto.de on ADAC 2026).
- evcc's estimator assumes `ChargeEfficiency = 0.85` — `prior_art_software.md` (evcc
  estimator.go). openWB added efficiency to scheduled charging in 2026-05 —
  `prior_art_software.md` (openWB #3393).

**Enyaq AC hardware**
- Enyaq 85: 11 kW on-board charger; three-phase 16 A 11 kW; one-phase 32 A 7.4 kW; one-phase
  16 A 3.7 kW. 22 kW stations are limited by the on-board charger —
  [EV Database](https://ev-database.org/car/3570/Skoda-Enyaq-85).
- The smaller Enyaq iV 50 has a 7.2 kW on-board charger —
  [evspecs.org, Enyaq iV AC charging](https://www.evspecs.org/technical-data/skoda/enyaq-iv/ac-charging)
  (opened). A VW e-up! is 7.3 kW on 2 phases — `charging_physics_battery.md §1` (Reick).
- Minimum current 6 A, about 4.1 kW three-phase. An MEB owner's 6 A three-phase charge averaged
  ~4.2 kW — `charging_physics_battery.md §3`.
- Enyaq iV 80: changing between 1 and 3 phases needs a stop and restart of the session (one
  forum thread) — `charging_physics_battery.md §3`.

**Taper and drop reports** (all anecdotal)
- ID.3 Pro S, software 5.0: "er hat bei 67% angefangen zu reduzieren (Ziel: 80 %)", down to
  3.7 kW; a departure time was set — `charging_physics_battery.md §1` (GoingElectric).
- MEB owners: drops to "just under 7 kW" by losing one phase, attributed to voltage sag
  ("about 7 % drop at 15.4 A"). One owner saw it only above ~10 A. SoC is not mentioned —
  `charging_physics_battery.md §1` (meinid.com).
- VW-group app setting "maximale Netzbelastung: max / reduziert" (Škoda app, e-up!/Citigo
  thread). "Reduziert" limited AC to about 5 A and was found set without the owner's knowledge.
  A reply says it applies only when no charge timer is used. This is a non-MEB car —
  [GoingElectric thread "Onboard charger scheinbar defekt? – falsche settings!", Sep 2022](https://www.goingelectric.de/forum/viewtopic.php?p=1932968) (opened).
- Škoda Public API charging profiles carry `maxChargingCurrent` REDUCED/MAXIMUM —
  `home_assistant_data.md` (Škoda OpenAPI spec).
- Danish installations: most have a 25 A fuse (max 11 kW three-phase) —
  `driver_behaviour_ux.md §2` (Ziras et al. 2024).
- motor.md's example taper is "11 kW falling to 7.5 kW from 65 %" — `docs/design/motor.md §4.2`.
- The scheduling note's real-week experiment assumed a different taper: 11 kW to 60 of 75 kWh
  (80 %), 7 kW to 67.5 kWh (90 %), 3.5 kW above — `scheduling_algorithm.md §2`.

**Cold**
- Škoda software heats the pack for driving only to "just above 0 degrees" since ME3, and to
  23 °C while charging at a station — `charging_physics_battery.md §4` (Rehak).
- ME3 software: thermal management "is activated at lower temperatures than previously", and
  temperature control "is now continuously adjusted" —
  [theevreport.com, 2022-02-25](https://theevreport.com/skoda-enyaq-iv-enhanced-with-new-software) (opened).
- The only cold-efficiency data is DC: 39 % at −25 °C against 93 % at +25 °C, measured on the
  off-board charger — `charging_physics_battery.md §4` (JRC, Trentadue et al. 2018).

### Inferences
**(reasoning) Power-dependent efficiency vs constant efficiency plus overhead.**

`P_batt = η·P_wall − P_aux` with η ≈ 0.93 and P_aux = 0.2 kW gives:

| Wall power | Effective efficiency |
|---|---|
| 11 kW | 0.912 |
| 7.5 kW | 0.903 |
| 4.1 kW (6 A, 3φ) | 0.881 |
| 3.7 kW (16 A, 1φ) | 0.876 |
| 1.4 kW (6 A, 1φ) | 0.787 |

- This matches the ADAC wallbox figures for MEB (91–93 %) and the shape of the e-Niro and socket
  data.
- One extra scalar, linear and monotone, so it fits the scheduling note's DP: energy per slot
  stays a function of power.
- An efficiency-by-power table adds a list the user cannot measure without a lab.
- **Position:** keep `charger_efficiency` and add optional `charging_overhead_kw`, default 0.
- For the maintainer's case (11 or 7.5 kW, three-phase) a constant 0.90–0.92 alone is within
  about 1 point. The overhead matters only for single-phase, 6 A or solar trickle.

**(reasoning) What the caller must supply.** All values are wall-side, since prices apply to wall
kWh:
- `car_power_soc_steps`, as measured at the charger;
- `charger_power_session_steps`;
- `charger_efficiency`, wall → battery at full power: about 0.90–0.93 for MEB at 11 kW, room
  temperature, from the ADAC figures. Not the e-Niro's 0.87, and not evcc's generic 0.85;
- optional `charging_overhead_kw` (0.1–0.3 by the ADAC estimate; more in winter, if heating is
  modelled there);
- `battery_capacity_kwh` as the *current* usable capacity: 77 kWh new for an Enyaq 85, less with
  age;
- `car_max_soc` equal to the car's own limit (§4).

The engine converts wall kWh to SoC only through `capacity/efficiency`. The caller can therefore
calibrate the single ratio "wall kWh per 1 % SoC" from logs (§4) instead of the two numbers
separately. New, that is about 77/0.92/100 ≈ 0.84 kWh per %.

**(reasoning) Valuing single-phase hours against three-phase hours.**
- A single-phase hour delivers about one third of the energy (3.7 vs 11 kW).
- It costs 4–8 points of efficiency:
  - the model above gives 0.876 vs 0.912;
  - the e-Niro measured −7.6 points;
  - ADAC's ID.3 socket vs wallbox was −4.6 points.
- So rank such slots by `price / η(P)`, and they need at least three times as many hours.
- A single-phase hour wins only if it is about 5–10 % cheaper and the time is there.
- D16 has no per-slot power limit, so slots limited by load balancing or a single phase cannot be
  expressed today. Under D13 that is the caller's domain; if the engine ever gets a per-slot cap,
  the overhead term values it correctly with no extra code.

**(reasoning) AC taper on MEB and the 11 → 7.5 kW cause.**
- 11 kW into 77 kWh is 0.14 C. A constant-voltage taper at 0.14 C normally starts only above
  ~90 %. The battery note says the same.
- A firm cut at 60–70 % is therefore a **BMS policy**, not electrochemistry at room temperature.
  Ranked by likelihood:
  1. **A car-side current limit on all three phases** (about 16 → 11 A ≈ 7.5 kW at
     3 × 230 V × 10.9 A). Two plausible drivers:
     - a temperature-dependent charge-current limit. In a cold pack the anode-potential margin
       against lithium plating shrinks as SoC rises, so a BMS limit that tightens with SoC in
       the cold is physically expected. This is reasoning; I did not open a source for it here;
     - pacing toward a departure time, which fits the ID.3 "67 %, target 80 %, departure set"
       report.
  2. **A phase drop under voltage sag.** Two phases × 16 A × 235 V = 7.5 kW. But the MEB reports
     say "just under 7 kW", and they are not tied to SoC.
  3. **A charger-side limit**: load balancing against the house's 25 A fuse in the evening, or
     thermal derating.

  The "reduziert" setting (≈5 A on the e-up!/Citigo) is not a candidate. It would cap the whole
  session, not start at 65 %.

**(reasoning) A test the maintainer can run with Home Assistant data.** Record at 10–60 s
resolution across 2–3 full sessions, one of them on a cold night:
- the charger's per-phase current (L1/L2/L3) and per-phase voltage, and its offered current
  (dynamic limit or pilot setpoint);
- total power and session energy;
- the car's SoC and `charging_state`;
- outdoor temperature;
- the main meter's per-phase current, if available.

Then:

| What the log shows | Cause | Where it belongs |
|---|---|---|
| All three phases drop together to ~10–11 A at a repeatable SoC; voltage normal; offered current still 16 A | Car-side limit | `car_power_soc_steps`. If the SoC at which it starts moves with temperature, the caller makes it seasonal (D6) |
| One phase → 0 A, the others stay at 16 A, after that phase's voltage sags; may recover | MEB phase drop | Not a SoC curve. Treat as under-delivery (D8 buffer); check the supply with an electrician or the grid company |
| The offered current falls first, and it tracks house load | Charger load balancing | `charger_power_session_steps` cannot express it. A per-slot cap or caller-side handling (D13) |
| The drop starts at a clock time tied to a departure timer, not at a SoC | Car pacing | Set the car to immediate/`MANUAL` mode and let the planner time the charge |

A cheap extra check: one session with the charger capped at 10 A three-phase. A flat ~6.9 kW to
the car's limit means there is no SoC taper below 10 A, like the e-Niro.

**(reasoning) The 6 A minimum and phase switching on the Enyaq.**
- The possible wall power is 0 or 4.1–11 kW three-phase, or 1.4–3.7 kW single-phase. Modulating
  down to 6 A is the least efficient option (0.88 vs 0.91).
- So a partial slot should be full power for part of the slot, which is also the scheduling
  note's "shorten the most expensive slot, start late" rule.
- Phase switching needs a session restart. Whether that wakes the car is unknown. Keep it in
  solar/load balancing (D13), never inside a price plan.

**(reasoning) Cold (D6).**
- In a Danish winter a cold-soaked pack heats while charging (documented at a station, 23 °C).
  The share of energy that goes to heat is larger at low power and early in a session.
- D6 covers power. **Efficiency needs to vary too.** The caller passes a winter
  `charger_efficiency` or a larger `charging_overhead_kw`, learned per temperature band from its
  own meter-vs-SoC history. No engine change is needed while both are per-call inputs.
- A charge that ends close to departure leaves the pack warm for driving. In a cold week, charging
  in the last available cheap slots is cheaper *and* better for the drive.

### Gaps
- No measured AC power-vs-SoC curve for any MEB car, and no Škoda statement on AC current
  reduction at mid SoC.
- No AC charging efficiency or pack-heater power below 0 °C, for any car.
- The real current value of the MEB "reduziert" setting was not found.
- Whether the Enyaq resumes after a 0 A pause without a new wake-up was not found.

---

## 3. C7: safety levels and defaults from the battery and range side, and what MEB/Škoda guidance says

### Takeaway
VW's MEB guidance, checked at source: **80 % for daily use, 100 % before long trips and drive off
soon after, and park for more than 12 h at 30–80 %**. Škoda's Battery Care mode limits the next
charge to 80 %. On the battery side:

| Setting | Default | Why |
|---|---|---|
| `default_target_soc` | **80 %** | Keep. It is VW's advice, though 80 % still lies on the high-fade plateau |
| `min_idle_soc` | **40 %** | 30–50 % is all below the ageing step; VW's 30 % plus a range margin |
| Opportunistic ceiling (new, O1) | **55 %** | The step |
| `min_safety_soc` | **20 %** | Range and availability, not cell protection |
| `default_arrival_soc` | **20 %** | Not 15. Stale SoC and uncertain winter consumption, not wear: arriving at 15–20 % does the pack no harm |
| `car_max_soc` | The car's own limit | It cannot be read on core Škoda, so the user must configure it |

### Cited Findings
- VW (MEB sister brand), verbatim — [VW Canada, battery tech and maintenance](https://www.vw.ca/en/electric-vehicles/about-electric-vehicles/battery-tech-and-maintenance.html):
  - "For daily usage, Volkswagen recommends setting the charging target at 80%."
  - "Before long trips, Volkswagen recommends setting the charging target at 100% for the highest
    possible range", "driving off as soon as possible after charging is completed".
  - "If the vehicle will be unused for longer than 12 hours, leave it parked with a battery charge
    level of at least 30%", and at most 80 %.
  - "When possible, avoid regular fast charging with direct current (DC)."
- Škoda Battery Care Mode (ME3 software, from February 2022 production, retrofitted in H2 2022):
  - "the battery will only be charged to a maximum of 80 percent when it is next plugged in";
  - "The program also reduces the DC charging speed and maximum charging power to avoid power
    peaks";
  - "If required, the full storage capacity of the battery and the maximum charging speed are
    always available".

  — [theevreport.com, 2022-02-25](https://theevreport.com/skoda-enyaq-iv-enhanced-with-new-software)
  (opened). It resolves the battery note's gap (that note saw Battery Care only in snippets).
- The Škoda Public API's charge limit: "Vehicles typically accept values between 50 and 100 in
  steps of 10". A profile has `minBatteryStateOfCharge` ("If battery drop below this value, then
  start immediate charging"). A 429 can mean the vehicle declined, "because its battery level is
  too low" — `home_assistant_data.md` (Škoda OpenAPI spec).
- Low-SoC storage is benign for calendar ageing: de Hoog et al. even found an initial capacity
  increase in low-SoC storage, and Keil's lowest plateau is the best one —
  `charging_physics_battery.md §5`.
- Users: 77 % want a minimum range, mean 70 km and median 50 km. Novices leave 20–25 % of range
  unused. evcc and Tibber charge a minimum at once, whatever the price —
  `driver_behaviour_ux.md §4`.
- An Enyaq stops at its own limit and resumes when the limit is raised —
  `charging_physics_battery.md §6`.

### Inferences
**(reasoning) `default_target_soc` = 80.**
- Supported by VW's daily advice and by Battery Care.
- 80 % is on Keil's 65–95 % plateau, so it is no "safe" level. It only avoids the further step at
  100 %.
- Lowering it to 70 % buys nothing (same plateau). Lowering it to ≤55 % buys a lot but costs range
  margin. That is why the opportunistic ceiling (55 %) and the target default (80 %) should be two
  separate numbers.

**(reasoning) `min_idle_soc`.**
- Any value from 30 to 50 % is in the low or medium plateau and costs no extra ageing.
- 40 % of 77 kWh is ~31 kWh, leaving ~15 kWh above a 20 % arrival reserve. At an assumed winter
  consumption of 20–25 kWh/100 km (not sourced), that is ~60–75 km, close to Will & Schuller's
  50–70 km minimum range.
- 50 % is acceptable if the user wants more range: still under the step.
- Battery side: do not exceed 55 %.

**(reasoning) `min_safety_soc`.**
- Low SoC does not harm the cells if the car is charged soon after; the BMS guards the true
  bottom.
- The level is about range and about the car still accepting commands (the Škoda 429 "battery
  level is too low").
- 20 % mirrors VW's "at least 30 %" for parking with a margin, and keeps an emergency drive
  possible in winter.
- It charges at any price, but rarely, so the cost is small.

**(reasoning) `default_arrival_soc` 15 vs 20.**
- Electrochemically indifferent: the car arrives, then charges.
- The arguments for 20 are errors elsewhere:
  - trip energy is predicted from distance and temperature by the caller (D3, D6), with winter
    error unquantified;
  - the SoC the plan starts from may be stale (§4).
- Choose **20 %**, easy to lower, as the driver note proposes. In a Nordic winter, 15 % leaves
  too little room for those errors.

**(reasoning) 100 % before trips.** VW wants 100 % reached just before leaving. In the engine
this needs:
- the trip target's own `max_charge_soc` = 100 (D7);
- the D8 buffer kept short (20 min);
- the energy above ~80–90 % placed last.

The late tie-break does this only when prices tie. A SoC-dependent holding cost does it always
(§7).

**(reasoning) `car_max_soc`.** It is the car's own limit, which the user changes in the car or
the app, and which Battery Care sets to 80 for one session. It is a live hard ceiling, not a
preference.
- On core Škoda (2026.11) it cannot be read or set (§4).
- The integration must take it as configuration, and warn when the plan stalls below a planned
  SoC with `charging_state = conserving` (car at its limit).

### Gaps
- Škoda's own owner's manual text (Enyaq) on daily limit, trips and low SoC was not opened. VW
  Canada's MEB guidance stands in.
- A VW UK figure of a "lower loading limit of 20 % in summer / 40 % in winter" appeared only in a
  search summary. The VW UK page I opened did not contain it.
- No source quantifies Enyaq standby drain or the size of its bottom buffer below displayed 0 %.

---

## 4. The Škoda data reality: SoC estimation from charger energy, and what staleness means for safety

### Takeaway
Under core Škoda in 2026.11 the car cannot be woken, its limit cannot be set, and the SoC carries
no capture time. The physical consequences are mild and manageable:
- **Between car readings, SoC can be projected from charger energy** with one calibrated number,
  wall kWh per 1 % SoC (≈0.84 for a new Enyaq 85). The error is about ±2–3 SoC points over a
  night's charge.
- **Charging on a stale or unknown SoC is safe for the battery.** The BMS and the car's own limit
  bound it. It only risks wear (sitting at the car's limit) or a shortfall (a too-high pre-drive
  reading).
- **O7: charge first**, but only a bounded amount, and stop on projected SoC. Refresh within the
  20/h quota.

### Cited Findings
- Core Škoda (HA 2026.11):
  - read-only; polls every 5 min; 20 requests/h per VIN;
  - no wake-up, no refresh endpoint and no charge-limit control;
  - `carCapturedTimestamp` is not exposed for SoC;
  - sensors include `battery_percentage`, `charging_power`, `charging_state` (incl.
    `conserving`) and `remaining_time_to_full_battery`.

  The old MySkoda wake button warned of "a strict limit on the number of wake-ups … to protect
  the 12V battery" — `home_assistant_data.md` (HA next docs, core sensor.py, Škoda OpenAPI,
  MySkoda entities.md).
- That note's proposed projection is `soc + kWh × efficiency / capacity`, owned by the caller. It
  reads O7 as "charge first: … Staleness should lower confidence, not block action" —
  `home_assistant_data.md`.
- Car-side energy counters do not see charging losses. Calibrate efficiency against the
  charger's meter, not the car's "charged energy" — `charging_physics_battery.md §6` (motor1.com
  on ADAC; search summary only, as that note says).
- Usable capacity of a new Enyaq 85: 77.0 kWh — [EV Database](https://ev-database.org/car/3570/Skoda-Enyaq-85).
  Fleet fade for AC-charged cars is about 1.5 %/yr —
  [Geotab via Yahoo Finance](https://finance.yahoo.com/news/geotab-data-points-modest-rise-141059571.html).
- When SoC is unknown at plug-in, evcc assumes the vehicle is empty —
  `prior_art_software.md` (evcc limits.mdx).

### Inferences
**(reasoning) Physics of the projection.**
- ΔSoC = E_wall × η_eff / C_usable.
- The two uncertain numbers enter only as the ratio k = C_usable / η_eff (wall kWh per 100 %).
  The caller can learn k directly: k = ΔE_wall / ΔSoC over sessions where the car reported SoC
  near both ends. Prefer long sessions and readings taken while the charge is running.
- The learned k folds in efficiency, aux load, age (SoH) and season. Keep one k per temperature
  band.

**(reasoning) Error size.**
- Efficiency uncertainty of ±3 % on a 30 kWh night is ±0.9 kWh, about ±1.2 points.
- Using the new-car 77 kWh when the pack has faded to ~94 % (≈4 years at 1.5 %/yr) makes the
  projection 6 % short of the true ΔSoC. On a 40-point charge that is about 2.5 points of
  under-estimate.
- The under-estimate errs toward overshoot, which is safe for range. A learned k removes it.
- The car's SoC is relative to its current capacity. That is reasoning on BMS practice, not
  sourced.

**(reasoning) What staleness really means.**
- Parked drain is small (not quantified in any source), so a reading taken *after* the last drive
  stays near true for days.
- The dangerous case is a reading from *before* a drive, which the cloud has not replaced. It is
  too high by the trip's consumption.
- Practical freshness rule for the caller: a SoC is trusted once HA has seen it change after the
  last unplug→plug-in. Until then, plan on it but flag it, and let only `min_safety_soc` act on
  it.

**(reasoning) Safety.**
- The BMS stops charging at the car's own limit and protects the cells. Charging blind cannot
  harm the pack.
- It can cost wear: leaving an unknown car at a 100 % limit for days. So:
  - charge first when the last known SoC < `min_safety_soc`;
  - stop on projected SoC at `min_safety_soc` + a few points;
  - re-plan when a fresh reading arrives.
- Never depend on waking the car: there is no endpoint, and waking draws on the 12 V battery.
- Do not spend the 20/h quota on refreshes that cannot reach the car.

**(reasoning) The car limit cannot be set.**
- To end a charge below the car's own limit, the caller must stop through the charger at the
  projected SoC.
- `charging_state = conserving` tells the caller the car's own limit was reached first. If that
  happens below the planned SoC, the configured `car_max_soc` is wrong: report it, and plan with
  the lower value.

### Gaps
- Measured staleness of the Enyaq's SoC through the Škoda cloud, parked and asleep: none found.
  The maintainer can log it after 2026.11.
- Whether core Škoda's `charging_power` is battery-side or wall-side was not documented. If it is
  battery-side, it gives a direct efficiency measurement against the charger.

---

## 5. Which numbers in the physics note come from one car or one test, and how far do they transfer to the Enyaq?

### Takeaway
Most hard numbers in the physics note come from a 2020 Kia e-Niro on one dynamometer, or from
forum anecdotes. **Their shape transfers, not their level.** For the Enyaq, use the MEB-specific
ADAC figures (ID.3 2022, ID.7 2026), the Škoda/VW documents, and the maintainer's own logs.

### Cited Findings
All entries are from `charging_physics_battery.md`, sections as given:

| Number | Origin | Transfer to the Enyaq (reasoning) |
|---|---|---|
| 87.2 / 87.0 / 80.3 / 79.6 % efficiency (3φ16, 3φ10, 1φ16, 1φ10) | Kia e-Niro MY2020, one dyno study, 21–23 °C (Reick 2021) §2 | Shape yes (flat at 3φ, 1φ penalty). Level no: ADAC measured ≤9 % loss for the ID.3 at 11 kW and <7 % for the ID.7 (MEB) → use 0.90–0.93 |
| Flat 6.9 kW over the last ~6 % to 100 % | Same e-Niro, 10 A, one run §1 | Shows that a low-C AC taper *can* be absent. Says nothing about MEB |
| 7.3 kW on 2 phases | VW e-up!, not MEB §1 | Not the Enyaq 80/85 (11 kW, 3φ); relevant to the Enyaq iV 50 class (7.2 kW on-board charger, [evspecs](https://www.evspecs.org/technical-data/skoda/enyaq-iv/ac-charging)) |
| 78 / 81 / 84 % at 6 / 10 / 16 A; "<60 %" at 6 A 1φ | e-Niro + go-e, forum, disputed instruments §2 | Direction only |
| 100–300 W auxiliary load | ADAC estimate across cars §2, §7 | Plausible for MEB; not measured |
| Reduction from 67 % to 3.7 kW | One ID.3 owner, departure time set §1 | Weak; possibly pacing |
| Phase drop to "just under 7 kW" | MEB owners, software 3.2–3.8.1 and 5.0 §1 | Relevant platform, anecdotal |
| 39 % / 93 % at −25 / +25 °C | DC off-board chargers (JRC) §4 | Mechanism only; not AC, not the car |
| Ageing plateaus; step ~60 % | 18650 lab cells, 25–50 °C, 9–10 months (Keil) §5 | The mechanism (anode lithiation) is general to graphite cells. The step's position depends on cell balancing → unknown for MEB cells and in displayed SoC |
| 0.7 %/yr "just in time" benefit | The note's own arithmetic at 25 °C §5 | An upper bound; lower at Nordic temperatures (§1 here) |
| ~1.5 %/yr fade, AC-charged | Geotab fleet, 21 models §5 | The best real-world anchor; not Enyaq-specific |

### Inferences
- **(reasoning)** The engine design should not hard-code any of these (D4 already says so). The
  integration's defaults for an Enyaq should come from ADAC's MEB figures, VW/Škoda guidance and,
  after two weeks of logging, the maintainer's own k and taper.

### Gaps
- No Enyaq- or MEB-specific measurement exists in any note of: an AC curve, AC efficiency against
  current or temperature, standby drain, or heater power.

---

## 6. Where the notes contradict each other on facts, checked at the source

### Takeaway
I found nine factual tensions. The ones that change decisions are 1, 2, 3, 5 and 7:
1. Efficiency level: 87 % (e-Niro), 85 % (evcc) or ≥91–93 % (MEB, ADAC).
2. Where the ageing step lies: 60 % (Keil) or "small below 80 %" (KIT).
3. The taper the scheduling experiment assumed: 80/90 % break points against the maintainer's
   65 %.
5. Negative prices as an argument for O1: spot-only against the consumer total.
7. The O1 simulations' omission of wear.

### Cited Findings and checks
1. **Efficiency.**
   - The physics note anchors its break-even on the e-Niro's 87 %.
   - The prior-art and scheduling notes cite evcc's 0.85 (estimator.go).
   - ADAC's MEB measurements are 91 % for the ID.3 2022 and >93 % for the ID.7 2026 — all in
     `charging_physics_battery.md §2`; `prior_art_software.md`.
   - Not a contradiction of measurements: different cars and different assumptions. **For the
     Enyaq use 0.90–0.93.**
2. **Ageing threshold.**
   - The physics note's takeaway uses Keil's step at "about 60 % SoC".
   - Its own KIT source says "the influence is small below 80%" for graphite/NCA pouch cells —
     both `charging_physics_battery.md §5`.
   - The two disagree on where the expensive region begins: different cells and anode balancing.
   - Consequence: the 55 % ceiling is a *precautionary* value. If MEB cells behave like KIT's,
     the ceiling could rise to ~70–75 %. Unknown.
3. **Taper used in the experiments.**
   - motor.md's example is 11 → 7.5 kW from 65 %.
   - The scheduling note's real-week experiment (Exp 3) used 11 kW up to 80 %, 7 kW up to 90 %,
     3.5 kW above (`scheduling_algorithm.md §2`).
   - The measured greedy gaps (median 0.01 %, max 5.4 %) are therefore for a later and milder
     knee than the maintainer's. Not re-measured.
4. **7.5 kW and phase drop.**
   - The physics note says 7.5 kW "matches two phases × 16 A × 230 V almost exactly"
     (`charging_physics_battery.md §1`). Its own arithmetic gives 7.36 kW at 230 V, and 7.5 kW
     needs 235 V.
   - The MEB phase-drop reports it cites say "just under 7 kW".
   - The fit is weaker than claimed. Three-phase ~11 A fits equally well.
5. **Negative prices and O1.**
   - The scheduling note: 6.3 % of DK1 spot hours negative (Jan–Sep 2025), so floors-only loses
     value (`scheduling_algorithm.md §7`).
   - The price note: the household total was negative in only 2 quarter-hours in 13 months in
     DK1, and never in DK2 (`price_composition_denmark.md §4`).
   - The second governs a Danish household, so the scheduling note's O1 argument is much weaker
     in Denmark than its spot-only figures suggest. Both notes say so in their own caveats.
6. **Battery Care.**
   - The physics note saw it only in snippets (`charging_physics_battery.md §6`).
   - Checked: it limits the *next* charge to 80 % and lowers DC power
     ([theevreport](https://theevreport.com/skoda-enyaq-iv-enhanced-with-new-software)).
   - The HA note's API limit (50–100 in steps of 10) is a different mechanism, the persistent car
     limit (`home_assistant_data.md`).
   - Both exist. The integration cannot see either on core Škoda.
7. **O1 savings vs wear.**
   - The forecast note's "91–97 % of perfect-foresight savings" assumes the car stores up to 3–5
     days of energy, with no wear term (`price_forecast_uncertainty.md §7.6`).
   - The driver note's "fill in cheap hours" also has no wear term.
   - Their savings are gross. §1 here nets them.
8. **"Danish users … fill".**
   - The driver note reads Ziras et al. as users who "delay to ~01:00 and fill up"
     (`driver_behaviour_ux.md §2, §7`).
   - The quoted source text is "early enough to guarantee full charging". That means completing
     the session to the car's own limit, which the dataset does not record.
   - It is not evidence that drivers want 80 % (or 100 %) rather than their need. I did not
     re-open the DTU PDF.
9. **Publication time of day-ahead prices.**
   - 12:45 CET (`price_composition_denmark.md §3`, Nord Pool support) against "13:00 CET"
     (`price_forecast_uncertainty.md §1`, Lund thesis).
   - Not my discipline and immaterial to battery questions. Both notes agree prices are in the
     API by 13:00–14:00.

### Inferences
- **(reasoning)** None of these contradicts a measurement. They are different cars, different
  cells and different price bases. Each changes a default or a framing, not the engine's
  structure.

### Gaps
- Keil's PDF (bot wall) and the DTU PDF were not re-opened by me. Checks 2 and 8 rely on the
  quotes in the notes.

---

## 7. Positions, and the summary table

### Takeaway
- The engine's structure stands: two step curves, min() of them, × efficiency, simulated.
- From the battery side, add three small things:
  1. an optional `charging_overhead_kw`;
  2. an optional SoC-dependent holding cost per hour, or at least an opportunistic ceiling for
     O1;
  3. a late tie-break.
- The caller carries the learned k (wall kWh per % SoC), the seasonal efficiency, the car's own
  limit, and the stale-SoC rules.

### Cited Findings
- No new sources here. The summary rests on §1–§6.

### Inferences
**(reasoning) The holding-cost idea.**
- `soc_holding_cost_steps = [(soc, cost_per_hour), ...]`, in price units, default none (D4).
- It lets the exact DP proposed in `scheduling_algorithm.md §7` trade wear against price
  natively:
  - charging late among ties;
  - placing 80–100 % last before a trip;
  - holding above the step only when the price gain beats the wear.
- A Danish integration default from §1: 0 below 55 %, ≈0.2 DKK/h from 55 to 90 %, and about
  double that above 90 %. Central estimates, to be refined.
- Without it, the opportunistic ceiling and the late tie-break are the simple approximation.

#### Summary table

| ID / question | Recommendation | Confidence | Evidence that would change it |
|---|---|---|---|
| **O1 / C1**, charge beyond floors | Next-cheaper-day rule (forecast note), capped at an **opportunistic ceiling of 55 %**. Above it only for targets (own caps, D7). At a consumer total ≤ 0, fill to the ceiling | Medium | MEB cells with no step below ~75 % (KIT-like) → ceiling 70–75 %. A year of DK data showing multi-day gains well above ~0.3 DKK/kWh per day held. A per-% SoH price study putting V1 below ~1,000 DKK |
| Value of wear | V1 ≈ 1,000–3,700 DKK per point (central 2,000). Parking above the step ≈0.5–1.5 pt/yr ≈ 5.5 DKK/day central. Break-even Δp ≈ 0.3 DKK/kWh per day held | Low–medium | A Danish SoH/resale regression; a current Škoda pack price; MEB calendar-ageing data at 0–15 °C |
| Late tie-break among equal costs | Adopt, with a small ε. Prefer a holding cost in scoring when the DP comes | High | Data showing that late finishes cause missed targets despite D8 |
| Winter warm battery vs late charging | No conflict: late is cheaper (night tariff) and leaves a warmer pack. Do not follow "charge on arrival" | Medium | AC efficiency data showing a large cold-start loss |
| D8 buffer / readiness | Keep 20 min. The caller may raise it in winter or for slow cloud chargers, and must verify that windows start | Medium | Logged start latency and overrun on the maintainer's charger |
| **C6** efficiency model (D16, D26) | Constant `charger_efficiency` (Enyaq 0.90–0.93) + optional `charging_overhead_kw` (0.1–0.3, default 0). Power curves and costs are wall-side | High for the structure; medium for the values | An MEB measurement showing a strongly non-linear efficiency at 3φ 6–16 A |
| Single-phase vs three-phase slots | Rank by price / η(P). A 1φ hour needs ~5–10 % lower price and 3× the hours. Phase switching stays outside the engine (D13) | Medium | MEB 1φ efficiency measurements |
| AC taper / 11 → 7.5 kW | Do not hard-code. Diagnose from per-phase current and voltage logs. Leading hypothesis: a car-side 3-phase current cut (possibly temperature-linked) | Low (cause) / high (test) | The maintainer's logs (table in §2) |
| 6 A minimum, partial slots | Full power for part of a slot; never trickle at 6 A in a price plan | High | — |
| D6 cold | The caller passes seasonal efficiency / overhead (learned k per temperature band) | Medium | Enyaq AC winter measurements |
| `default_target_soc` | 80 % (VW daily advice; Battery Care) | High | Škoda manual saying otherwise |
| `min_idle_soc` | 40 % (30–50 acceptable; never above 55) | Medium | Override data showing 40 % too low for unplanned trips |
| `min_safety_soc` | 20 % | Medium | Enyaq refusing remote commands at a higher SoC; standby-drain data |
| Arrival SoC (O2 default) | 20 % rather than 15, easy to lower | Medium | Logged trip-energy prediction error in winter being small (<10 %) |
| `car_max_soc` (D18) | = the car's own limit; configured by the user on core Škoda; detect `conserving` below the planned SoC | High | Core Škoda exposing the limit as a sensor |
| 100 % before trips | Trip target cap 100; energy above ~80–90 % last; short buffer | High (guidance) / medium (mechanism) | — |
| SoC estimation (caller) | Project from charger kWh using a learned k = wall kWh per % (≈0.84 new) | High | — |
| **O7** stale SoC below safety | Charge first, bounded: to `min_safety_soc` + a few points by projected SoC, then re-plan. Never wake. Respect the 20/h quota | High | A Škoda API wake-up endpoint |
| Battery Care / car limit visibility | Document: the integration cannot see Battery Care or the limit; the user must not set Battery Care when a 100 % trip is planned | Medium | Core Škoda adding control or diagnostic entities |

### Gaps
- Every Enyaq-specific value (taper, k, winter overhead, staleness) awaits the maintainer's own
  logs. The integration should log them from day one.
