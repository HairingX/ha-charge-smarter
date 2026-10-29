# Driver behaviour and smart-charging UX: evidence for defaults, margins and controls

Scope: how drivers live with smart home charging (schedules, margins, overrides, trust), and
what this means for ChargeSmarter's decisions D7, D8, D9, the floors (`min_safety_soc`,
`min_idle_soc`), `default_target_soc` (80 %), `default_arrival_soc` (15 %), O1, O2, O12 and L1.
Research date: 2026-10-28. Every cited finding comes from a page or PDF opened during this task.
Labels: "Reasoning" marks my own inference. Origin of the data is noted per finding (DK, NO,
SE, UK, DE, NZ, NL).

Source-quality notes:
- The strongest behavioural source is the **Electric Nation Customer Trial Final Report** (UK,
  Western Power Distribution, 24/10/2019, 591 pages), read in full text. It is a real-world
  trial with logged override use, but from 2017-2019 with many small-battery cars and a
  network-driven (not price-driven) control.
- The strongest **Danish** source is Ziras et al. (2024), DTU with Spirii: 1.3 million real
  residential charging sessions in Denmark, 2021-2023.
- Stated-preference surveys (Will & Schuller, DE) are early-adopter samples, not behaviour.
- App conventions come from vendor help pages, which describe features but rarely defaults or
  failure handling.

## 1. How often do users override smart schedules, why, and what reduced overrides?

### Takeaway
Overrides are rare and concentrated: in Electric Nation's largest logged trial, 2.5 % of
charging sessions (after the novelty phase) had an override, two-thirds of participants never
used it in that period, and about 20 % of participants made 90 % of the requests. The main
reason was an unplanned or near-term extra journey. Yet the *availability* of an override is
one of the most demanded features and is what makes people accept automation.

