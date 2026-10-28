# Red-team audit of the seven research notes on cheapest home EV charging

Panel role: sceptic. Done on 2026-10-28. I tested whether the evidence carries the notes' most
decision-relevant claims. I did not argue positions.

Method, so every verdict can be checked:

- **Re-opened** means I fetched the cited page, PDF, API or source file myself today and found
  the quoted text or number.
- **Re-ran** means I ran the notes' own scripts in `experiments/` (Python 3.13.17) on data I
  downloaded today from the same APIs.
- **Recomputed** means I wrote my own code (not kept in the repository) on the same data.
- **Reasoning** marks my own argument.
- **Could not re-open** means I tried and failed. In each case the reason is given.

Data fetched today:

- Energi Data Service `DayAheadPrices`, DK1/DK2, 2025-10-01 to 2026-10-29: 75,656 quarter-hour
  rows ([API](https://api.energidataservice.dk/dataset/DayAheadPrices)).
- `Elspotprices`, DK1, Jan–Sep 2025: 6,551 hourly rows, 411 of them negative
  ([API](https://api.energidataservice.dk/dataset/Elspotprices)). The scheduling note says 6,527
  rows with 411 negative; the row count differs slightly.
- `DatahubPricelist` rows for N1 area 131, Radius `DT_C_01`, elafgift `EA-001`, Systemtarif and
  Transmissions nettarif ([API](https://api.energidataservice.dk/dataset/DatahubPricelist)).
- The 46 elpriser.org archive runs, issued 2026-10-06 to 2026-10-28, for DK1 and DK2
  ([archive API](https://elpriser.org/api/openapi.json)).

Verdict scale: **confirmed**, **misread**, **overstated**, **unsupported**, **could not re-open**.

## 1. Which of the most decision-relevant claims survive re-opening at the source?

### Takeaway
The factual backbone survives. That covers taxes, tariffs, the 15-minute market, how rare
negative totals are, the Škoda/Zaptec/Easee facts, the evcc/emhass code, and the Electric Nation
figures. Every script re-run reproduced its note's numbers.

What does not survive is the step from those numbers to the recommendations:

- **The savings figure** (1,400–3,000 DKK/yr) is the value of any timing at all. A midnight timer
  already gets about 60–65 % of it.
- **"D22 as written is 8 % worse (63 % worst)"** measures a trimming rule that motor.md does not
  specify. The figure is about 3× smaller once Danish tariffs are in the price.
- **The forecast bias of 114–158 DKK/MWh**, and the markup sizes built on it, move by about 50 %
  when two more days of data are added. The bias was measured within each day, not as the
  cross-day choice the markup governs.
- **Two behavioural claims misread Ziras et al.:** "most cars do not plug in daily", and "Danish
  users fill up, so O1(a) is contradicted".

### Cited Findings

**Price composition (price_composition_denmark.md)**

- **Elafgift.** Re-opened. skat.dk: "fra 1. januar 2026 til 31. december 2027 vil satsen for
  elafgiften blive sat ned til 0,8 øre pr. kWh", "svarende til 0,008 kr. pr. kWh" —
  [skat.dk](https://skat.dk/erhverv/afgifter-paa-varer-og-ydelser-punktafgifter/nyhedsbrev-afgifter/midlertidig-nedsaettelse-af-elafgiften-i-2026-og-2027).
  DataHub `EA-001` is 0.008 from 2026-01-01 to 2028-01-01, and 0.72 in 2025. Systemtarif is
  0.074 / 0.072 / 0.049 and Transmissions nettarif 0.061 / 0.043 / 0.056 for 2025 / 2026 / 2027 —
  [DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist). **Confirmed.**
- **Tariff periods.** Re-opened. "Lavlast: kl. 24-06 … Højlast: kl. 06-17 og 21-24 … Spidslast:
  kl. 17-21", with winter tariffs from 1 October to the end of March "hos de fleste netselskaber"
  — [Tænk](https://taenk.dk/forbrugerliv/bolig/nettariffer-betydning-for-samlet-elpris).
  **Confirmed.**
- **Tariff rates.** Re-opened in DataHub:
  - Radius `DT_C_01`, 2026-10-01 → 2027-04-01: 0.106175 / 0.318524 / 0.955573.
  - N1 A/S - 131 `CD`, 2026-10-01 → 2027-01-01: 0.087854 / 0.263563 / 0.79069.
  - N1 also has a separate December 2025 row (0.068 / 0.204 / 0.612).
  - Source: [DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist).
    **Confirmed.**
- **15-minute day-ahead.** `DayAheadPrices` has resolution "15 minutes (PT15M)" and points to
  Elspotprices "for data before 2025-10-01" —
  [metadata](https://api.energidataservice.dk/meta/dataset/DayAheadPrices). **Confirmed.**
  Minor misread: the note says the first quarter-hour row is 2025-10-01T00:15. The dataset holds
  a row at `TimeDK` 2025-10-01T00:00 for both areas (own query).
- **Hourly averaging on default products.** "timeprisen i fremtiden blive beregnet ud fra et
  simpelt gennemsnit af priserne i de fire kvarterer". Suppliers with "mindst 200.000 kunder"
  must offer quarter-hour products. One supplier's press officer estimates an average family
  "måske vil kunne spare 200 kroner om året" —
  [Tænk](https://taenk.dk/forbrugerliv/bolig/flere-elpriser-i-doegnet-giver-minimale-besparelser).
  **Confirmed.**
- **Negative total price nearly never.** Recomputed: (spot + grid tariff + Energinet + elafgift)
  × 1.25, markup 0, 2025-10-01 to 2026-10-29.
  - DK1 (N1 131): total below 0 in **2** quarter hours (2026-05-24 14:00 and 15:00); minimum
    −0.075 DKK/kWh.
  - DK2 (Radius): **0**; minimum +0.205 DKK/kWh.
  - Data: [DayAheadPrices](https://api.energidataservice.dk/dataset/DayAheadPrices),
    [DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist).
  - **Confirmed**, for these two grid companies only.
- **Savings 1,400–3,000 DKK/yr.** Recomputed independently: 392 nights, plug-in 17:00–07:00,
  cheapest quarters of the total price.

  | Case | Saving vs plug-in at 17:00 | Note's figure |
  |---|---|---|
  | DK1, 5 kWh/night, 11 kW | 1,396 DKK/yr (38 %) | 1,399 |
  | DK1, 7.5 kWh/night, 11 kW | 2,203 | 2,208 |
  | DK2, 5 kWh/night, 11 kW | 1,704 | 1,708 |
  | DK2, 7.5 kWh/night, 3.7 kW | 3,046 | 3,051 |

  **Arithmetic confirmed.** Two problems remain:
  - **Reproducibility.** `experiments/prices/arr.py` imports a function `total` from `analyse.py`,
    and the `analyse.py` in that folder defines none. `arr.py` also only covers the 2026
    sensitivity table. The script behind the headline 393-night table is not in the repository.
  - **Overstated as the engine's value.** Against a fixed timer from 00:00, smart charging saves
    only:
    - 484 DKK/yr (DK1, 5 kWh), 634 (DK1, 7.5 kWh);
    - 466 (DK2, 5 kWh), 608 (DK2, 7.5 kWh).

    The note's own 2026 table gives 619 (DK1, 6 kWh). Danish users already delay: "the delay
    utilization rate above 50%" after August 2022 —
    [Ziras et al. 2024](https://backend.orbit.dtu.dk/ws/files/364983824/1-s2.0-S0378779624004425-main.pdf).

**Forecasts (price_forecast_uncertainty.md)**

- **elpriser.org published backtest.** Re-opened.
  - MAE "D+2: 149 / 165 … D+5: 179 / 192 … D+7: 195 / 207 … 197 / 211 DKK/MWh — 23–32 % of the
    mean price, against 35–38 %" — [OpenAPI spec](https://elpriser.org/api/openapi.json).
  - Min-hour hit rate 69.0 % / 70.0 %; P10–P90 coverage 80.5 % / 80.3 % —
    [model card](https://huggingface.co/Elpriser/denmark-price-forecast).
  - **Confirmed.**
  - The card's "These figures are a **floor**" is explained there: the backtest "deliberately
    uses a weather-forecast lead at least as old as the operational run would see". In other
    words, the provider presents the backtest as conservative. The live 3-week error (next item)
    is nonetheless 1.5–1.9× the backtest.
- **The note's 3-week live error table.** Re-ran `analyse.py`.
  - **With actuals through 2026-10-27, it reproduces the note exactly.** DK1 D+2..D+9 MAE is
    227–357, and DK1 bias runs from −12 to +42 (the note's "−55 to +42" includes D+3's −55).
  - **With actuals through 2026-10-29, which adds two high-price days (DK1 daily means 1,558 and
    2,224):**
    - DK1 D+2 MAE: 227 → **284**; D+9: 357 → **419**.
    - DK1 bias: **−62 to −122** for every horizon.
    - DK2 bias: −116..−175 → **−197..−269**.
    - P10–P90 coverage in DK2 falls to 65–75 %.
  - Data: [archive](https://elpriser.org/api/openapi.json),
    [DayAheadPrices](https://api.energidataservice.dk/dataset/DayAheadPrices).
  - **Confirmed as computed; too fragile to carry any number.**
- **Trend hit rates.** Re-ran `pt.py`. It reproduces the note exactly (DK1 73 / 81 / 100 / 74 /
  89 / 82 %, PT 2.24–4.59; n = 17–22). Each n counts runs issued on consecutive days whose
  D+2..D+9 windows overlap, so the independent evidence is about three weeks of prices. The note
  itself says the PT test assumes an independence the data lack. **Confirmed as computed,
  overstated as evidence.** "100 % at D+4" is 20 overlapping calls in one October.
- **"Ranking with a small markup beats a trend switch".** Re-ran `sim.py`. It reproduces the
  note's table exactly (for example DK1, 50 kWh: floor 718, oracle 358, P = 0 372, trend
  switch 434). Code inspection shows:
  - The "trend switch" is the note's own design: fill to capacity (or 3 days' worth) when the
    forecast mean of D+2..D+6 exceeds D+1. The maintainer's actual rule was not available to
    implement. Only the coarse version was tested against the planner-style rule.
  - In DK1, premiums of 100, 150 and 200 give identical results (386 DKK/MWh). In DK2, 0 and 50
    are identical. 23 decisions cannot resolve the premium.
  - The oracle is "wait for the next cheaper day", not the true optimum.
  - Prices are spot only, as the cheapest 2 hours of each day, with no targets or absences.
  - **Overstated.** It shows that fill-to-max is worse than next-cheaper in one month. It does
    not establish a markup of 0.05–0.10 DKK/kWh.
- **Optimizer's curse, 114–158 DKK/MWh.** Re-ran `analyse2.py`.
  - Actuals through 10-27 reproduce DK1 +114..+158 and DK2 +196..+277.
  - Actuals through 10-29 give **DK1 +184..+224** and **DK2 +257..+343**.
  - In the longer sample the overall DK1 level bias (forecast − actual) is −62..−122. Roughly
    half of the "curse" is therefore a plain under-forecast of the whole period, not selection.
  - The code takes the 4 cheapest hours **within every forecast day**, chosen or not. It does
    not measure the bias of the days a planner would choose to wait for, which is what the D20
    markup governs.
  - **Misread as a selection effect, and unstable.** The derived "≈0.12–0.16 DKK/kWh" and
    "λ ≈ 0.2–0.3" are not supported.

**Algorithm (scheduling_algorithm.md)**

- **"D22 as written": median +7.6 %, p90 +52 %, max +63 %.** Re-ran `exp3.py` (CONST, NONNEG,
  60 weeks) on the [Elspotprices](https://api.energidataservice.dk/dataset/Elspotprices) data.
  - Result: median 7.55, p90 52.29, max 63.15 %; absolute max 1.775 EUR/week. **Reproduced.**
  - Code inspection of `model.py`:
    - The selection loop (`greedy_d22`, `incremental=False`) matches motor.md §6.2: cheapest slot
      first, given to the earliest target still short whose deadline it precedes, until every
      floor is met.
    - The entire gap comes from `trim="chrono"`, which shrinks the latest selected slots first.
    - With `trim="price"`, the same selection has a gap of 0 in 60 of 60 weeks.
  - motor.md §6.2 does not say how the overshoot of the last whole hour is removed, and O9
    leaves `SET_CHARGE_LIMIT` open — [motor.md](../../motor.md), [decisions.md](../../decisions.md).
  - "Chronological trim" is one plausible reading: a charge limit cutting the charge in time
    order. It is not what the text says.
  - **Overstated: the label "as written" is an interpretation.**
- **Spot-only bias in the same experiment.** Recomputed: `exp3.py` copied with a Danish price
  added to every hour.
  - The added price is the Radius winter tariff (0.106 / 0.319 / 0.956) plus the 2026 flat part
    (0.123 DKK/kWh), converted at 7.46 DKK/EUR.
  - Applied all year to 2025 spot. This is a stylised test, not a real 2025 bill.
  - Results:

    | Run | Median gap | p90 | Max | Absolute gap |
    |---|---|---|---|---|
    | "cum + chrono" (constant power) | **2.25 %** | 20.3 % | **29.9 %** | median 0.147, max 2.236 EUR/week (unchanged) |
    | "cum + price" (constant power) | 0 | — | — | — |
    | "cum + price" (taper) | 0.07 % | 2.14 % | 7.05 % | max 0.42 EUR/week |

  - The relative figures in the note are inflated about 3× because the price excludes the
    tariff.
- **Negative prices contradict O1 "never".** Re-ran with taper and unclipped spot. "cum + price"
  floors-only had a median gap of 0.47 %, p90 8.91 % and max 48.35 % (0.862 EUR/week).
  **Reproduced.**
  - On the Danish total price, negative hours occur in 2 quarter hours a year in DK1 and never in
    DK2 (above). In the tariff variant the negative-price gap disappears; the remaining maximum
    of 7.05 % is the taper.
  - **Misapplied to Denmark.** The note itself flags "rarely negative … unmeasured"; the
    measurement now exists.
- **DP timings.** Re-timed `dp_energy_fast` on this container:
  - 168 × 1 h: 5.8 ms (0.5 kWh grid), 9.8 ms with the start state.
  - 672 × 15 min: 22.3 ms and 37.1 ms.
  - 0.25 kWh grid: 12.1 / 42.8 ms.

  **Confirmed** on this CPU, within a few ms. Home Assistant hardware was not measured, and
  backtracking time was not measured.
- **Test instances** (code of `exp3.py`):
  - weekday commutes using 6–20 kWh, with a floor of at least 30 kWh at 07:00;
  - one long trip of 30–50 kWh;
  - 168 hours of **perfectly known** 2025 hourly spot prices.

  A real call sees about 11–35 h of published prices
  ([DayAheadPrices metadata](https://api.energidataservice.dk/meta/dataset/DayAheadPrices),
  "between 13:00 and 14:00 CET"). The energy per day is larger than the 5–7.5 kWh/night in the
  composition note. **The biases are real and only partly acknowledged.** Reasoning: a shorter
  known horizon gives a greedy fewer slots to mis-trim, so the gaps probably shrink; this is
  unmeasured.

**Physics (charging_physics_battery.md)**

- **Kia e-Niro efficiencies.** Re-opened in the PDF: three-phase 87.21 / 86.98 %, single-phase
  80.32 / 79.58 %, and "almost constant at 6.9 kW" —
  [Reick et al. 2021](https://arbor.bfh.ch/bitstreams/67fb6c67-ed54-4535-a0fb-f43b55a2a3f5/download).
  **Confirmed**, for one car at 21–23 °C.
- **ADAC.**
  - 2026 test: "Verluste bei allen fünf Fahrzeugen unter sieben Prozent" at an 11/22 kW wallbox,
    and 9.1–12.8 % at reduced power —
    [firmenauto.de](https://www.firmenauto.de/management/fuhrparkmanagement/e-auto-ladeverluste-adac-vergleich-steckdose-wallbox-fuenf-elektroautos/).
  - 2022 test: ID.3 13.6 % at a household socket. ADAC "beziffert" the control-electronics draw
    at "100 bis 300 Watt", which is an estimate, not a measurement —
    [autohaus.de](https://www.autohaus.de/nachrichten/autohandel/adac-test-stromverluste-durch-schnellladen-vermeiden-3231295).
  - **Confirmed.** The `P_aux` model built on them is reasoning, and the note labels it so.
- **11 → 7.5 kW explained as a phase drop.** Only forum anecdotes and arithmetic. No measurement
  on the maintainer's car exists in any note. **Unsupported as an explanation; correctly
  labelled as a hypothesis.**
- **Keil et al. 2016.**
  - The mediaTUM PDF returned a bot-check page. I re-opened the abstract on the
    [IOP article page](https://iopscience.iop.org/article/10.1149/2.0411609jes) through a fetch
    tool.
  - Found there: plateaus "covering SoC intervals of more than 20%–30%"; "a marked step … at
    about 60% SoC for the NCA and NMC cells"; "substantially accelerated capacity fade … NMC cells
    at 100% SoC".
  - The NMC cell is a Sanyo UR18650E (2.05 Ah), tested at 25, 40 and 50 °C for 9–10 months.
  - **Text confirmed. The by-eye Fig. 2b values could not be re-opened** (bot block). The
    transfer to an Enyaq at Danish temperatures is **overstated** (section 3).

**Home Assistant (home_assistant_data.md)**

- **Core Škoda.**
  - "The integration is read-only. It reports the charging state … but cannot start, stop, or
    schedule charging." "The Škoda device was introduced in Home Assistant 2026.11, and it's used
    by 0 active installations" —
    [HA next docs](https://next.home-assistant.io/integrations/skoda/).
  - Code: `_PLATFORMS: list[Platform] = [Platform.SENSOR]`
    ([__init__.py](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/skoda/__init__.py)),
    `UPDATE_INTERVAL = timedelta(minutes=5)`
    ([coordinator.py](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/skoda/coordinator.py)),
    and manifest `"quality_scale": "bronze"`, `skoda-public-api==1.3.0`.
  - `carCapturedTimestamp` is used only for auxiliary heating in
    [sensor.py](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/skoda/sensor.py).
  - **Confirmed.**
- **Škoda API.**
  - "Requests are rate-limited per VIN. The current limit is 20 requests per hour; this value is
    not final and may change." Errors count against the quota —
    [docs](https://public.api.connect.skoda-auto.cz/docs).
  - The OpenAPI paths are vehicle status, charging start/stop/limit/mode/profiles and climate.
    There is **no wake or refresh path** —
    [OpenAPI](https://public.api.connect.skoda-auto.cz/v3/api-docs).
  - **Confirmed.**
- **MySkoda.** The README says "This integration will stop working in October 2026" and "The new
  integration is expected to ship with Home Assistant 2026.10" —
  [README](https://raw.githubusercontent.com/skodaconnect/homeassistant-myskoda/main/README.md).
  - The announcement is confirmed. Whether it has actually stopped working **could not be
    re-opened**: GitHub's issue and release pages and its API returned 403 in this session.
  - The README's "2026.10" is contradicted by core's "introduced in 2026.11". The core page is the
    primary source.
- **Zaptec.** "Many EVs don't like getting too frequent changes to the available charge current.
  Zaptec recommends not changing the values more often than every 15 minutes" —
  [README](https://raw.githubusercontent.com/custom-components/zaptec/master/README.md).
  **Confirmed, with a scope warning.** The rule concerns the installation's available current,
  not start/stop. The HA note's D10 row lists it as a general rate budget.
- **Easee.** "polling the API too often usually leads to being locked out for a time period", and
  no more than 5 sites —
  [wiki](https://raw.githubusercontent.com/wiki/nordicopen/easee_hass/UpdateFrequency.md),
  [wiki: Limits](https://raw.githubusercontent.com/wiki/nordicopen/easee_hass/Limits.md).
  **Confirmed as a community-wiki statement.** No official figure exists.

**Driver behaviour (driver_behaviour_ux.md)**

- **Electric Nation.** Re-opened (PDF text):
  - "18,282 transactions took place in Trial 2, of which 782 had an associated" high-priority
    request.
  - "11,305 charging events took place, with 282 high priority requests (2.5%). 80 of 237".
  - "approximately 20% of participants were responsible for 90% of high" priority requests.
  - The main reason was charge "for another journey (either later the same day, or a long journey
    the day after)".
  - Source: [Final Report](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378).
  - **Confirmed.** The transfer to Denmark is unsupported (section 3).
- **Ziras et al. 2024.** Re-opened (PDF text):
  - The gap is defined as "the time difference between two sessions' plug-in time": "40% of the
    sessions are fewer than 24 h apart, 70% fewer than 48 h apart and 85% 72 h apart".
  - Elsewhere the paper notes "a large density peak occurs at 24 h, revealing a recurrent
    pattern".
  - It measures chargers, not cars ("at least 10 % of customers have two vehicles", per the
    driver note), from 5,534 residential Spirii chargers, 2021–2023.
  - Source: [Ziras et al.](https://backend.orbit.dtu.dk/ws/files/364983824/1-s2.0-S0378779624004425-main.pdf).
  - **The 40 % figure is confirmed. "Most cars do not plug in daily, 60 % more than a day apart"
    is misread.** A daily 17:00 plugger with normal jitter falls on both sides of exactly 24 h,
    and the distribution peaks there.
  - The paper's "capturing most of the economic benefit" is a single sentence with no number. It
    concerns delaying charging, "early enough to guarantee full charging, especially for PHEVs".
    The driver note drops "especially for PHEVs" and uses the sentence as evidence that Danes
    "fill up", against O1(a). **Misread.**
- **Franke's 20–25 % buffer.** "usually 20 to 25 percent of the available range resources of
  electric vehicles are lost as a psychological safety buffer" —
  [TU Chemnitz](https://www.tu-chemnitz.de/tu/pressestelle/aktuell/5618/en). **Confirmed as a
  press-release statement** about a MINI E trial with 79 users (per the driver note).

**Prior art (prior_art_software.md)**

- **evcc planner.**
  - `type Planner struct` and `func (t *Planner) Plan(...)`.
  - Rates "sorted in ascending order by cost and descending order by start time (prefer late
    slots)"; `sortByCost` breaks ties with `j.Start.Compare(i.Start)`.
  - Sources: [planner.go](https://raw.githubusercontent.com/evcc-io/evcc/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/planner/planner.go),
    [sort.go](https://raw.githubusercontent.com/evcc-io/evcc/9404d825d6a659d8ce7f47d3b0d2e14ac04506e0/core/planner/sort.go).
  - **Confirmed**: the planner is stateless and greedy. The loadpoint around it is stateful, as
    the note says.
- **evcc issues.**
  - #24339 "Repeating plans: charging stops on plan overrun": opened 2025-10-11, closed
    2026-02-01, closed by PR #26529. The maintainer quote "Prio 1 muss aber sein, dass der Planner
    das Ziel trifft" is there — [issue](https://github.com/evcc-io/evcc/issues/24339) (read
    through a fetch tool).
  - #34466: "A plan that needs less than 14m therefore always has a remaining time below the
    threshold and can never start". Fixed by PR #34604 on 2026-10-10; it refers to discussion
    #33936 — [issue](https://github.com/evcc-io/evcc/issues/34466).
  - **Confirmed.** Discussion #33936 itself was not opened (GitHub returned 403 to direct
    requests).
- **emhass.** `pyproject.toml` lists `highspy>=1.10.0` and `cvxpy>=1.6.0, <1.8.0`.
  `optimization.py` has `import cvxpy as cp` and `self.lp_solver = "Highs"  # Default to Highs for
  speed` — [pyproject](https://raw.githubusercontent.com/davidusb-geek/emhass/179cbc2b584bd935c96ad679ec4f32f496f412fb/pyproject.toml),
  [optimization.py](https://raw.githubusercontent.com/davidusb-geek/emhass/179cbc2b584bd935c96ad679ec4f32f496f412fb/src/emhass/optimization.py).
  **Confirmed.**

### Inferences
- Reasoning: the sources were read honestly. Every number I could re-open matched. The weak
  points are the interpretation layer and the samples. The two most-cited quantitative "findings"
  that would move decisions are both artefacts of setup:
  - D22's 63 % comes from the trim rule plus spot-only prices.
  - The 114–158 DKK/MWh bias comes from a 3-week sample and within-day selection.
- Reasoning: on the savings figure, the decision-relevant number is the gain over what a Danish
  household already does with a charger timer. That is ≈470–630 DKK/yr. It is a modest return,
  and it is captured almost entirely by ranking on the total price within tonight's known prices.
  Nothing in the notes shows that forecasts, multi-target chaining or a DP add a measurable
  amount on top of it for a typical Danish commuter.

### Gaps
- The by-eye values from Keil Fig. 2b: PDF blocked by a bot check.
- MySkoda's real shutdown status, and evcc discussion #33936: GitHub blocked.
- The script behind the composition note's 393-night table does not exist in the repository. My
  recomputation agrees with its output, so this is a reproducibility gap, not an error.

## 2. Where do the notes contradict each other, and which side is right?

### Takeaway
Six notes give five different answers to O1. None of them rests on Danish measurements of what
charging beyond the floors is worth. The negative-price argument fails for Danish total prices.
The behavioural argument misreads Ziras. The battery argument over-transfers Keil. The forecast
argument rests on 23 decisions. The other contradictions can be settled from the sources.

### Cited Findings
- **O1, charge beyond the floors.**

  | Note | Position |
  |---|---|
  | Physics | (a) never |
  | Scheduling | (a) contradicted by negative prices |
  | Forecast | a "next-cheaper day" rule |
  | Driver | (c) percentile or (b) threshold |
  | Composition | (c) percentile |
  | Prior art | (b) user threshold |

  The measured facts that bear on this:
  - The Danish total price is negative in 2 quarter hours a year (DK1) and never in DK2
    (recomputed, section 1).
  - With tariffs in the price, the negative-price loss of floors-only disappears in Exp 3
    (recomputed).
  - Ziras does not show "filling up" (re-opened, section 1).
  - Keil's step is at about 60 % *cell* SoC in 18650 cells at 25–50 °C
    ([IOP](https://iopscience.iop.org/article/10.1149/2.0411609jes)).
- **Forecast markup basis.** The composition note says the markup should apply to the spot part
  only, or be absolute. The forecast note says additive in price units. They **agree**, and both
  are reasoning on a measured fact: the tariff and tax parts are known months ahead in DataHub
  ([DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist), re-opened rows
  run to 2028).
- **Markup size.** Within the forecast note, the figure goes from 0.12–0.16 DKK/kWh (section 5) to
  0.05–0.10 (section 7). My re-run with two more days puts the "bias" at 0.18–0.22 (DK1) (section
  1). **No side is right.** The data cannot set this number.
- **O11, 15-minute slots.**
  - The HA and prior-art notes call the hourly assumption "contradicted" and "behind the prior
    art".
  - The composition note measured that choosing quarters rather than hours is worth ≈45–75
    DKK/yr, and only to households on a quarter-hour product. Default products bill the simple
    hourly average ([Tænk](https://taenk.dk/forbrugerliv/bolig/flere-elpriser-i-doegnet-giver-minimale-besparelser)).
  - **The composition note is right on the money:** O11 matters for correctness of the input
    contract, not for savings.
- **Tie-break and timing.**
  - The physics and prior-art notes favour the latest equal-price slot (wear, evcc).
  - The driver note argues a plan that starts at 03:00 "looks like nothing is happening" and that
    an early margin reduces overrides.
  - Both are **reasoning**. No source measures either effect.
- **MySkoda.** The HACS README says core ships in 2026.10; core docs say 2026.11. **Core docs are
  right** (re-opened).
- **Scripts.** The forecast note says "The scripts were throwaway and are not kept".
  `experiments/prices/README.md` says they are kept, and they are; I re-ran them. The note's
  method line is stale.
- **Performance budget.** The composition note (672 quarter-hour points) and the scheduling note
  (DP at 22–37 ms for 672 slots, re-timed) together show that motor.md §7's 10 ms budget cannot
  hold for quarter-hour input in pure CPython. The notes do not contradict each other here; the
  budget is contradicted by both.

### Inferences
- Reasoning on O1: the only measured quantity is the composition note's tariff structure. Night
  hours are systematically cheaper (timer saves 600–1,100 DKK/yr against plug-in at 17:00,
  recomputed). That favours a rule tied to the night block or a percentile. It says nothing about
  how much extra SoC to buy. O1 is a value judgement (availability against wear against a few
  hundred DKK), and the notes should not present it as evidence-settled in any direction.
- Reasoning on the tie-break: "latest equal slot" and an "early visible start" can coexist. The
  integration can show "next charge starts 03:00" (the driver note's own fix) without moving the
  plan.

### Gaps
- No note measured the monetary value of charging beyond the floors on Danish total prices with a
  real schedule. This could be done with the existing DP plus a terminal value.

## 3. Which recommendations rest on reasoning alone but read as if measured?

### Takeaway
Six recommendations carry numbers that look measured but are reasoning or tiny-sample
arithmetic:

1. the forecast premium of 0.05–0.10 DKK/kWh;
2. "0.7 %/yr extra fade, same order as the fleet's 1.5 %/yr";
3. "D22 contradicted as written";
4. "most cars do not plug in daily";
5. default floors and arrival SoC (labelled as reasoning, but tabled beside cited evidence);
6. "60–65 % / most of the benefit is already captured", which is my own figure on stylised
   assumptions and should be read the same way.

### Cited Findings
- **Forecast premium "≈0.05–0.10 DKK/kWh, 0.3–0.6× first-day MAE".**
  - It comes from `sim.py`, where DK1 premiums of 100–200 give identical results (re-ran).
  - The "first-day MAE" it scales by is the 149 DKK/MWh backtest
    ([OpenAPI](https://elpriser.org/api/openapi.json)), while the live error was 227–284 (re-ran).
  - The note does say "not a calibrated result". Its section 6 Takeaway still states the band as
    a revision.
- **Battery wear "≈0.7 %/yr upper bound … same order as the fleet's 1.5 %/yr".**
  - Arithmetic on by-eye figure values, at 25 °C, for a 2.05 Ah 18650 NMC cell
    ([IOP](https://iopscience.iop.org/article/10.1149/2.0411609jes)).
  - It assumes the car sits above the step for 6 extra hours a night. The scheduling experiments'
    own commuter floors are 30 kWh of 75 (40 %), below Keil's ~60 % step.
  - Danish night temperatures (the note's own −5..+5 °C) are far below 25 °C.
  - The 1.5 %/yr fleet figure comes through a news article on Geotab, which I did not re-open.
- **"Electric Nation's 2.5 % is a floor estimate for Danish cars".** Reasoning.
  - The trial managed charging by cutting current under network control, in 2017–2019
    ([Final Report](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)).
  - A price planner that shifts a whole charge to 03:00 is a different intervention. The
    direction of the transfer is unknown.
- **`default_arrival_soc` 20 % from Franke's 20–25 %.**
  - Franke's buffer is range people do not use when planning trips
    ([TU Chemnitz](https://www.tu-chemnitz.de/tu/pressestelle/aktuell/5618/en)).
  - Mapping it to SoC on return is reasoning. The note labels it so, but the verdict column says
    "partly contradicted".
- **"D22: contradicted as written"** (scheduling note §7 table). This rests on an implementation
  choice motor.md does not make (section 1). By contrast, "the matroid argument makes the
  increment greedy exact" is derived and verified (0 of 4,000 in Exp 1, per the note). I did not
  re-run Exp 1.

### Inferences
- Reasoning: the report writer should carry these as hypotheses with the test that would settle
  each, not as findings. In each case the test is cheap and named in section 4.

### Gaps
- I did not re-run Exp 1 or Exp 2 (synthetic instances), or the networkx timing (Exp 6).

## 4. What is missing entirely that a decision needs?

### Takeaway
The decisions most exposed to missing data are O1, O4/D20, D16/D26 and O7. The cheapest source
for all of them is the maintainer's own Home Assistant history. None of the notes used it; the
forecast note states that "nothing was logged before this task".

### Cited Findings
- **Carnot accuracy.** No published accuracy. The API needs a personal key
  ([Carnot connector](https://github.com/MTrab/energidataservice/blob/master/custom_components/energidataservice/forecasts/carnot/__init__.py),
  per the forecast note; not re-opened by me). Carnot is the forecast the main Danish HA
  integration offers, and possibly the one behind the maintainer's trend experience.
- **Danish override data** for price-based control: none found by the driver note. Electric
  Nation is UK network-throttling data
  ([Final Report](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)).
- **Enyaq-specific physics.** No note has a measured Enyaq number: no AC power curve, efficiency,
  winter heating energy or standby drain (stated in the physics note's own Gaps).
- **The maintainer's context.** Unknown in every note:
  - his grid company, so which tariff;
  - his billing product (hourly or quarter-hour), which decides whether O11 is worth anything;
  - his charger brand (HA note: "unknown brand");
  - his actual nightly kWh and plug-in pattern.
- **An end-to-end test.** No note ran the actual engine logic on:
  - Danish total prices (2026 tariffs, quarter-hour);
  - a realistic known horizon (11–35 h) plus forecasts with markup;
  - a real schedule with targets and absences.

  Exp 3 uses 168 h of perfect hourly spot. `sim.py` has no schedule.
- **Forecast archive length.** The elpriser archive starts 2026-10-06 and keeps 400 days
  ([OpenAPI](https://elpriser.org/api/openapi.json)). A calibration over both seasons will be
  possible from about April 2027.

### Inferences
- Reasoning: logging in the integration before the engine exists would settle more than further
  desk research. The items to log:
  - per-phase current and SoC during sessions (D16, the 11 → 7.5 kW cause);
  - charger meter kWh against ΔSoC (D16/D26 efficiency);
  - the age of `carCapturedTimestamp` against HA `last_changed` (O7, `soc_max_age_minutes`);
  - every Carnot and elpriser forecast run (O4).
- Reasoning: re-run Exp 3 with a known horizon cut at 13:00 each day, forecasts beyond it, and
  2026 Danish total prices. That would show whether the DP-versus-fixed-greedy difference
  (≤0.42 EUR/week with tariffs, recomputed) matters at all once forecast error is present.

### Gaps
- Whether Tibber's `price_total` includes the DSO tariff in Denmark: open in the HA note, not
  checked by me.

## 5. Claim-by-claim verdicts and the decisions they affect

### Takeaway
Of 28 claims audited:

| Verdict | Count | Rows |
|---|---|---|
| Confirmed at source or by re-run | 14 | 1–5, 7, 13, 15, 17, 21, 22, 24, 25, 28 |
| Confirmed in part, the rest could not be re-opened | 2 | 19, 23 |
| Confirmed as computed but overstated as evidence | 4 | 6, 8, 9, 12 |
| Overstated | 3 | 10, 16, 20 |
| Misread | 3 | 11, 26, 27 |
| Reproduced but misapplied to Denmark | 1 | 14 |
| Unsupported | 1 | 18 |

The decisions most affected are D22 (the evidence for replacing it is weaker than stated), D20/O4
(no markup number is supported) and O1 (unsettled by evidence). D10, D13, D25 and the O7 lean
toward charging first are supported.

### Cited Findings
Sources for every row are in sections 1–3. "Re-ran" and "recomputed" refer to the data listed in
the method note at the top.

| # | Claim | Note | Verdict | Consequence for decisions |
|---|---|---|---|---|
| 1 | Elafgift 0.008 DKK/kWh for 2026–2027 | Price composition | **Confirmed** (skat.dk, DataHub EA-001) | D3: the price passed must be the total; the flat part is small, so the variable parts dominate the ranking |
| 2 | Tariff periods 00–06 / 06–17, 21–24 / 17–21; winter from 1 Oct; Radius and N1 rates | Price composition | **Confirmed** (Tænk, DataHub) | D13: the caller must compose the total price; O1 night-block rules are meaningful |
| 3 | 15-minute day-ahead since 2025-10-01 | Price composition, Forecast, HA | **Confirmed** (metadata). Minor misread: the first row is 00:00, not 00:15 | O11: the contract needs a slot duration |
| 4 | Default products bill the hourly average of quarters | Price composition | **Confirmed** (Tænk) | O11 is about correctness, not savings; HA and prior-art "contradicted" framing **overstated** |
| 5 | Negative total price nearly never (DK1 2 quarter hours, DK2 none) | Price composition | **Confirmed** (recomputed) | D25 stays (supported, rarely used); undercuts the negative-price argument against O1 (a) |
| 6 | Smart charging saves 1,400–3,000 DKK/yr | Price composition | **Arithmetic confirmed** (recomputed within 0.3 %); **overstated** as the engine's value: 466–634 DKK/yr against a midnight timer; headline script missing | Project value case; O1; whether forecasts are worth their complexity |
| 7 | elpriser backtest MAE 149 / 179 / 197; hit rate 69–70 % | Forecast | **Confirmed** (OpenAPI, model card); live error 1.5–1.9× higher | O4 scale |
| 8 | 3-week live MAE 227–357; DK1 near unbiased | Forecast | **Confirmed as computed**; adding two days: 284–419 and bias −62..−122 | O4: no calibration possible yet |
| 9 | Direction hit rates 73–100 % (DK1), 23 overlapping runs | Forecast | **Confirmed as computed, overstated as evidence** (n ≤ 22, overlapping, one month) | D20 keeps forecasts in the ranking: plausible, not established |
| 10 | Ranking with a small markup beats a trend switch | Forecast | **Overstated**: the switch is a coarse design of the note's own; 23 decisions; premiums 100–200 indistinguishable | D20, O1 (next-cheaper rule), O4 |
| 11 | Optimizer's curse 114–158 DKK/MWh → markup 0.12–0.16, then 0.05–0.10 DKK/kWh | Forecast | **Misread** (within-day selection, about half level bias) and **unstable** (184–224 with two more days) | O4: no default supported |
| 12 | D22 as written: median +7.6 %, max +63 % | Scheduling | **Reproduced but overstated**: comes only from an unspecified chronological trim; 0 % with price trim; 2.3 % / 30 % with Danish tariffs | D22 selection rule stands; specify the trim (O9); DP optional |
| 13 | Best greedy with taper: 0.01 / 1.9 / 5.4 % | Scheduling | **Confirmed**; with tariffs 0.07 / 2.1 / 7.1 %, ≤0.42 EUR/week | D12, D22: a DP gains little money; keep it as a test oracle |
| 14 | Negative prices contradict O1 (a) (up to 0.86 EUR/week) | Scheduling | **Reproduced on spot; misapplied to Denmark**: disappears on the total price | O1 |
| 15 | DP 5.7 ms (168 h), 21–35 ms (672 quarter hours) | Scheduling | **Confirmed** on this CPU (5.8 / 22.3 / 37.1 ms); HA hardware unmeasured | Motor §7 10 ms budget fails for quarter-hour slots; O8, O11 |
| 16 | Test instances representative | Scheduling | **Overstated**: synthetic commutes, 168 h perfect spot, 2025 hourly | D22, S4 |
| 17 | Efficiency 87 / 80 % (e-Niro); ADAC < 7 % at wallbox, 100–300 W aux | Physics | **Confirmed** (one car; aux is an ADAC estimate) | D16 / D26 overhead term: plausible, Enyaq unmeasured |
| 18 | 11 → 7.5 kW is probably a phase drop | Physics | **Unsupported** (forum anecdotes plus arithmetic; correctly labelled) | D16: log per-phase current before encoding the curve |
| 19 | Keil plateaus, step at ~60 %, NMC 100 % steep | Physics | **Confirmed** (abstract and text); **Fig. 2b values could not be re-opened** | D7 / 80 % default |
| 20 | "Just in time" saves ≈0.7 %/yr, same order as fleet fade; O1 (a) | Physics | **Overstated** transfer (18650 cell, 25 °C, assumes SoC above the step) | O1, the latest-slot tie-break |
| 21 | Core Škoda read-only, 2026.11, sensors only, 5-min poll | HA | **Confirmed** (docs, code, manifest) | O7 → charge first; WAKE / SET_CHARGE_LIMIT optional; D10 caller duties |
| 22 | Škoda API 20 requests/h per VIN, no wake endpoint | HA | **Confirmed** (docs, OpenAPI) | Refresh budgeting in the caller |
| 23 | MySkoda stops working in October 2026 | HA | Announcement **confirmed**; actual shutdown **could not re-open** (GitHub 403) | Adapter plan for the maintainer's car |
| 24 | Zaptec: no changes more often than every 15 min; Easee lockouts | HA | **Confirmed**; Zaptec's rule is about current changes, not start/stop; Easee's is a community-wiki statement | Caller hysteresis (D10) |
| 25 | Electric Nation overrides 4.2 % / 2.5 %; 20 % of users make 90 % | Driver | **Confirmed**; transfer to Danish price control **unsupported** | O12 (override as trust device), O1 |
| 26 | Ziras: 40 % re-plug within 24 h → most cars do not plug in daily | Driver | **Misread**: per charger, plug-in to plug-in, distribution peaks at 24 h | `idle_planning_horizon_hours`, `min_idle_soc` defaults |
| 27 | Ziras: Danes "fill up" and capture most of the benefit → O1 (a) contradicted | Driver | **Misread**: about delay timing, "especially for PHEVs", no number | O1 |
| 28 | evcc planner stateless and greedy; #24339, #34466; emhass cvxpy + HiGHS | Prior art | **Confirmed** (code at the pinned commits, issue pages, pyproject) | D10 (caller holds the state; test the caller hardest), D19 soft minimum |

### Inferences
- Reasoning: for D22, the defensible statement is narrower than any note's. motor.md's selection
  rule is exact for constant power when the partial slot is the most expensive one chosen. It is
  within about 2 % (p90) under a taper on Danish total prices. The open item is the trim rule
  (O9), not the algorithm family.
- Reasoning: for D20/O4, the defensible statement is about shape only. An additive markup, zero
  on published prices, with a step at the first forecast day: yes. Any default size: no, until a
  multi-season archive (elpriser from 2026-10-06, Carnot logged by the integration) has been
  scored on the cross-day decision itself.

### Gaps
- Claims not re-checked by me, which should be carried as the authors' own:
  - Lund thesis figures (λ = 0 near-optimal; 44–56 EUR/yr from multi-day forecasts);
  - Fernández-Zapico 13 % / 1 %;
  - Geotab 1.5 %/yr;
  - Will & Schuller percentages;
  - openWB, OpenEMS, EV Smart Charging and Predbat code details;
  - Exp 1 / 2 / 6.
