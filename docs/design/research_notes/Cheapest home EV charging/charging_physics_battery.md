# Physics of home AC charging: energy per hour, losses, and battery wear

Researched 2026-10-28 for the ChargeSmarter planning engine (`docs/design/motor.md`,
`decisions.md`). Every factual claim links to a page or PDF opened during this task. Lines marked
**(reasoning)** are engineering judgement drawn from the cited facts, not facts in themselves.
Search-result snippets that could not be opened are listed only under Gaps.

## 1. AC charging curves: does home AC charging taper with SoC, and what explains 11 → 7.5 kW at 60–70 %?

### Takeaway
At 11 kW the C-rate is low, so AC charging usually holds near-constant power until close to full.
One measured case: a Kia e-Niro charged the last ~6 % to 100 % at a flat 6.9 kW. For the VW MEB
platform (ID.3/ID.4/ID.5/Enyaq) there are owner reports of both an SoC-linked reduction starting
around 67 % and the car dropping a phase (to ~7 kW) when the supply voltage sags. The maintainer's
7.5 kW matches two phases × 16 A × 230 V almost exactly. **Logging per-phase currents** is the
only way to tell whether his drop belongs in the car's SoC curve or is something else.

### Cited Findings
- On a dynamometer test, the Kia e-Niro (MY2020, 11 kW three-phase on-board charger) was recharged to 100 % after a WLTC with the wallbox set to 10 A on three phases. "The constant slope of the curve shows that the charging power was almost constant at 6.9 kW during the charging process". 4.52 kWh was charged, and the WLTC used 3.93 kWh of battery energy, so the measured segment was the top few percent of SoC. — [Reick et al., *Vehicles* 2021, 3, 736–748 (PDF)](https://arbor.bfh.ch/bitstreams/67fb6c67-ed54-4535-a0fb-f43b55a2a3f5/download)
- Same paper: the VW e-up! tested alongside has a maximum AC charge power of 7.3 kW on 2 phases, against 11 kW on 3 phases for the Kia. Some VW-group cars therefore charge on two phases by design. — [Reick et al. 2021 (PDF)](https://arbor.bfh.ch/bitstreams/67fb6c67-ed54-4535-a0fb-f43b55a2a3f5/download)
- An ID.3 Pro S owner (software 5.0, 08/2024) on an 11 kW wallbox reported that after about 3 hours the car charged at only 3.7 kW. Asked whether it was near 100 %, he answered: "er hat bei 67% angefangen zu reduzieren (Ziel: 80 %)". The reduction began at 67 % with a target of 80 %. Another ID.3 owner (ME3.8) reported 3–4 kW while stuck at 70 % with a target of 80 % and a departure time set. These are single anecdotal reports. — [GoingElectric forum, ID.3 thread, Dec 2024](https://www.goingelectric.de/forum/viewtopic.php?p=2293640)
  - Both reports involve a departure time and an 80 % target. **(reasoning)** That pattern would also fit the car pacing its charge to finish at the set departure time rather than a pure electrochemical taper. Not verified.
- MEB owners (ID.3, ID.4, ID.5, Cupra Born; software 3.2 to 3.8.1, one report on 5.0) describe home AC charging that starts at 10–11 kW and then drops one phase, falling to "just under 7 kW". It sometimes returns to 10 kW later in the session. Posters attribute it to the car reacting to voltage drop on a phase ("about 7 % drop at 15.4 A"). One owner found it only above ~10 A, with a 6 A three-phase charge (~4.2 kW) staying on all phases. No fix was confirmed. SoC is not mentioned as a factor. — [meinid.com, "Reduzierte AC-Ladeleistung seit 3.7 Software", p. 4](https://www.meinid.com/thread/8031-reduzierte-ac-ladeleistung-seit-3-7-software/?pageNo=4)
- An Enyaq iV 80 owner reports that the car stopped at its own 80 % limit, and charging resumed when he raised the limit to 90 %. No AC taper over SoC is described in that thread. — [GoingElectric, Enyaq iV 80 thread](https://www.goingelectric.de/forum/viewtopic.php?p=1583688)
- A supplier article (Landworld Technology, published on the Busworld platform, 2026-02-25; marketing-grade, no data) states in general terms: "As the battery approaches high SOC, charging current is reduced to protect cell durability"; on-board chargers may "reduce output power to protect components" at thermal thresholds; "constant 11 kW charging is uncommon across the entire session"; single-phase homes get lower power "regardless of vehicle capability". It gives no SoC threshold. — [one.busworld.org](https://one.busworld.org/news/what-11-kw-ac-onboard-charging-really-delivers-in-practice)
- In the ADAC's 2022 test, losses were measured at an 11 kW wallbox for the ID.3 among others (see section 2). The article reports energy, not the power curve. — [autohaus.de on ADAC test, 2022-09-15](https://www.autohaus.de/nachrichten/autohandel/adac-test-stromverluste-durch-schnellladen-vermeiden-3231295)

### Inferences
- **(reasoning)** Arithmetic: 2 phases × 16 A × 230 V = 7.36 kW, and at 235 V = 7.52 kW. Three phases at ~11 A gives the same figure (3 × 230 V × 10.9 A ≈ 7.5 kW). The maintainer's "7.5 kW" therefore fits three possible mechanisms:
  1. The car drops a phase (the MEB voltage-sag behaviour above). This is not a function of SoC, and it may come and go.
  2. A car-side current reduction from about 16 A to about 11 A per phase, linked to SoC. This is the ID.3 "reduces from 67 %" report.
  3. A charger-side limit: load balancing against the house's main fuse, thermal derating of the charger, or a schedule in the charger app.
- **(reasoning)** Diagnostic for the integration, cheap to do: record the charger's per-phase current and voltage entities across a session. If the drop shows on all three phases at ~11 A and recurs at the same SoC, it belongs in `car_power_soc_steps` (D16). If one phase goes to 0 A while the others stay at 16 A, it is a phase drop: neither curve models it properly, and it shows up as random under-delivery. If the charger reports its own lower limit, it belongs in `charger_power_session_steps` or in load balancing (D13).
- **(reasoning)** Physics: 11 kW into a 60–80 kWh pack is about 0.14–0.18 C. Constant-current/constant-voltage tapering at such low C-rates normally starts only near full. A firm reduction at 60–70 % is unusual electrochemically. It is more likely a manufacturer policy (thermal, scheduling, or "gentle" charging) or a supply effect than CV-phase physics. The engine's step curve can represent any of these, as long as it is learned from the user's own data rather than assumed.
- **(reasoning)** If the engine takes the taper as `[(0, 11), (65, 7.5)]` but the true cause is an intermittent phase drop, plans will overestimate delivery early in a session and underestimate it late. The completion buffer (D8) absorbs some of this error.

### Gaps
- No manufacturer document or measured AC power-vs-SoC curve for the Enyaq or any MEB car was found. Skoda's owner manual text on AC charging and the "reduced AC current" setting was not found. EV-database and Bjørn Nyland AC curves were not found in the searches made.
- Whether MEB cars pace AC charging to a departure time (reducing current deliberately) could not be confirmed from any source.

## 2. Charging efficiency (wall to battery): is it constant, and does a slow cheap charge cost more than a fast one?

### Takeaway
Efficiency is **not** constant. It falls at low power, mainly because a roughly fixed auxiliary
load (control units, 12 V, pumps; ADAC estimates 100–300 W) and on-board-charger losses weigh
more when less power flows. Three-phase 10–16 A is close to flat (~87 %). Single-phase or
socket charging is 7–15 points worse. At 6 A the loss grows sharply. A slow single-phase charge
in cheap hours can therefore cost more than a fast three-phase one, unless prices differ by
roughly 10 % or more.

### Cited Findings
- Kia e-Niro, measured wall to battery (room temperature 21–23 °C):
  - 3-phase 16 A: **87.21 %**; 3-phase 10 A: **86.98 %**; 1-phase 16 A: **80.32 %**; 1-phase 10 A: **79.58 %**.
  - "The influence of the current intensity in three-phase charging is minimal". Single-phase on a three-phase charger costs 7.63 points.
  - Overall charging losses across the two cars tested ranged from 12.79 to 20.42 %, and efficiency was "in the range of 83 to 88 %".
  - Over 100,000 km, single-phase charging cost about €800 more at €0.30/kWh.

  — [Reick et al. 2021 (PDF)](https://arbor.bfh.ch/bitstreams/67fb6c67-ed54-4535-a0fb-f43b55a2a3f5/download)
- Reick et al., citing Apostolaki-Iosifidou et al. (2017): one-way losses in the battery are 1.15–7.87 % and in the vehicle's charger 0.88–16.53 %, "in dependency of current and SOC. In general, losses decrease with increasing current." — [Reick et al. 2021 (PDF)](https://arbor.bfh.ch/bitstreams/67fb6c67-ed54-4535-a0fb-f43b55a2a3f5/download)
- Apostolaki-Iosifidou, Codani & Kempton, *Energy* 127 (2017): one-way losses measured at 12–36 %. Most losses are in the AC-DC power electronics. Efficiency is lowest "at low power transfer" and at low SoC. Building-side losses are under 3 %. — [IDEAS/RePEc abstract](https://ideas.repec.org/a/eee/energy/v127y2017icp730-742.html)
- ADAC 2022 test (Zoe, Model 3, ID.3, 500e):
  - Losses at a household socket against an 11 kW wallbox: **VW ID.3 13.6 % vs 9 %**; Zoe ~24 % vs 9.7 %; Model 3 15.2 % vs 7.7 %; 500e 12.7 % vs 6.3 %.
  - Causes named: the on-board charger's AC-DC conversion, about 5–10 % lost as heat; control units on the 12 V network during charging, an estimated **100–300 W**; long supply cables.
  - The ADAC recommends 11 or 22 kW wallboxes, and in winter charging right after driving while the battery is warm.

  — [autohaus.de, 2022-09-15](https://www.autohaus.de/nachrichten/autohandel/adac-test-stromverluste-durch-schnellladen-vermeiden-3231295)
- ADAC test published 2026-08-15 (Mercedes CLA 350, **VW ID.7 Tourer (MEB)**, Volvo EX30, Renault 5, Tesla Model Y):
  - Household socket (2.3 kW): 24.2 % for the CLA; 12.7–15.3 % for the other four.
  - **Wallbox 11/22 kW: under 7 % for all five.**
  - Wallbox at reduced power: Renault 5 8 % (5.1 % at full power); the others 9.1–12.8 %.
  - Causes named: on-board systems active during charging, and AC-DC conversion.

  — [firmenauto.de on ADAC test, 2026-08-15](https://www.firmenauto.de/management/fuhrparkmanagement/e-auto-ladeverluste-adac-vergleich-steckdose-wallbox-fuenf-elektroautos/)
- Anecdotal (Kia e-Niro, go-e charger, preliminary, instrument accuracy disputed in thread): efficiency on 3 phases about 78 % at 6 A, 81 % at 10 A and 84 % at 16 A; on 1 phase "below 60 %" at 6 A, ~78 % at 10 A and ~86 % at 16 A. — [GoingElectric forum](https://www.goingelectric.de/forum/viewtopic.php?p=1264219)

### Inferences
- **(reasoning)** A physically motivated model that fits these data: `P_battery = η_conv × P_wall − P_aux`, with `η_conv` ≈ 0.90–0.95 and `P_aux` ≈ 0.1–0.3 kW while the car is awake and charging. The 0.1–0.3 kW comes from the ADAC estimate. With 300 W of auxiliary load, the share lost to it is:
  - 2.7 % at 11 kW;
  - 7.3 % at 4.1 kW (6 A three-phase);
  - 21 % at 1.4 kW (6 A single-phase).

  This reproduces the shape of every measurement above: flat at three-phase 10–16 A, poor at a socket, very poor at 6 A single-phase.
- **(reasoning)** Break-even, using the e-Niro numbers. 10 kWh into the battery takes 11.47 kWh from the wall at 3φ/16 A, and 12.57 kWh at 1φ/10 A, which is 9.6 % more. A plan that spreads the same energy over more hours at low power is cheaper only if those hours are more than about 10 % cheaper. Between 3φ/10 A and 3φ/16 A the penalty is about 0.3 %, which is negligible.
- **(reasoning)** For the engine: a constant `charger_efficiency` is adequate **as long as the charger only ever runs near its full three-phase power**, which is the normal case for a scheduled home charge. It understates cost and time whenever the curves force low power: single-phase installations, load-balanced 6 A, solar trickle. It also misses the time-proportional auxiliary load. Two options, in order of preference:
  1. Add an optional `charging_overhead_kw`, the auxiliary draw while charging, subtracted each step. It is one number, it keeps the model linear, and it captures why slow is dear.
  2. Make efficiency a step function of wall power `[(kw, eff), ...]`.
- **(reasoning)** Where efficiency is applied matters for cost. Prices apply to wall energy, while SoC moves with battery energy. The engine should state that `expected_kwh` and `expected_cost` are wall-side. It should also state whether `car_power_soc_steps` is wall-side (what the charger meter shows) or battery-side (what some cars report). The maintainer's 11 → 7.5 kW was presumably read at the charger, which is wall-side.

### Gaps
- No measurement of AC charging efficiency against temperature (cold battery, cold on-board charger) was found. The JRC temperature study covers only DC (see section 4).
- No Enyaq- or MEB-specific efficiency curve against current. The ID.7 figure (<7 % at a wallbox) is the closest MEB data point.
- The full text of Apostolaki-Iosifidou et al. was not accessible (abstract only).

## 3. Minimum current, 1-phase/3-phase switching, and what they mean for `min_session_kwh` and partial-hour charging

### Takeaway
An IEC 61851 AC charger cannot signal less than 6 A. The lowest non-zero power is therefore
about 1.4 kW single-phase or 4.1 kW three-phase. Changing the number of phases on MEB cars
means stopping and restarting the session. Because efficiency falls at low power, a partial
hour should be charged **at full power for part of the hour**, not at low current for all of it.

### Cited Findings
- "the minimum charging current for electric vehicles is 6 A, which means that the power of the PV-system should be at least 4.1 kW" (three-phase). — [Reick et al. 2021 (PDF)](https://arbor.bfh.ch/bitstreams/67fb6c67-ed54-4535-a0fb-f43b55a2a3f5/download)
- A charger control-pilot implementation (JosEV) maps a requested current of 6–80 A to a PWM duty cycle for basic charging. 0 A gives a 100 % duty cycle (no charging allowed), and 5 % signals digital communication. This is an API spec, not the IEC text itself. — [JosEV API, CP PWM](https://josev-api.ecog.io/v2.1.0/external_messages/cp_pwm)
- On a Skoda Enyaq iV 80, changing between 1- and 3-phase requires stopping and restarting the charging session. The poster considers this unsuitable for following changing solar output. The same thread reports a possible MEB software issue with the car not waking for charging, which others dispute. — [GoingElectric, Enyaq iV 80 thread](https://www.goingelectric.de/forum/viewtopic.php?p=1583688)
- An MEB owner's 6 A three-phase home charge averaged ~4.2 kW. — [meinid.com](https://www.meinid.com/thread/8031-reduzierte-ac-ladeleistung-seit-3-7-software/?pageNo=4)

### Inferences
- **(reasoning)** For the charger curve (D16): an Enyaq on a three-phase charger can deliver 0 kW or 4.1–11 kW at the wall, never 0.1–4.1 kW. A valid plan therefore cannot rely on a fractional-power step below 4.1 kW. The engine's model of full curve power for a whole step, or no charging, is consistent with this. Partial hours are expressed as fewer steps at full power, which is also the most efficient choice (section 2).
- **(reasoning)** `min_session_kwh` (D19): 2 kWh at 11 kW is ~11 minutes, or two 6-minute steps. The physical costs of a session start are:
  - waking the car (MEB wake-up problems are reported);
  - the charger's soft start, already in `charger_power_session_steps`;
  - the auxiliary load from wake until contactors close, plus the BMS and cooling run-on afterwards.

  None is quantified in any source found. A soft energy minimum is reasonable. A small extra fixed energy cost per session start, for example 0.1–0.3 kWh, would let the cost scoring decide instead of a threshold. Its value is unverified; it is a tunable, not a fact.
- **(reasoning)** Phase switching is a solar or load-balancing concern, which is outside the engine (D13). If the integration ever switches to 1-phase for low power, it must hand the engine the 1-phase curve. The efficiency penalty there is large (section 2).

### Gaps
- The IEC 61851-1 text itself could not be accessed. The 6 A minimum is cited from a peer-reviewed paper and an implementation spec instead.
- No measured energy cost of a session start (wake, contactors, BMS run-on) was found.
- Whether the Enyaq accepts the charger pausing at 0 A and resuming without a new wake-up was not found.

## 4. Cold weather: battery heating during AC charging, preconditioning, Danish winter

### Takeaway
Sources confirm that cold reduces charging efficiency and power, and that the Enyaq heats its
battery while charging (to ~23 °C at a station). No source quantifies **AC** charging losses in the
cold. The DC evidence is severe: 39 % efficiency at −25 °C against 93 % at +25 °C. Folding
temperature into the curves (D6) is still sound, but the efficiency also needs to vary with
temperature, which the current inputs cannot express.

### Cited Findings
- JRC (Trentadue et al., *Energies* 2018, 11, 1937) tested seven DC fast chargers (≤50 kW) and two EVs at −25, −15, +25 and +40 °C. The metric is the charger's power conversion efficiency, DC out over AC in, per SAE J2894/1. The paper reports "lower energy efficiencies at extreme temperatures, due to lower requested and, thus, delivered power levels". "The lowest and highest power conversion efficiencies of 39% and 93% were observed at −25 °C and ambient temperature (+25 °C), respectively." This is DC, and it measures the off-board charger, not the car. Its mechanism is the same as in section 2: a cold battery requests less power, and power electronics are inefficient at low load. — [Trentadue et al. 2018, JRC PDF](https://ses.jrc.ec.europa.eu/sites/default/files/publications/evaluation_of_fast_charging.pdf)
- A Škoda representative (Stepan Rehak, Twitter thread, Enyaq iV):
  - Early software heated the battery to about 10 °C for driving, which raised winter consumption. From summer 2021 production and the ME3 update, it heats only to "just above 0 degrees".
  - While charging at a station, "The charging station is heating the battery (to 23 degrees) and charging at the same time", and "the charging speed is bit lower".
  - The advice is "Always set your departure time".
  - The thread does not separate AC from DC.

  — [threadreaderapp, Rehak thread](https://threadreaderapp.com/thread/1615643925703786496.html)
- ADAC: in winter, charge right after driving while the battery is still warm. — [autohaus.de](https://www.autohaus.de/nachrichten/autohandel/adac-test-stromverluste-durch-schnellladen-vermeiden-3231295)
- All efficiency figures in Reick et al. were taken at 21–23 °C without preconditioning, so they are a best case. — [Reick et al. 2021 (PDF)](https://arbor.bfh.ch/bitstreams/67fb6c67-ed54-4535-a0fb-f43b55a2a3f5/download)

### Inferences
- **(reasoning)** In a Danish winter (typically −5 to +5 °C overnight), a car parked outside with a cold-soaked pack will spend part of the first AC session's energy heating the battery. Two consequences for the engine:
  1. **Effective efficiency is lower early in a session and at low power.** The heater's draw is a larger share at 4 kW than at 11 kW. This reinforces the case for a per-session or per-hour overhead term (section 2).
  2. **Timing interacts with temperature.** Charging just before departure leaves a warm battery at departure, so driving efficiency and power are better; this matches Škoda's "set your departure time". Charging right after arrival uses the residual heat from driving, so charging efficiency is better; this matches the ADAC. Which wins is not quantified by any source found. A price-driven plan will often pick the middle of the night, which gets neither benefit.
- **(reasoning)** D6, where the caller folds temperature into the curves, covers power. It does not cover efficiency: `charger_efficiency` is a single number, but the caller can pass a lower one in winter. Suggest the integration derives a seasonal or temperature-banded efficiency from its own meter-versus-SoC history. The engine needs no change if efficiency stays a per-call input.
- **(reasoning)** Cold also slows charging, which is the reason the completion buffer (D8) exists. Nothing found suggests 20 minutes is too short at 11 kW AC. Evidence for or against was not found.

### Gaps
- No measurement of AC (Mode 3) charging efficiency or battery-heater energy in sub-zero conditions for any car, and none for the Enyaq.
- A SINTEF study of cabin preheating energy (up to 2 kWh typical, 5 kWh max per session) appeared only as a search snippet and could not be opened, so it is not used.
- Whether the Enyaq heats the pack during **AC** charging, and to what temperature, is not documented in any source opened.

## 5. Battery degradation: time at high SoC, cycle depth, and whether to charge "just in time"

### Takeaway
For NMC/NCA cells, calendar ageing depends strongly on storage SoC. It runs in **plateaus**,
with a step at about 55–70 % SoC where the graphite anode passes ~50 % lithiation, and a further
steep rise at 100 % for NMC. Heat makes it worse (Arrhenius). Holding 80 % is in the same
"high-fade" plateau as 70–95 %. What matters is **hours spent above the step**, not 80 versus
75. Charging close to departure reduces those hours. Never charging beyond the required floors
(O1 option a) is directly supported. Fleet data put real-world fade for AC-charged cars at about
1.5 %/year.

### Cited Findings
- Keil et al., *J. Electrochem. Soc.* 163 (9) A1872 (2016), open access:
  - **Test:** NCA, NMC and LFP 18650 cells stored at 16 SoCs from 0 to 100 % at 25, 40 and 50 °C for 9–10 months.
  - **Plateaus, not a slope:** "calendar aging does not increase steadily with the SoC. Instead, plateau regions, covering SoC intervals of more than 20%–30% of the cell capacity, are observed". "A marked step in the capacity curves is observed at about 60% SoC for the NCA and NMC cells".
  - **Cause:** low anode potential, with graphite lithiated over 50 %, drives SEI growth and loss of lithium. "staying below this characteristic SoC can reduce calendar aging considerably". The central graphite peak lies at 57 % SoC (NCA) to 73 % (LFP), depending on how much the anode is oversized.
  - **100 % for NMC:** "the NMC cells reveal a steep increase in capacity fade for the 100% cell", attributed to high-voltage side reactions.
  - **NMC at 50 °C, above 70 % SoC:** NMC cells exhibit a higher capacity fade than NCA and LFP.
  - **Conclusion:** "high storage SoCs corresponding to low anode potential should be avoided."

  — [Keil et al. 2016, PDF (TUM mediaTUM)](https://mediatum.ub.tum.de/doc/1651485/document.pdf); [TUM record](https://portal.fis.tum.de/en/publications/calendar-aging-of-lithium-ion-batteries-i-impact-of-the-graphite-/)
- Values read by eye from Keil et al. Fig. 2b (NMC cells, ~10 months of storage, relative capacity; approximate, ±0.5 points):

  | Storage SoC | 25 °C | 40 °C | 50 °C |
  |---|---|---|---|
  | 10–60 % | ≈ 0.97 (≈ 3 % loss) | ≈ 0.93–0.95 | ≈ 0.88–0.90 |
  | 70–95 % | ≈ 0.94–0.945 (≈ 5.5 % loss) | ≈ 0.89–0.90 | ≈ 0.83 |
  | 100 % | ≈ 0.935 | ≈ 0.81 | ≈ 0.77 |

  — [Keil et al. 2016, PDF p. A1874](https://mediatum.ub.tum.de/doc/1651485/document.pdf)
- Companion abstract (Keil et al., IMLB 2016; >200 cells, NMC/NCA/LFP):
  - "High-fade plateau" at **65–95 % SoC**, "medium" at **30–55 %**.
  - Lowering SoC helps only if it leaves the high-fade plateau.
  - Recommended storage below 55–70 % depending on anode balancing. For EVs, ≤50 % when unused is beneficial.

  — [ECS IMLB 2016 abstract](https://ecs.confex.com/ecs/imlb2016/webprogram/Paper76672.html)
- Werner, Paarmann & Wetzel (KIT, 2021), graphite/NCA pouch cells: capacity fade and impedance rise accelerate with temperature following Arrhenius, and "A large impact of the storage state of charge at 100% is evident, whereas the influence is small below 80%". — [KIT publication PDF](https://publikationen.bibliothek.kit.edu/1000133836/117458694)
- de Hoog et al., *Applied Energy* 200 (2017), 20 Ah NMC/graphite, 146 cells over ~2.5 years: in cycling, capacity loss is "strongly affected" by depth of discharge and temperature. In calendar ageing, it is affected "most by high storage State-Of-Charges and storage temperatures". Low-SoC storage even showed an initial capacity increase. — [IDEAS/RePEc abstract](https://ideas.repec.org/a/eee/appene/v200y2017icp47-61.html)
- Geotab fleet data:
  - **2024:** ~5,000 EVs, 1.8 %/year average degradation (2.3 % in 2019); best models 1.0 %/year; high use was "not significantly" worse. — [Geotab press release 2024](https://www.geotab.com/uk/press-release/2024-battery-degradation)
  - **2025/26:** 22,700+ EVs, 21 models. Average 2.3 %/year. Mainly DC (>100 kW) up to 3.0 %/year; **mainly AC about 1.5 %/year**. Hot climates +0.4 %/year. A wider SoC range did not materially increase degradation "unless they spent extended periods close to full or empty charge". — [Yahoo Finance on Geotab study, 2026-01-13](https://finance.yahoo.com/news/geotab-data-points-modest-rise-141059571.html)
- Schmalstieg et al. (2014), "A holistic aging model for Li(NiMnCo)O2 based 18650 lithium-ion batteries", *J. Power Sources* 257, 325–334, exists. It is identified only from a reference list; its content was not accessed. — [arXiv 2112.13671 reference list](https://arxiv.org/pdf/2112.13671)

### Inferences
- **(reasoning) A rough size of the "just in time" benefit.** At 25 °C cell temperature, NMC in Keil's data loses about 2.5 points more over 10 months stored in the 70–95 % plateau than in the 10–60 % plateau.
  - If early charging leaves the car above the step for 6 extra hours a night, 25 % of the time, the extra calendar fade is about 0.25 × 2.5 ≈ 0.6 points per 10 months, or roughly 0.7 %/year.
  - This is an upper bound. A Danish pack spends most of the year well below 25 °C and Arrhenius scaling shrinks the effect. Calendar fade also slows over time.
  - Even so, it is the same order as the fleet's whole 1.5 %/year. It is not negligible, and it is free to capture when prices tie.
- **(reasoning) Where the step lies in displayed SoC is unknown.** Keil's step sits at 55–73 % *cell* SoC, depending on cell design. The car's displayed SoC maps onto a net window inside the gross capacity, and that mapping was not found for MEB. Treat "about 55–70 % displayed" as a plausible but unverified threshold.
- **(reasoning) 80 % against 100 %.** For NMC, 100 % is a distinct further step: steep in Keil's data at 40–50 °C, and the KIT authors call 100 % "large impact". The 80 % default, with caps that allow 100 % only when a target needs it (D7), is well supported. Lowering the default from 80 to 70 % buys little, since both are in the same plateau. Lowering it below ~55 % buys a lot but costs range margin.
- **(reasoning) O1 (charge beyond the floors in cheap hours?).** The ageing physics supports option (a), never: extra SoC parked above the step is wear bought with money saved. If option (b) or (c) is ever adopted, the surplus should be capped below the step (e.g. ≤ 55–60 %), not at `default_target_soc` = 80. A wear term in scoring (D14 mentions "later … battery wear") is the cleaner long-run answer.
- **(reasoning) Tie-break for charging late.** Among hours of equal (or nearly equal, within a small tolerance) marked-up price, prefer the **latest**, so the car spends the fewest hours at high SoC before departure. This costs nothing in money. It trades against charging-time risk, which the completion buffer (D8) already covers. In winter it also leaves a warmer pack at departure (section 4).
- **(reasoning) Cycle depth.** Cycling studies (de Hoog) show DoD matters. For a commuter whose daily use is 10–20 % of capacity, shallow daily top-ups are already the engine's natural behaviour under D22. Nothing here argues for deeper, rarer cycles. The deferred "prefer shallow cycles (30–70 %)" candidate is consistent with both the calendar and the cycling evidence.

### Gaps
- The full text of Schmalstieg et al. 2014 and of de Hoog et al. 2017 (for numeric DoD coefficients) could not be accessed. A Naumann et al. NMC study was not found; the 2020 Naumann paper found covers LFP.
- No study found quantifies the real-world difference between charging early and sitting at 80 %, and charging just in time, for an EV.
- The MEB cell balancing, and so where the high-fade step falls in displayed SoC, was not found.
- Geotab's statement on SoC habits gives no numbers.

## 6. Vehicle-side behaviour: the car's own charge limit, sleep/wake, SoC reporting, standby drain

### Takeaway
The Enyaq enforces its own charge limit, which the user can change in the car. Raising it
restarts charging. MEB cars have reported wake-up and phase-handling quirks. No source was found
on SoC reporting delay or parked standby drain.

### Cited Findings
- An Enyaq iV 80 stopped at its own 80 % limit and resumed charging when the limit was raised to 90 %. A possible MEB software problem with waking for charging was reported (and disputed) in the same thread. — [GoingElectric, Enyaq thread](https://www.goingelectric.de/forum/viewtopic.php?p=1583688)
- A known bug caused an Enyaq on an OpenEVSE-type charger to ignore a current limit set on the charger until it was set again. It was described as fixed in later charger firmware. — [OpenEnergyMonitor community](https://community.openenergymonitor.org/t/skoda-enyaq-not-obeying-the-current-limit-but-does-obey-when-its-re-set-from-the-webui/20351). *This page was seen through the search tool's summary only. Treat it as weak.*
- Car-side counters do not see charging losses: on-board figures differ by 10–25 % from wall energy because "die Messsysteme im Auto können die beim Aufladen anfallenden Verluste nicht erfassen". — [motor1.com on ADAC](https://de.motor1.com/news/435391/elektroauto-ladeverluste-adac/). *Seen only in the search tool's summary; not opened.*

### Inferences
- **(reasoning)** D18 `car_max_soc` is right to exist, but on the Enyaq the user can change the car's limit at any time from the app or the car. The integration should read it live each call and pass it in, rather than treat it as a static configuration value. If the engine plans above the car's current limit, the plan silently under-delivers unless `SET_CHARGE_LIMIT` (O9) raises it.
- **(reasoning)** Because the car's energy figures exclude wall-side losses, any efficiency the integration learns should compare the charger's meter (wall kWh) against ΔSoC × capacity. It should not use the car's "charged energy".

### Gaps
- SoC reporting latency and frequency for the Enyaq through the Skoda cloud API: not found in this task.
- Standby (parked) drain per day for MEB or Enyaq: not found. No ADAC standby measurement was found.
- Skoda Battery Care Mode (80 % limit, ME3 update): seen only in search snippets (fleetnews.co.uk returned 403), so not used as a finding.

## 7. Are "parasitic" losses safe to drop (D26)?

### Takeaway
D26 combines two different things. **Parked standby drain** is safe to drop, because each call
reads a fresh SoC. **Overhead while charging** is not negligible. Control units and the 12 V
system draw an estimated 100–300 W during charging, which is 1–3 % at 11 kW but 7–21 % at
1.4–4.1 kW, and more in the cold. It is precisely what makes slow charging dearer.

### Cited Findings
- During charging, control units on the 12 V network draw an estimated 100–300 W. — [autohaus.de on ADAC 2022](https://www.autohaus.de/nachrichten/autohandel/adac-test-stromverluste-durch-schnellladen-vermeiden-3231295)
- "Die während des Ladevorgangs aktiven Bordsysteme" (on-board systems active during charging) are named as a cause of loss. Reduced-power wallbox losses are 8–12.8 %, against under 7 % at full power. — [firmenauto.de on ADAC 2026](https://www.firmenauto.de/management/fuhrparkmanagement/e-auto-ladeverluste-adac-vergleich-steckdose-wallbox-fuenf-elektroautos/)
- Efficiency is lowest at low power transfer. — [Apostolaki-Iosifidou et al. 2017 abstract](https://ideas.repec.org/a/eee/energy/v127y2017icp730-742.html)

### Inferences
- **(reasoning)** Keep D26 for standby drain, restart time and the CC/CV transition. Add a charging-overhead term, as in section 2: either `charging_overhead_kw`, or efficiency as a function of power. Then:
  - `charger_efficiency` covers the conversion loss;
  - `charging_overhead_kw` covers the time-proportional auxiliary draw, and can carry a winter value for battery heating.

  This changes the ranking of plans only where power varies between options. That happens with load-balanced or single-phase setups, and with long low-power solar sessions handled by the integration.
- **(reasoning)** Standby drain matters only across absences longer than a few days, such as a holiday. There the engine's projected SoC on return could be off. D26's "fresh SoC each call" handles the present, not the projection. Folding it into `energy_kwh` of a long absence is the caller's job (D3). The integration should document that.

### Gaps
- No measurement of the Enyaq's or MEB's auxiliary draw while charging, or of its parked standby drain.

## 8. Verdict per decision: supported, contradicted, or silent, and what should change

### Takeaway
The model's structure (two step curves, minimum times efficiency, step simulation) is sound for
11 kW three-phase home charging. Three things should change. Efficiency should depend on power,
or carry a fixed overhead. The cause of the maintainer's taper should be verified before it goes
into the SoC curve. The ageing evidence supports O1 (a) and a "latest of equal-price hours"
tie-break.

### Cited Findings
- See sections 1–7. No new sources here; the verdicts below are reasoning over those findings.

### Inferences
- **(reasoning)** Verdicts:

  | ID | Verdict | Evidence and what should change |
  |---|---|---|
  | **D12** (step simulation with both curves) | **Supported** | AC power is near-flat at 11 kW for most of the range (§1). Taper and charger effects are step-like, so a step simulation suits them. No change. |
  | **D16** (power = min(car SoC curve, charger session curve) × constant efficiency) | **Partly contradicted** | The min() structure is fine. A **constant** efficiency is contradicted at low power (§2, §7): 87 % at 3φ 16 A; 80 % at 1φ; ~78 % or worse at 6 A. Change: add `charging_overhead_kw` (preferred) or efficiency by power. State that power curves are wall-side and that costs use wall kWh. Also state that the 11 → 7.5 kW example is unverified as SoC taper: it may be a phase drop (§1). |
  | **D18** (`car_max_soc` hard ceiling) | **Supported, with a caveat** | The Enyaq enforces its own user-settable limit (§6). Read it live each call; it is not a static configuration value. Interacts with `SET_CHARGE_LIMIT` (O9). |
  | **D19** (soft `min_session_kwh` 2 kWh) | **Supported, refinable** | The 6 A minimum (4.1 kW 3φ) means no trickle sessions (§3). Short sessions should run at full power. A fixed per-start energy cost would make the minimum a cost decision rather than a threshold. Its value is unmeasured. |
  | **D26** (parasitic drain not modelled) | **Split** | Standby drain while parked: **supported** (fresh SoC each call). Overhead while charging: **contradicted** for anything but full-power three-phase charging (§7). Model the overhead (see D16). |
  | **D6** (temperature folded into curves by caller) | **Supported for power, silent or insufficient for efficiency** | Cold lowers efficiency (DC data: 39 % at −25 °C), and the Enyaq heats the pack while charging (§4). The caller should also pass a lower winter efficiency or a higher overhead. No engine change if both are per-call inputs. |
  | **D8** (20-min completion buffer) | **Silent** | No source quantifies AC charging overrun in the cold. Keep it. |
  | **O1** (charge beyond floors in cheap hours?) | **Supports lean (a), never** | Calendar fade jumps above ~55–70 % SoC and again at 100 % (NMC) (§5). If (b) or (c) is ever chosen, cap the surplus below the step (≤ ~55–60 %), not at 80 %. |
  | **O8** (`simulation_step_minutes` 6 or 3) | **Silent; reasoning favours 6** | At 11 kW a 6-min step is 1.1 kWh, about 1.4–1.8 % SoC on a 60–80 kWh pack. That is finer than any documented taper breakpoint and finer than the uncertainty in efficiency (several %) and in the cause of the taper. 3 minutes adds precision the inputs do not have. |
  | **"Prefer shallow cycles"**, deferred candidate | **Supported** | DoD drives cycle ageing; calendar ageing favours a low resting SoC (§5). |
  | **New: tie-break to the latest of equal-price hours** | **Proposed** | Free wear reduction and a warmer pack at departure in winter (§4, §5). Cheap to implement in `scoring`. |

- **(reasoning)** Suggested caller-side work, outside the engine:
  1. Log per-phase current against SoC to diagnose the 11 → 7.5 kW drop.
  2. Learn efficiency per season as charger meter kWh ÷ (ΔSoC × capacity).
  3. Read the car's own charge limit live.

### Gaps
- Every Enyaq-specific number remains unverified: the AC curve against SoC, AC efficiency, winter heating energy, standby drain, and SoC reporting latency. The maintainer's own logged sessions are likely the best available source.