### Cited Findings
- Electric Nation (UK) trial: "over 130,000 charging events, covering nearly two million
  hours"; "nearly 700 EV owners taking part in the 18-month trial" — [Electric Nation Customer
  Trial Final Report, pp. 9-11](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- Override mechanism: a "high priority" request in the GreenFlux app; it "effectively acted as an
  override to demand management", "only applied to the current charging transaction", and the
  charger "returned to normal priority for the next session" — [Electric Nation Final Report,
  §4 and §11.2.5](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- Override rate, whole Trial 2: 18,282 transactions, 782 with a high-priority request (4.2 %);
  147 of 241 participants with transaction data (61 %) made at least one request — [Electric
  Nation Final Report, p. 345](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- Override rate after the novelty effect (from week 27): 11,305 charging events with 282
  requests (2.5 %); 80 of 237 participants (33-34 %) used it; requests "did not exceed 5 % of
  charge events after Week 27"; "use of a high priority feature is likely to be relatively
  infrequent" — [Electric Nation Final Report, pp. 345-346](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- Concentration: "approximately 20 % of participants were responsible for 90 % of high priority
  requests"; two participants alone contributed 16 %; median participant 0 % of sessions,
  upper quartile 2.6 % — [Electric Nation Final Report, pp. 346-348, Table 11-14](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- Who overrides: participants with batteries of 35 kWh and above were more likely to override
  (51 % made a request; median 1.3 %, upper quartile 7.8 % of sessions); BEV upper quartile
  16.9 % vs PHEV 9.9 %. The report's explanation: management reduces the average current, which
  usually still fills the car, "however, this may not be the case during shorter transactions,
  or where a large amount of energy is required" — [Electric Nation Final Report, pp. 348-350](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- No link between override use and stated concern about management, or the amount of
  management actually experienced — [Electric Nation Final Report, §11.2.5.2](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- Why: "The most common reason for requesting high priority was to ensure the vehicle had enough
  charge for another journey (either later the same day, or a long journey the day after). A
  third of respondents only used the app to test it out ... to satisfy themselves that it worked
  in case they needed it later" — [Electric Nation Final Report, p. 358](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- Managed charging did not raise "hot unplugs" (unplugging before fully charged): the rate
  declined slightly from the unmanaged period through Trials 1-2, "an indication that management
  did not cause widespread inconvenience"; outside management 18 % of events were hot unplugs
  (15-minute threshold; 14 % at a 5-minute threshold) — [Electric Nation Final Report, §8.8 and §11.1](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- Acceptance: smart charging was acceptable to the "majority of trial participants", attitude
  "overwhelmingly positive" — [Drive Electric summary of Electric Nation](https://www.drive-electric.co.uk/news/smart-charging-insights-electric-nation-trial/)
- Powerco (New Zealand), 80 drivers, 2021-2023, evening throttling 17:00-21:30: "When we started
  to throttle charging to 80 %, participants started to override the charging more frequently";
  two participants suspended participation at 100 % throttling; owners of 32 A cars "felt their
  charging was too limited at higher control levels"; control level had little influence on
  satisfaction — [Powerco smart EV charging trial](https://www.powerco.co.nz/news/industry-insights/smart-ev-charging-trial)
- Stated preference (Germany, 237 early adopters): 76 % request the ability "to override the
  smart charging process and charge directly"; 77 % a minimum range; 71 % a planned departure
  time. Users want "between three to four main features (range buffer, manual override,
  expected departure time, planned range) and do not want an overly complex interaction" —
  [Will & Schuller 2016, Transportation Research Part C 71, author version](https://publikationen.bibliothek.kit.edu/1000058842/16803231)
- Same study: acceptance drivers were grid stability and renewables; "the individual need for
  flexibility should not be impaired through charging control"; economic incentives were not
  significant in that sample — [Will & Schuller 2016](https://publikationen.bibliothek.kit.edu/1000058842/16803231)
- Sweden (surveys N = 1428, 24, 31; 27 interviews; supplier-managed charging at public
  stations): users were positive to the concept and "willing to relinquish some control", but
  the technology was "associated with uncertainty and anxiety", and flexibility depended on
  working patterns, finances and charger access — [IIIEE Lund summary of the 2022 study](https://www.iiiee.lu.se/article/requesting-control-and-flexibility-exploring-swedish-user-perspectives-electric-vehicle-smart)
- Denmark (2026): FDM reports many drivers notice slower charging and "undrer sig over, at
  elbilen lader langsommere i perioder"; FDM asks operators to inform consumers far better —
  [Mobilsiden, 20 Aug 2026](https://mobilsiden.dk/?p=287502)

### Inferences
- Reasoning: an override is primarily a *trust device*; a third of users pressed it only to see
  that it worked. Its presence matters more than its usage rate. Design it to be findable and
  obviously working, not for heavy use.
- Reasoning: the dominant override trigger (an extra trip later the same day, or a long trip
  tomorrow that was not entered) is exactly what a lean "charge only to the stated need" planner
  is most exposed to. The cheapest remedy is a sensible floor charged early, not a smarter
  optimiser (see O1 and floors below).
- Reasoning: larger batteries overrode more in Electric Nation because sessions needing much
  energy were squeezed. Modern Danish cars (large packs, 11 kW) are closer to that group, so a
  2019 override rate of 2.5 % is a floor estimate, not a ceiling.
- Reasoning: override frequency rises with control intensity (Powerco). A price optimiser that
  pushes all charging to the last cheap hours is "intense control" from the driver's view; a
  margin that leaves the car usable early in the night reduces overrides.

### Gaps
- No Danish or Nordic measurement of override frequency for price-based (rather than
  grid-based) smart charging was found. Searches for Insero, Energinet, Clever trial results
  returned nothing usable.
- An Australian study (Transportation Research Part A, 2025) reportedly found an override app
  raised stated willingness to adopt managed charging from 43.9 % to 61.5 %; the article page
  returned HTTP 403, so this is **unverified** (search snippet only):
  https://www.sciencedirect.com/science/article/pii/S0965856425002903
- A Dutch study of 138 households with an override button (Gardien, Refa, Tamis, EVS33, 2020)
  was found, but only the abstract was accessible; its override results were not found —
  [HvA record](https://research.hva.nl/en/publications/exploring-electric-vehicles-owners-preferences-and-experiences-wi/)
- No Octopus or Ohme published data on override (bump/max charge) frequency was found.

## 2. Danish driving and plug-in behaviour: how much flexibility exists?

### Takeaway
Danish home sessions are typically long and small: 35 % last 9-15 hours (overnight), half need
under 12 kWh, and a typical weekday car is plugged in from about 16-17 to 6-8. Most cars do not
plug in daily (40 % of re-plugs within 24 h, 85 % within 72 h). Flexibility is large; Danish
users already delay charging to about 01:00, "early enough to guarantee full charging".

### Cited Findings
- Dataset: Spirii residential chargers across Denmark, 2021-2023, 1.3 million sessions after
  filtering; at least 10 % of customers have two vehicles; most installations have a 25 A fuse
  (max 11 kW three-phase) — [Ziras et al. 2024, Electric Power Systems Research 234, DTU Orbit PDF](https://backend.orbit.dtu.dk/ws/files/364983824/1-s2.0-S0378779624004425-main.pdf)
- Plug-in/out times: weekday plug-in peak around 17:00; weekday plug-out peak between 7 and 8;
  "users who plug in their EV around 16 will plug out on average 14 h later (around 6)";
  summer weekends shift plug-in toward 11:00 — [Ziras et al. 2024](https://backend.orbit.dtu.dk/ws/files/364983824/1-s2.0-S0378779624004425-main.pdf)
- Duration: bimodal (short sessions of a few hours vs overnight ~12 h); "35 % of the sessions
  last between 9 and 15 h"; "only 8 % of the sessions last more than 24 h"; utilisation
  drops below 0.5 for sessions of 6 h and more — [Ziras et al. 2024](https://backend.orbit.dtu.dk/ws/files/364983824/1-s2.0-S0378779624004425-main.pdf)
- Energy: sessions span 0-80 kWh, "approximately 50 % of them having a consumption of less than
  12 kWh"; sessions over 6 h average about 20 kWh — [Ziras et al. 2024](https://backend.orbit.dtu.dk/ws/files/364983824/1-s2.0-S0378779624004425-main.pdf)
- Frequency: "40 % of the sessions are fewer than 24 h apart, 70 % fewer than 48 h apart and 85 %
  72 h apart"; energy rises with gap and saturates after 4 days — [Ziras et al. 2024](https://backend.orbit.dtu.dk/ws/files/364983824/1-s2.0-S0378779624004425-main.pdf)
- Price response: share of delayed sessions rose above 50 % after the August 2022 price spike;
  "Most users apply delays that postpone charging after 22 and usually around 1"; users "simply
  delay charging to hours of typically low spot prices and early enough to guarantee full
  charging", which captures "most of the economic benefit" — [Ziras et al. 2024](https://backend.orbit.dtu.dk/ws/files/364983824/1-s2.0-S0378779624004425-main.pdf)
- Occupancy: chargers have a car connected 30-40 % of the time at night on weekdays in 2023,
  around 10 % at midday — [Ziras et al. 2024](https://backend.orbit.dtu.dk/ws/files/364983824/1-s2.0-S0378779624004425-main.pdf)
- Danish travel survey 2025 (11,477 interviews, persons over 6): car travel 29.3 person-km per
  person per day, 21.4 car vehicle-km per person per day (excl. business); average trip
  14.0 km; 39.3 km total travel per person per day — [DTU TU årsrapport Danmark 2025, Tables 2-3](https://www.man.dtu.dk/-/media/institutter/management/scientific-advice/transportvaneundersoegelsen/t-u/tu-udgivelser/tu_danmark_2025.pdf)
- UK comparison: median charging frequency 3-4 times a week; 15 % charge at least daily (mostly
  PHEVs); larger batteries (35 kWh+) "usually re-fill about 15 % to 50 % of their battery
  capacity on each charge"; 75 % of cars plugged in 17-19 are charging less than half the time
  plugged in — [Electric Nation Final Report, p. 10](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- UK: cars plugged in "over 12 hours" on average but drawing power for 1.5 hours; average BEV
  session starts "more than 50 % full" — [Drive Electric summary](https://www.drive-electric.co.uk/news/smart-charging-insights-electric-nation-trial/)

### Inferences
- Reasoning: with ~12 h overnight plug-ins and ~12-20 kWh per session at 11 kW, a typical session
  needs 1-2 hours of charging, out of 9-15 hours available. The engine will almost always find a
  cheap slot; the user risk lies in *unannounced* trips and in *missing* sessions (60 % of
  re-plugs are more than a day apart), not in a lack of hours.
- Reasoning: because cars are often not plugged in daily, the SoC at plug-in can be low after a
  2-3 day gap. A floor charged at once is useful on those evenings.
- Reasoning: users already reach "most of the economic benefit" with a crude "delay to ~01:00
  and fill up" rule. The marginal saving from also shaving the *amount* charged (O1 option a)
  is small compared with its availability risk.

### Gaps
- No Danish per-car daily driving distance for EVs was verified. The Trafikdage 2025 abstract on
  Danish EV driving (reported to say white-plate EVs drive about 5 km/day more than other cars)
  could not be accessed (HTTP 503, connection reset):
  https://www.trafikdage.dk/abstracts_2025/Elbilernes%20elforbrug%2C%20elomkostninger%20og%20afledte%20CO2-emissioner.pdf
- Danmarks Statistik: no EV-specific km per car figure was found.
- Norwegian Elbilisten survey results (night charging share, home charging share) were behind a
  paywall at tu.no; not accessed.

## 3. Departure-time prediction vs user-entered schedules; how apps ask for time and target

### Takeaway
Drivers *can* predict their departures fairly well on average, but they rarely bother to enter
them: in Electric Nation only a small minority used journey planning, and Clever (DK) calls
manual entry "cumbersome" and a source of "inaccurate" plans. Commercial apps converge on a
**single recurring "ready by" time plus a target %**, defaulting to sensible values when the user
enters nothing.

### Cited Findings
- Accuracy: 60 drivers, 2-week field test with GPS and logbooks; "participants are on average able
  to accurately predict their departure times and trip lengths although for some outliers their
  prediction errors would potentially have led to insufficient battery levels"; trip type
  (work, leisure, shopping) affected accuracy — [Hahnel, Gölz & Spada 2013, Transportation
  Research Part A 48](https://fis.leuphana.de/en/publications/how-accurate-are-drivers-predictions-of-their-own-mobility-accoun/)
- Burden: in Electric Nation's CrowdCharge app, entering journey plans was mentioned as a reason
  to use the app by only 7 %; reasons for not using it were "a lack of clarity around the benefits
  ... and the balance of time required to enter the information and the benefit received"; "80 %
  of participants entered their state of charge for fewer than 1 in 5 of their charging sessions"
  — [Electric Nation Final Report, pp. 314-327](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- Default when nothing is entered: CrowdCharge assumed "a default journey (50 miles, departing four
  hours after plug-in)" with "a conservative assumption for vehicle efficiency" — [Electric Nation
  Final Report, §11 and §12](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- Denmark: Clever's smart charging required customers to "manually enter details like charging
  need in kWh", "a cumbersome process that often leads to inaccurate estimates and suboptimal
  charging plans"; reading vehicle data via Enode raised the plan matching rate from 75 % to 90 % —
  [Enode/Clever announcement](https://enode.com/newsroom/clever-and-enode-partner-to-build-state-of-the-art-smart-charging-with-real-time-ev-data)
- Stated preference: 71 % want to submit a planned departure time; 37 % want "a variation range
  around their arrival time"; 60 % want a "planned range which serves as an upper threshold beyond
  which no additional battery charge is necessary" — [Will & Schuller 2016](https://publikationen.bibliothek.kit.edu/1000058842/16803231)
- Octopus Intelligent (UK): asks for a "ready by" time restricted to 04:00-11:00 and "how much
  charge you need"; the schedule "is always displayed in your app after your plug in" —
  [Octopus Intelligent Go FAQs](https://octopus.energy/intelligent-go-faqs/); [Octopus Intelligent FAQs](https://octopus.energy/intelligent-faqs)
- Ohme (UK): target and "Ready by" (when the car should finish) need Dynamic Charging on; without
  a car integration it can only "top up by" an amount; a change made while plugged in "is saved at
  plugout" as the next session's target; with Dynamic Charging off it defaults to "Charge to full,
  ready as soon as possible" — [Ohme: update my charging target](https://ohme-ev.com/support/how-do-i-update-my-charging-target/);
  [Ohme: choose the right target](https://ohme-ev.com/support/how-do-i-choose-the-right-target-for-my-car/)
- evcc (open source, HA-adjacent): a plan is "a departure time and a charging goal"; percent when
  SoC and capacity are known, else kWh (kWh plans are one-off and cannot repeat); repeating plans
  by weekday, stored per vehicle; optional "late charging" moves 15 min-2 h of charging to just
  before departure for preconditioning and to avoid long high-SoC periods — [evcc docs: plans](https://docs.evcc.io/en/features/plans)
- Tibber (Nordic): departure time and battery level are set per car ("Power-up"), so households
  can have different departure times per EV; the app shows "exactly which hours the charging of
  your car is planned to" — [Tibber: Smart Charging 2.0](https://tibber.com/en/magazine/news/smart-charging-2.0)
- Denmark: weekday plug-out times are consistent, peaking between 7 and 8 — [Ziras et al. 2024](https://backend.orbit.dtu.dk/ws/files/364983824/1-s2.0-S0378779624004425-main.pdf)

### Inferences
- Reasoning: the integration must assume most users will configure one recurring weekday
  departure (and maybe a weekend one) and then never touch it. Trips will often be missing.
  Defaults and floors carry the safety, not the trip list.
- Reasoning: weekday plug-out times in Denmark are regular enough that the integration (not the
  engine, per D27) could propose a default departure from the car's own plug-out history.
  This is a later feature; a fixed configurable default (e.g. 07:00 weekdays) is the first step.
- Reasoning: the Octopus restriction of "ready by" to 04:00-11:00 shows that commercial products
  design for the overnight case; ChargeSmarter's arbitrary targets are richer, so the UI should
  still make the recurring morning target the easy path.

### Gaps
- No study comparing learned departure prediction against user entry on the *rate of not-ready
  events* in a home price-optimising setting was opened (arXiv/AAAI papers found but not read).
- Tibber's support article on smart charging returned 404; per-weekday departure defaults in
  Tibber could not be verified.

## 4. Safety margins: minimum SoC, arrival buffers and default targets

### Takeaway
Users want a guaranteed minimum (77 % request one; mean 70 km, median 50 km) and leave 20-25 %
of their range unused as a psychological buffer. Commercial and open-source tools implement a
"minimum charge, charged immediately regardless of price" floor and a separate upper limit, with
a per-plan target allowed to exceed the everyday limit.

### Cited Findings
- 77 % request an option to submit a minimum range; "The average minimum range requested in the
  sample is 70 km (median 50 km)" — [Will & Schuller 2016](https://publikationen.bibliothek.kit.edu/1000058842/16803231)
- "usually 20 to 25 percent of the available range resources of electric vehicles are lost as a
  psychological safety buffer"; range experience is "highly subjective" and depends on
  understanding of range and preferred safety margin (MINI E Berlin, 79 users, 6 months) —
  [TU Chemnitz press release on Franke's dissertation](https://www.tu-chemnitz.de/tu/pressestelle/aktuell/5618/en)
- evcc "minimum charge": the car charges to it "as quickly as possible after plugging it in", even
  from grid or home battery; if SoC is unknown at plug-in, evcc assumes empty — [evcc docs: limits](https://docs.evcc.io/en/features/limits)
- evcc limit: a per-vehicle default limit applies at plug-in; a temporary limit "only applies to
  the current charging process"; a limit set in the vehicle is "a hard limit that evcc cannot
  exceed"; "Charging plans have a higher priority than the charging limit" (a 100 % plan overrides
  an 80 % limit) — [evcc docs: limits](https://docs.evcc.io/en/features/limits)
- Tibber: "the car will always be charged right away until it reaches your minimum battery level"
  — [Tibber: Smart Charging 2.0](https://tibber.com/en/magazine/news/smart-charging-2.0)
- Ohme uses 80 % as its example target; no default is stated — [Ohme: choose the right target](https://ohme-ev.com/support/how-do-i-choose-the-right-target-for-my-car/)
- Octopus makes no charge-limit recommendation and states the plan won't affect battery life more
  than regular charging — [Octopus Intelligent Go FAQs](https://octopus.energy/intelligent-go-faqs/)
- Electric Nation's no-information default was deliberately conservative (50 miles, conservative
  efficiency) — [Electric Nation Final Report](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)

### Inferences
- Reasoning, with an **unsourced assumption** of 18-20 kWh/100 km for illustration only: a 50-70 km
  minimum range is about 9-14 kWh, i.e. roughly 15-20 % of a 70 kWh pack. That puts users' stated
  "minimum range" in the same band as `default_arrival_soc` = 15 % and suggests a
  `min_safety_soc`/`min_idle_soc` expressed or explained in km would be closer to how users think.
- Reasoning: Franke's 20-25 % buffer is a range people *do not use*; an arrival target of 15 % is at
  or below the margin novice drivers keep. 15 % is defensible for experienced drivers; 20 % is
  the safer default for a broad audience. Franke's work also suggests the buffer shrinks with
  experience, so it should be easy to lower.
- Reasoning: "minimum charged at once regardless of price" (evcc, Tibber) is the common pattern
  for a safety floor and matches `min_safety_soc`. Neither tool documents an equivalent of
  `min_idle_soc` charged *in cheap hours*; that is a ChargeSmarter refinement.

### Gaps
- Tesla's official daily/trip charge-limit guidance (tesla.com/support/range and owner's manual)
  returned HTTP 403; manufacturer default targets (80 % daily / 100 % for trips) are therefore
  **not verified** in this note. Forum claims seen in search results were not used.
- No source measured what arrival SoC drivers actually *choose* when asked per trip.
- Volkswagen, Hyundai/Kia, and other manufacturer app defaults were not researched.

## 5. Explanations and trust: what users need, and how "not ready" is handled

### Takeaway
Visibility of the plan (which hours, expected cost) is the main trust feature apps ship. Users
who do not understand why charging is slow or late become anxious (Sweden, FDM in Denmark).
No commercial help page found documents what happens when the car is *not ready* by the
deadline; the best-effort "full charge trumps price" rule is the one explicit guarantee.

### Cited Findings
- Tibber: aims for "even more transparency"; shows the planned charging hours and a calculated
  session price — [Tibber: Smart Charging 2.0](https://tibber.com/en/magazine/news/smart-charging-2.0)
- Octopus: the schedule "is always displayed in your app after your plug in"; any charging they did
  not schedule "is charged at your normal home energy rate"; stopping can lag "up to 30 minutes"
  because of status-check intervals — [Octopus Intelligent FAQs](https://octopus.energy/intelligent-faqs);
  [Octopus Intelligent Go FAQs](https://octopus.energy/intelligent-go-faqs/)
- Ohme "Max charge" shows a pink "Max charging" banner with "Time until full" — [Ohme: update my
  charging target](https://ohme-ev.com/support/how-do-i-update-my-charging-target/)
- Electric Nation app: most-used function was viewing charging history; the smart-charging inputs
  were rarely used; a third used the override only to test it — [Electric Nation Final Report,
  pp. 314-316, 358](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- Electric Nation: "Satisfaction and acceptability can be linked to participants use of the app"
  — [Electric Nation Final Report, §11.1 summary](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- Will & Schuller: the perceived risk of smart charging (e.g. "reduced operational range")
  reduces acceptance — [Will & Schuller 2016](https://publikationen.bibliothek.kit.edu/1000058842/16803231)
- Sweden: smart charging "associated with uncertainty and anxiety" — [IIIEE Lund](https://www.iiiee.lu.se/article/requesting-control-and-flexibility-exploring-swedish-user-perspectives-electric-vehicle-smart)
- Denmark: drivers wonder why the car charges more slowly at times; FDM calls for better
  information — [Mobilsiden 2026](https://mobilsiden.dk/?p=287502)
- Franke and colleagues: trust in the range estimation system is a resilience factor against
  range stress — reported in search results only; the 2015 paper itself was **not opened**.

### Inferences
- Reasoning: three facts must be visible at plug-in for trust: (1) "ready by HH:MM at X %" status
  (met/partial), (2) when charging will happen, (3) expected cost. ChargeSmarter's D29 output
  (feasibility + per-target status and SoC) already carries (1); (2) is in the plan; (3) needs
  cost in the output or in the integration.
- Reasoning: the plan's *start* time matters for trust more than in commercial apps, because
  a plan that starts at 03:00 looks like "nothing is happening" at 22:00. Showing "next charge
  starts at 03:00" removes the main reason to press "charge now" just to check.
- Reasoning: the only failure rule documented anywhere (Tibber, ChargeSmarter D9) is best-effort
  with price ignored. Shortfall must be surfaced *at plug-in*, when the user can still act
  (raise the cap, charge now, plan a stop), not at departure.

### Gaps
- No vendor documents what happens or what is shown when a target is missed (Octopus FAQ silent;
  Tibber support article 404; Easee support 403).
- No study found quantifying how much a displayed savings figure changes override behaviour.

## 6. Manual control conventions across apps

### Takeaway
The convention is: one-tap "charge now" that applies to the **current session only** and reverts
at unplug; a per-session target change; a separate minimum charged at once; and turning smart
charging off. "Pause" exists mostly as stopping a session or editing the schedule.

### Cited Findings
- Electric Nation: the override applied to a single session and reverted next session — [Electric
  Nation Final Report](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- Octopus: "bump charge" starts a charge immediately and can be stopped in the app; "boost" for a
  quick charge outside scheduled slots, billed at the normal rate; smart charging can be turned off
  in settings — [Octopus Intelligent FAQs](https://octopus.energy/intelligent-faqs)
- Ohme: "Max Charge" temporarily turns off Dynamic Charging, routines and price cap and charges as
  fast as possible until full or unplugged; "Smart charge" or re-plugging restores the settings;
  a session-only change to a routine reverts at plugout — [Ohme: update my charging target](https://ohme-ev.com/support/how-do-i-update-my-charging-target/)
- evcc: temporary charge limit applies to the current session only and resets at unplug; a plan
  can temporarily exceed the limit; minimum charge is charged at once — [evcc docs: limits](https://docs.evcc.io/en/features/limits);
  [evcc docs: plans](https://docs.evcc.io/en/features/plans)
- Tibber: minimum battery level is charged right away; departure time and battery level are
  per car — [Tibber: Smart Charging 2.0](https://tibber.com/en/magazine/news/smart-charging-2.0)

### Inferences
- Reasoning: users expect "charge now" to be one tap, session-scoped, and self-reverting at
  unplug, with a visible banner and a cost hint. A sticky override that silently disables the
  planner for days would be a trust failure of a different kind (high bills).
- Reasoning: a "charge now to X %" variant (Tibber's minimum, evcc's min SoC) covers the main
  override reason (a trip later today) better than a full-power-to-100 % button: it gives enough
  for the trip and lets the plan resume.

### Gaps
- Easee (HTTP 403) and Zaptec (not researched) app conventions are not documented here.
  Easee's override behaviour seen only in search snippets was not used.
- Tibber "charge now"/"pause" controls could not be verified (support article 404).

## 7. What this means for ChargeSmarter's decisions

### Takeaway
The evidence supports the hard-cap, buffer and best-effort decisions, and the safety floor. It
**argues against the O1 lean (a) "never charge beyond the floors"**: unannounced trips are the
main override cause and users rarely enter plans, so a modest fill in cheap hours buys most of
the trust at little cost. Manual controls (O12) and basic explanations (part of L1) should come
earlier than planned.

### Cited Findings
(References to findings above; sources in sections 1-6.)
- Override reason = extra trip today or tomorrow; overrides concentrated in large-battery users —
  [Electric Nation Final Report](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)
- Users rarely enter journey plans or SoC — [Electric Nation Final Report](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378);
  [Enode/Clever](https://enode.com/newsroom/clever-and-enode-partner-to-build-state-of-the-art-smart-charging-with-real-time-ev-data)
- Danish users delay to ~01:00 and fill — [Ziras et al. 2024](https://backend.orbit.dtu.dk/ws/files/364983824/1-s2.0-S0378779624004425-main.pdf)
- Plans may exceed the everyday limit; vehicle limit is hard — [evcc docs: limits](https://docs.evcc.io/en/features/limits)

### Inferences — decision by decision (all Reasoning unless a source is cited)

| Item | Verdict | What should change |
|---|---|---|
| **D7** hard caps; a target's own cap wins over `default_target_soc` | **Supported.** evcc uses the same structure: a per-vehicle default limit, plans may exceed it, the car's own limit is hard ([evcc limits](https://docs.evcc.io/en/features/limits)); 60 % of users want a "planned range" upper threshold ([Will & Schuller](https://publikationen.bibliothek.kit.edu/1000058842/16803231)) | None to the engine. Integration: make "raise the cap for this trip" a one-tap fix on a `PARTIAL` result |
| **D8** 20-min completion buffer, absolute | **Supported in principle, silent on the value.** Electric Nation logs 14-18 % hot unplugs (people leave early) ([report](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)); drivers' predictions have outliers ([Hahnel 2013](https://fis.leuphana.de/en/publications/how-accurate-are-drivers-predictions-of-their-own-mobility-accoun/)); 37 % want a tolerance around times ([Will & Schuller](https://publikationen.bibliothek.kit.edu/1000058842/16803231)). Counterpoint: evcc offers charging *up to* departure to keep the battery warm and precondition ([evcc plans](https://docs.evcc.io/en/features/plans)) | Keep 20 min. Note in docs that the buffer must also cover control latency: Octopus reports stop/start lag of up to 30 min ([Octopus](https://octopus.energy/intelligent-faqs)); if the integration's actuation lag is larger, the buffer should be at least that lag. Keep L3 (per-target) deferred; preconditioning is the car's job |
| **D9** best effort, report shortfall | **Supported.** Tibber: "full charge trumps low price"-type behaviour (minimum charged "right away") ([Tibber](https://tibber.com/en/magazine/news/smart-charging-2.0)); Electric Nation default was conservative | Surface the shortfall at plug-in (integration), not at departure |
| **`min_safety_soc`** (charge at once, any price) | **Supported.** evcc min SoC and Tibber minimum level work exactly this way; 77 % ask for a minimum range, mean 70 km / median 50 km ([Will & Schuller](https://publikationen.bibliothek.kit.edu/1000058842/16803231)) | Give it a non-zero default (Reasoning: ~10-15 %, or "50 km" converted by the caller). Consider letting the integration show it in km |
| **`min_idle_soc`** (charged in cheap hours, no targets) | **Supported, and evidence says it carries most of the safety**: users rarely enter trips; unplanned trips drive overrides | Default it high enough for an unplanned round trip, e.g. ~40-50 % (Reasoning; Electric Nation's own default was a 50-mile trip). Reconsider `idle_planning_horizon_hours` = 24: cars are often not plugged in the next day (60 % of re-plugs > 24 h apart, [Ziras](https://backend.orbit.dtu.dk/ws/files/364983824/1-s2.0-S0378779624004425-main.pdf)), so reach the idle floor *within the current plug-in* (by the expected plug-out, e.g. next 07:00) rather than within 24 h |
| **`default_target_soc` = 80 %** | **Silent / not verified.** Ohme uses 80 % as its example; manufacturer guidance could not be opened (Tesla 403) | Keep 80 % as default; do not cite manufacturer guidance until verified |
| **`default_arrival_soc` = 15 %** | **Partly contradicted.** Drivers leave 20-25 % of range unused as a psychological buffer ([TU Chemnitz/Franke](https://www.tu-chemnitz.de/tu/pressestelle/aktuell/5618/en)) | Default 20 % (Reasoning), easy to lower; experienced drivers will lower it |
| **O1** charge beyond floors when cheap | **Evidence contradicts lean (a).** Danish users fill up in cheap night hours and capture most of the benefit ([Ziras](https://backend.orbit.dtu.dk/ws/files/364983824/1-s2.0-S0378779624004425-main.pdf)); overrides come from unplanned trips ([Electric Nation](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)) | Prefer (c) percentile of the horizon's prices, up to `default_target_soc`, or (b) a user price threshold; (c) needs no user input, which matters given low input engagement. If (a) is kept, raise the default `min_idle_soc` as above |
| **O2** arrival SoC per absence or global | **Supported: global default with optional per-absence value.** Users rarely enter per-trip data ([Electric Nation](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)) | `min_soc_at_end` on `AbsenceWindow`, defaulting to `default_arrival_soc`; the UI should never require it |
| **O12** manual "charge now" / "pause" | **Strongly supported as a trust feature.** 76 % want an override ([Will & Schuller](https://publikationen.bibliothek.kit.edu/1000058842/16803231)); used in 2.5-4.2 % of sessions, a third only to test it ([Electric Nation](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)) | Design it before release: (1) "Charge now" — session-scoped, reverts at unplug (Electric Nation, Ohme, evcc convention), with banner and cost hint; (2) "Charge now to X %" — covers the trip-today case; (3) "Pause until …" with an expiry, never open-ended; (4) "Ready by" one-off target (maps to a `ChargeTarget`); (5) smart charging off. In the engine, (2) is a target at `now` and (3) an `AbsenceWindow` with `energy_kwh = 0`, so no engine change is needed |
| **L1** advice output | **Partly supported to bring forward.** Plan visibility and cost are what apps ship for trust ([Tibber](https://tibber.com/en/magazine/news/smart-charging-2.0), [Octopus](https://octopus.energy/intelligent-faqs)); confusion about slow charging is a Danish complaint ([Mobilsiden](https://mobilsiden.dk/?p=287502)) | Keep advice codes deferred, but make sure the output already gives: per-target status and margin (D29), next charging start, and expected cost of the plan. "Avoidable at 100 %"-type advice can wait |

### Gaps
- None of the decisions can be checked against Danish *override* data; such data was not found.
- The recommended default values above (idle floor ~40-50 %, safety floor ~10-15 %, arrival 20 %)
  are reasoning from the cited evidence, not measured optima; they should be marked as such in
  `decisions.md` if adopted.
