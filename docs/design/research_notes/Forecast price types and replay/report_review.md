# Independent review of "Cheapest home EV charging" (report of 2026-10-28)

Reviewer's position: a senior reviewer who had not seen the work before, on 2026-11-06. The report
under review is `docs/design/reports/Cheapest home EV charging.md`. Its evidence is the notes and
panel papers in `docs/design/research_notes/Cheapest home EV charging/`. The design it judges is
`docs/design/motor.md` and `docs/design/decisions.md`.

The maintainer: DK1, grid company N1, billed per hour (hourly price = simple mean of the four
quarter prices), Škoda Enyaq, home AC charger. He uses the Carnot forecast through the Energi Data
Service (EDS) integration and finds it always lower than the outcome but right on trend.

Method and labels:
- **Opened**: I fetched the page, dataset or source file myself on 2026-11-06.
- **Re-ran**: my own code on data I downloaded today. The scripts are in
  `experiments/report_review/` beside this note.
- **Note §x**: checked against the cited note's text only.
- **Reasoning**: my own argument, not a sourced fact.
- **Not found**: searched and not found, or the source refused me.
- Not done, by instruction:
  - Carnot's API was not called.
  - Forecast bias and price types, and the end-to-end replay, belong to two parallel researchers
    and are not simulated here.

Sources opened for this review:
- **The EDS integration**, cloned at commit `4b4085d` (2026-10-25, v1.6.22):
  - [sensor.py](https://github.com/MTrab/energidataservice/blob/4b4085d004c5c3721258e7802b88b05d441e2670/custom_components/energidataservice/sensor.py)
  - [api.py](https://github.com/MTrab/energidataservice/blob/4b4085d004c5c3721258e7802b88b05d441e2670/custom_components/energidataservice/api.py)
  - [__init__.py](https://github.com/MTrab/energidataservice/blob/4b4085d004c5c3721258e7802b88b05d441e2670/custom_components/energidataservice/__init__.py)
  - [tariffs/energidataservice/__init__.py](https://github.com/MTrab/energidataservice/blob/4b4085d004c5c3721258e7802b88b05d441e2670/custom_components/energidataservice/tariffs/energidataservice/__init__.py)
  - [chargeowners.py](https://github.com/MTrab/energidataservice/blob/4b4085d004c5c3721258e7802b88b05d441e2670/custom_components/energidataservice/tariffs/energidataservice/chargeowners.py)
  - [connectors/energidataservice/__init__.py](https://github.com/MTrab/energidataservice/blob/4b4085d004c5c3721258e7802b88b05d441e2670/custom_components/energidataservice/connectors/energidataservice/__init__.py)
  - [forecasts/carnot/__init__.py](https://github.com/MTrab/energidataservice/blob/4b4085d004c5c3721258e7802b88b05d441e2670/custom_components/energidataservice/forecasts/carnot/__init__.py)
  - the commit history, searched with `git log -S`.
- **Energi Data Service API**:
  - [DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist): all N1 rows for
    GLN 5790001089030, and all `Nettarif C`, `Nettarif C time`, elafgift, Systemtarif and
    Transmissions nettarif rows (1,494 rows).
  - [DayAheadPrices](https://api.energidataservice.dk/dataset/DayAheadPrices): DK1, 2025-10-01
    00:00 to 2026-11-06 23:45 Danish time (38,596 quarter rows).
- **N1's press release** of 1 Oct 2026
  ([Ritzau](https://via.ritzau.dk/pressemeddelelse/15176319/n1-overgar-til-vintertariffer-1-oktober-brug-strommen-uden-for-myldretiden-og-fa-en-billigere-elregning?lang=da)).
- **Nord Pool's operational message** of 17 May 2026
  ([Nord Pool](https://www.nordpoolgroup.com/en/trading/Operational-Message-List/2026/05/sdac_exc_03b-further-delay-of-the-market-coupling-session-20260517115000/)).
- N1's own tariff page returned HTTP 403 and was not opened.

Notes cited (relative to this folder):
- price note: `../Cheapest home EV charging/price_composition_denmark.md`
- forecast note: `../Cheapest home EV charging/price_forecast_uncertainty.md`
- HA note: `../Cheapest home EV charging/home_assistant_data.md`
- economist: `../Cheapest home EV charging/panel_market_economist.md`
- optimisation note: `../Cheapest home EV charging/panel_optimisation_engineer.md`
- battery note: `../Cheapest home EV charging/panel_battery_engineer.md`
- control/UX note: `../Cheapest home EV charging/panel_control_ux_engineer.md`
- red team: `../Cheapest home EV charging/panel_red_team.md`

## 1. Does each headline claim follow from the notes and panel papers it cites, with their caveats?

### Takeaway
The factual backbone holds. Every tariff, tax and negative-price number I re-queried in DataHub
matches, and I reproduced the price note's 2026 savings table to the krone.

What does not hold is the money framing for this maintainer. Every savings figure was computed for
**quarter-hour billing**, but he is billed per hour. On his billing:
- the midnight timer is worth more: about 1,090 DKK/yr, not 730;
- ranking tonight's total prices is worth less: about 410 DKK/yr, not 470–630.

The report also has a handful of mismatched numbers, one dead measurement (recorder history of the
Carnot forecast), and summary counts that do not match its own register.

### Cited Findings

**Spot-checks (22 numbers).** ✓ means it matches; ✗ means it does not match or does not follow.

| # | Report claim | Check | Result |
|---|---|---|---|
| 1 | Elafgift is 0.008 DKK/kWh for 2026–27 | DataHub `EA-001`: 0.008, 2026-01-01 → 2028-01-01, VAT class D02 (opened) | ✓ |
| 2 | Energinet is 0.115 DKK/kWh in 2026 (0.105 in 2027, in the note) | DataHub: Systemtarif 0.072 + Transmissions nettarif 0.043 in 2026; 0.049 + 0.056 in 2027 (opened) | ✓ |
| 3 | Radius winter rates 0.106 / 0.319 / 0.956 excl. VAT | DataHub `DT_C_01`, 2026-10-01 → 2027-01-01: 0.106175 / 0.318524 / 0.955573 (opened) | ✓ |
| 4 | Night-to-peak swing 1.06 DKK/kWh incl. VAT | (0.9556 − 0.1062) × 1.25 = 1.062 | ✓, but it is Radius (DK2), not N1 |
| 5 | N1 winter rates 0.088 / 0.264 / 0.791 | DataHub `CD`: 0.087854 / 0.263563 / 0.79069 (opened). N1's press release gives 11 / 33 / 99 øre incl. VAT, winter "oktober 2026 – marts 2027" | ✓ |
| 6 | Price note's 2026 table: plug-in at 17:00 3,836, timer 3,106, smart 2,487, spot-ranked 2,672 DKK/yr (DK1) | Re-ran on quarter billing, 301 nights (2026-01-01 to 10-28) scaled to a year. With N1's DataHub rows: 3,836 / 3,106 / 2,487 / 2,672. With the note's hardcoded tariff: 3,837 / 3,107 / 2,488 / 2,673 | ✓ exactly |
| 7 | Headline: the timer "is worth about 600–1,100 DKK a year" | The report's own table and the price note give about 730 (DK1) to 1,090 (DK2). "600–1,100" comes from the red team's summary row | ✗ minor: the lower bound is unsupported |
| 8 | Ranking tonight's totals adds 470–630 DKK/yr | Red team: 466–634. Price note: 619 (DK1), 578 (DK2). All on quarter billing | ✓ as computed; ✗ for hourly billing |
| 9 | Ranking on spot alone loses 185–217 DKK/yr | 2,672 − 2,487 = 185; 2,768 − 2,551 = 217; re-ran | ✓ (quarter billing) |
| 10 | The cheapest spot quarter falls outside 00–06 on about 70 % of nights | Price note: 218/301 and 204/301 | ✓ (not re-run) |
| 11 | Median daily spread 1.62 (DK1) / 1.72 (DK2) | Price note §5 | ✓ (not re-run) |
| 12 | Spot negative in 2.5 % of DK1 quarters | Re-ran: 951 of 37,828 = 2.51 % | ✓ |
| 13 | Total price negative in 2 DK1 quarters, minimum −0.075 | Re-ran with N1's DataHub rows by date: 2 quarters, minimum −0.075 | ✓ |
| 14 | 6.3 % of DK1 hours negative in 2025 (spot) | Red team: 411 of 6,551 | ✓ |
| 15 | elpriser.org backtest MAE 149 / 179 / 197 DKK/MWh, 23–32 % of the mean price | Red team's quote | ✓ |
| 16 | Register row S1: "MAE is 23–38 % of the mean" | 35–38 % is the naive baseline's share, not the forecast's | ✗ minor |
| 17 | Live error 227–357, then 284–419 DKK/MWh | Red team §1 | ✓ |
| 18 | E5: chained daily targets 66–78 %, flat value 4–47 %, percentile −5 to −30 % | Optimisation note, lines 463–465 | ✓ |
| 19 | Direction right 73–100 % / 59–90 %, cheapest day picked 50–71 %, Spearman 0.7–0.8 | Forecast note §7; optimisation note, line 474 | ✓ |
| 20 | DP timings 13 / 26 / 41 / 100 ms; session starts 3.0 → 1.2 for +0.19 % | Optimisation note | ✓ |
| 21 | Battery: 1,000–3,700 DKK per point; 0.5–1.5 points a year; 5.5 DKK a day; 500–5,500 DKK/yr | Battery note (500–5,550) | ✓ |
| 22 | 51 minutes late; at most 12 DKK for "charge first" | Control/UX note | ✓ |

**The maintainer's own numbers, on hourly billing** (re-ran). Assumptions: N1 area 131's DataHub
rows by date, 2026 flat parts of 0.123 DKK/kWh, × 1.25 VAT, no supplier markup, plugged in
17:00–07:00 every night, 301 nights scaled to a year, the cheapest **hours** by total price billed
at the hour's mean. Figures are DKK per year.

| Case | Plug-in at 17:00 | Timer at 00:00 | Smart by total | Smart by spot | Timer's value | Ranking's value over the timer | Loss from ranking on spot |
|---|---|---|---|---|---|---|---|
| 6 kWh a night, 11 kW | 4,119 | 3,033 | 2,622 | 2,775 | 1,087 | **411** | 154 |
| 6 kWh a night, 3.7 kW | 4,345 | 2,991 | 2,673 | 2,792 | 1,354 | 317 | 119 |
| 15 kWh a night, 11 kW | 10,690 | 7,508 | 6,643 | 6,967 | 3,182 | 865 | 324 |

**Why hourly billing moves the numbers: the ramp inside the hour.** In DK1 in 2026, the four
quarters of 17:00–18:00 averaged 0.681 / 0.810 / 0.921 / 1.042 DKK/kWh spot (re-ran, 301 days). A
33-minute charge from 17:00 pays the first quarters on a quarter-hour product, but the hour's mean
on an hourly product. The price note's "a couple of øre" between quarters holds on average, but not
in the ramp hours.

**Other overstatements and mismatches in the report text:**
- **"The facts were re-opened and hold."** Two facts were never re-opened:
  - whether the EDS Carnot forecast carries tariffs (the HA note lists it as a gap, and the
    economist calls it "unverified");
  - whether the forecast attribute is recorded.
  Section 2 answers both.
- **The recorder measurement is dead.** The report asks for his past Carnot forecasts from the
  recorder, "now, if the data exist". EDS excludes `ATTR_FORECAST` from the recorder through
  `_unrecorded_attributes`. This came in commit `966dbab` of 2025-09-13, "Do not record large
  datasets in attributes Fixes #803" (git history, opened). Since then no history exists.
- **Summary counts do not match the register.**
  - The summary lists D16, D19, D20, D22, D26 and D28 as "change"; the register also marks L1, L4
    and O10 "change".
  - Of the "answered" list, the register also answers O5, S2 and S4, and S1 and S3 in part, while
    O4 is answered for its shape only.
- **The headline swing is not the maintainer's.** The report uses Radius (DK2). N1's winter swing
  is (0.7907 − 0.0879) × 1.25 = **0.88 DKK/kWh incl. VAT** now, and **0.98** from 2027-01-01.
- **motor.md is misquoted.** "as motor.md §6.2 now says" states the opposite of motor.md: §6.2
  takes hours "within the price data", and §6.1 step 5 stops at "end of price data".
- **The default markup is more precise than its evidence.** The integration default of 0.08
  DKK/kWh (0.10 from D+4) rests on 21–23 overlapping decisions with elpriser.org's forecast, not
  Carnot. The report labels it uncalibrated, which is right.
- **"High" confidence is stated without the billing basis.** The 470–630 DKK figure is right as
  arithmetic but assumes quarter billing, while N2 recommends hourly slots for hourly-billed
  households.

### Inferences
- Reasoning: hourly billing strengthens the report's central message. The timer captures 1,087 of
  1,497 DKK/yr. What the engine adds on top falls to about 410. The case for putting effort into the
  price adapter rather than the optimiser is stronger for this maintainer.
- Reasoning: a slow charger gains less from ranking (317 DKK/yr at 3.7 kW). It has to use more of
  the night, so it has less choice.

### Gaps
- The price note's 393-night headline table still has no script. I did not recompute it.
- The elpriser.org figures were checked only against the red team's quote, not re-opened.
- The O1 oracle and E5 were not re-run; that is the parallel replay researcher's task.

## 2. The price calculation end to end: where can it rank hours wrongly for this maintainer?

### Takeaway
With tariffs and VAT switched on, EDS puts known and forecast prices on the **same basis**. Carnot
delivers spot only, and EDS adds the dated grid tariff, Energinet, elafgift, the user's markup
template and VAT to every forecast hour. So the report's "false price cliff" does not occur with
EDS.

Nine other mechanisms can still give the wrong best hour, and three are specific to N1:
- EDS's single "N1" choice is N1's grid area 131 only.
- N1's published 2027 rows move the season boundaries and shift the tariff periods by one hour in
  spring 2027.
- EDS silently uses a grid tariff of 0 when no DataHub row covers a date.

### Cited Findings

**How EDS composes the price** (opened, commit `4b4085d`):
- **Spot.** It reads `DayAheadPrices` in EUR, from yesterday to two days ahead (UTC), and converts
  to the user's currency.
- **Hourly mode** (option `resolution`, default `True`). It averages the quarters in consecutive
  groups of four **by position**, not by timestamp. One missing or duplicated quarter would
  misalign every later hour. Re-ran: DK1 has no gap or irregular step from 2025-10-01 to
  2026-11-06, so this has not happened yet.
- **The composition.** Every price, known or forecast, goes through `_calculate`: (spot/unit +
  template + system tariffs for that date + the charge owner's tariff for `fake_dt.hour`) × (1 +
  VAT). The tariff is looked up by the slot's **local** date and clock hour. The template is
  rendered with the slot's time, so a time-varying markup is possible. It is added before VAT.
- **Carnot.** The request is `energysource=spotprice&daysahead=7`, in DKK per MWh. Today's entries
  are dropped, and tomorrow's once tomorrow's real prices are valid. The forecast goes through the
  same `_calculate`, so it carries tariffs and VAT whenever the known prices do.
- **Silent zero tariff.** When no row covers a date, `get_dated_tariff` returns `{}`. The code then
  sets `owner_tariff = ... if chargeowner_tariff else 0`, with no warning. The "empty tariff
  dataset" warning fires only when the whole dataset is empty.
- **Overlapping rows are summed.** For N1 that is intended, because EDS fetches both `CD` and
  `CD R` ("Rabat på nettarif N1 A/S"). N1 has used `CD R` for rebates that vary by hour: −0.408 /
  −1.016 DKK/kWh in December 2022, and −0.220 / −0.617 in Q4 2023. No `CD R` row is valid after
  2025-03-01.
- **Update timing.**
  - Tomorrow's spot is fetched at 13:xx local, at a random minute, and retried every quarter from
    14:00 if missing.
  - Tariffs are fetched at start-up, at 13:xx and on retries.
  - Carnot is fetched every 30 minutes, and no attribute records when.
- **Attributes.**
  - `today` and `tomorrow` are bare lists, documented as "today[0] is the price of hour 00.00".
  - `raw_today`, `raw_tomorrow` and `forecast` carry timestamps.
  - All of these, and `tariffs`, are excluded from the recorder.
- **VAT.** DK1 and DK2 use 0.25. N1's `CD` rows and the three state tariffs all have VAT class D02.

**N1 in DataHub** (opened):
- **Three charge owners.** N1 publishes C-tariffs under:
  - "N1 A/S - 131": GLN 5790001089030, code `CD`;
  - "N1 A/S - 016": GLN 5790002502699, code `C-Tarif`;
  - "N1 A/S - 344": GLN 5790000611003, codes `T-C-F-F-TD`, `T-C-F-T-TD` and `T-C-F-TIME`.
  EDS has only "N1" = 5790001089030, codes `CD` and `CD R`.
- **The rates are identical for now**: 0.0879 / 0.2636 / 0.7907 for Oct–Dec 2026, and 0.0983 /
  0.2950 / 0.8849 from 2027-01-01. The published rows diverge in spring 2027:

  | Charge owner | Published 2027 rows |
  |---|---|
  | N1-131 | Jan–Mar: winter rates, normal hours. **April: winter rates, low load 01–07, peak 18–22, and 00–01 at the high rate.** May 1 – Oct 30: summer rates, normal hours. Oct 31 (the DST day): summer rates, low 00–05, peak 16–20. **Winter rates from 1 Nov** to 2028-02-29. |
  | N1-344 | Jan 1 – Mar 27: winter, normal hours. Mar 28 (the DST day): shifted. **Mar 29 – Jun 22: winter rates, low 01–07, peak 18–22.** |
  | N1-016 | Jan–Mar: winter. Apr 2027 – Dec 2027: summer, normal hours. |

  Neither N1's 2026 rows (Oct–Mar winter, Apr–Sep summer, normal hours) nor its press release (low
  00–06, peak 17–21) shows these changes.
- **Mid-season changes are routine at N1.** It published December-only rows in 2024 (0.045 / 0.134
  / 0.402) and 2025 (0.068 / 0.204 / 0.612). No December 2026 row exists today.
- **Patterns at other grid companies that the report does not mention:**
  - weekday and weekend rows, with no peak at weekends (Aal El-Net);
  - a November-only cut (Elektrus);
  - no low-load block (FLOW Elnet);
  - flat 2027 C-tariffs (Ikast, Grindsted, Læsø, Forsyning Elnet).

**Publication timing.** On 17 May 2026 Nord Pool announced at 13:50 CET that the coupling session
was delayed, with "a risk of Full Decoupling", and the next update at 14:20 (opened). Search
results also list delay notices on 30 June and 27 August 2026 (titles only, not opened).

**The car's behaviour** (re-ran, crude). The plan assumes 11 kW in every hour, takes the cheapest
hours by total price and re-plans each hour, while the car actually takes less. Data: 2026 N1
hourly totals, 301 nights.

| Nightly need | Power the car takes | Nights the plan ran out of hours before 07:00 |
|---|---|---|
| 6 kWh | 7.4 kW | 0 |
| 6 kWh | 3.7 kW | 5 |
| 15 kWh | 7.4 kW | 14 |
| 15 kWh | 3.7 kW | 167 |
| 25 kWh | 3.7 kW | 275 |

### Inferences
These are the ways the composed price could rank hours wrongly for this maintainer. All of it is
reasoning on the findings above.

1. **Wrong charge owner.** If his metering point is in area 344 or 016, EDS gives area 131's rows.
   Today that costs nothing. In April 2027 it does: area 131 calls 06–07 low load, area 016 calls it
   high load at summer rates. Verify his area once, from his bill or Eloverblik. An adapter of our
   own should key on GLN plus charge type code, not on the name "N1".
2. **N1's 2027 rows, right or wrong.**
   - If they are right, an engine or experiment that hardcodes 00–06 / 17–21 and Oct–Mar charges
     00–01 at the high rate and avoids 06–07, which is low load. The panel's `prices.py` and
     `arbitrage.py` do exactly that.
   - If they are data errors, EDS passes the error faithfully into every price.
   - Either way, read the hour-by-hour row, never a rule, and flag rows whose period boundaries
     differ from the previous row's.
3. **Silent zero tariff.** A day priced without its grid tariff looks 0.11–1.1 DKK/kWh cheaper incl.
   VAT, and the engine would defer charging to it.
   - It cannot happen for N1 now, because N1's rows are published into 2028.
   - It can happen after a company publishes late; several rows end on 2027-02-01.
   - The adapter must refuse such a slot, or price it pessimistically.
4. **Units and VAT of the additive markup.**
   - EDS can show prices in DKK or øre, per kWh or per MWh, with or without VAT, and its template is
     excl. VAT.
   - A default of "0.08 DKK/kWh incl. VAT" is wrong by ×100, ×1,000 or ×1.25 unless the adapter
     reads the sensor's unit and knows the VAT setting.
   - Too small a markup makes the engine wait for forecast days it should not wait for.
   - EDS does not expose the VAT setting as an attribute.
5. **15-minute mode for an hourly-billed household.** In that mode the engine sees ramps of up to
   about 0.36 DKK/kWh inside the hour. It would pick 17:00 over 17:45, a difference the maintainer
   does not pay. Check EDS's `resolution` option, or average by timestamp.
6. **Index-based attributes.** On DST days `today` has 23 or 25 entries, so index ≠ hour after
   02:00. If tomorrow's prices are missing at midnight, `today` becomes `None`. Use the timestamped
   attributes and check dates.
7. **Late or decoupled results.** Until tomorrow's prices arrive, tomorrow is priced from Carnot.
   That is 13:xx at the earliest, later on a delayed day such as 17 May 2026. The plan must re-run
   when the forecast is replaced, and this should be tested.
8. **The supplier's product.**
   - A flat per-kWh markup never changes the ranking.
   - I found no Danish supplier with a markup that varies by hour (search, not found). EDS's
     template could carry one, and his own supplier's terms were not checked.
   - A fixed-price or monthly-average product removes the spot part. All 00–06 hours then tie, and
     the tie-break decides.
   - The adapter therefore needs the product type, not only the billing resolution.
9. **The car takes less than the plan assumes.**
   - At his likely nightly need of 5–8 kWh, an 11 kW plan is robust even at 7.4 kW.
   - At 15 kWh or more, or on one phase, the plan picks too few hours and runs out of night.
   - This is a power-model error, not a price error, but it changes which hours are used. Plan on
     measured session power from the first week.
10. **Checked, and not a risk:**
    - VAT applies to every component (class D02).
    - Grid tariffs are hourly (`PT1H`), so metering per quarter or per hour gives the same grid
      charge.
    - Other household consumption in the same hour does not change the marginal price under a
      per-kWh tariff.
    - EUR→DKK conversion uses the CurrencyConverter package. A stale rate scales every hour alike
      (reasoning).

**On "always lower than the outcome".** In the code, the forecast's basis matches the known prices
when tariffs are on, so the gap he sees is not an artefact of how EDS composes prices. The red team
found the same sign in elpriser.org's data with two more days: a DK1 bias of −62 to −122 DKK/MWh at
every horizon.

Reasoning: a level bias does not hurt the ranking among forecast days, which is what he sees as
"right on trend". It does hurt the choice between a known and a forecast day, which is what the
additive markup governs. Its size and cause belong to the parallel researcher on forecast bias.

### Gaps
- Whether N1 intends its 2027 rows: not confirmed, since N1's page returned 403.
- The maintainer's N1 area, supplier, product and EDS settings: unknown.
- Carnot's time resolution, and whether its value is a mean or a median: unknown without calling
  the API.
- How DataHub encodes a 25-hour DST day in 24 columns: not resolved. EDS maps by clock hour.

## 3. What has been overlooked entirely?

### Takeaway
The report misses five considerations that could change the best charging time or the engine's
contract:
- **Row changes:** grid companies change their rows, period boundaries and seasons included, beyond
  the TREFOR example.
- **Charge owner:** the integration may read the wrong N1 area.
- **Tariff gaps:** a date with no tariff row is priced silently without the grid tariff.
- **Markup basis:** the unit and VAT basis of an additive markup.
- **The post-2027 tariff model:** it could add a capacity term to a household's cost.

Solar self-consumption, which is in the integration's planned scope, would also break the
one-price-per-slot contract.

### Cited Findings
- **Tarifmodel 3.0** is reported to apply from 2023 until 2027, and no successor for households was
  found. Dansk Erhverv asks for a model for the period after 2027 (search-result summaries only, not
  opened). A search for "Tarifmodel 4.0" found nothing.
- **Capacity payments.** N1 has notified a dynamic 12-month capacity payment for **larger**
  consumers (document title in search results, not opened). N1's `CD` tariff has only a fixed
  subscription (D01) and the per-kWh tariff (D03) (opened).
- **Elafgift.** The 0.008 row ends 2028-01-01 (opened). The rate from 2028 was not found.
- **Weekday/weekend C-tariff rows** exist at Aal El-Net (opened).
- **Energinet's 2027 tariffs** are still flat and separate (`P1D`) (opened).

### Inferences
All reasoning:
- **A capacity term for households after 2027** would make a slot's cost depend on power and on the
  rest of the house's load in that hour. That breaks N1's "price per wall kWh". Reserve an optional
  power ceiling per slot in the contract.
- **The fuse and the house's base load** cap the available power. The integration could pass them
  as that same per-slot ceiling.
- **Solar.** In a sunny hour the first kWh costs the lost export value (spot minus fees, no tariffs,
  no VAT), and the rest costs the import total. That is a piecewise price, which `PricePoint` cannot
  carry. N1 should say how a solar caller passes it. This does not apply if the maintainer has no PV
  (unknown).
- **Weekday-dependent tariffs** break any cache of "the tariff for this hour of day". The rule is to
  read the dated row.
- **Forecast freshness** is invisible in EDS, so N17's log must record the fetch time of each run.
- **The contract type** (fixed price, monthly average, spot, quarter-hour product) changes what
  "price" means. The report covers only the billing resolution.

### Gaps
- The successor to Tarifmodel 3.0: not found.
- A Danish supplier with a markup that varies by hour: not found.

## 4. Is the decision register, with N1–N17, consistent with motor.md and decisions.md?

### Takeaway
Mostly consistent, with loose ends:
- the removals leave fields, tunables and codes in motor.md that the register does not name;
- N12 brings back an absolute DKK threshold, which the report itself argues against;
- N3 requires motor.md's multiplicative markup formula to change.

### Cited Findings
- **Markup formula.** motor.md §6.4 uses `price × (1 + markup/100)`, and decisions.md O4 uses
  `[(hours_ahead, percent)]`. The report's N3 makes the markup additive and counts lead time from
  the last published slot.
- **Price horizon.** motor.md §6.2 takes hours "within the price data", and §6.1 step 5 stops at the
  "end of price data". The report's N8 covers all available time.
- **Waking the car.** motor.md still has §6.1 step 2 (wake), the tunables `soc_max_age_minutes`,
  `soc_refresh_delay_seconds` and `wake_up_before_charge_minutes`, the output `requires_wakeup`, and
  the reason `STALE_SOC_NEEDS_WAKEUP`. The report's N9, N15 and O7 remove waking.
- **D28.** motor.md still has `charger_auto_threshold`, §6.1 step 4 and `CHARGER_HANDLES_LOW_PRICE`.
- **The idle floor.** motor.md has `idle_planning_horizon_hours` = 24. The report's N13 moves the
  deadline to the expected plug-out.
- **Thresholds.** The report says absolute DKK thresholds "go stale at every tariff change", yet N12
  allows "a user threshold is one step".
- **Restart cost.** D26 calls restart cost "seconds", not modelled. The report's N5 adds a start
  overhead in kWh.

### Inferences
All reasoning:
- N3 needs motor.md §6.4 and O4's wording rewritten.
- D28's change should name the field and the reason code it removes. O7 and N15 should name step 2,
  the three wake tunables, `requires_wakeup` and `STALE_SOC_NEEDS_WAKEUP`. N13 should say what
  becomes of `idle_planning_horizon_hours`.
- The measurement table still lists `soc_max_age_minutes`. Say whether it survives under N15.
- Either state N12's threshold relative to tonight's prices, or accept that it must be re-entered
  at every tariff change.
- N9 makes `START_CHARGING`/`STOP_CHARGING` informational, but no register row records that change
  to motor.md §5 `actions`.
- N1 and N6 are consistent with each other and with D3. N1 should add unit and VAT normalisation as
  a duty of the integration, since the engine cannot detect it.
- N14 is conditional, which is consistent with D22's verdict. D14 ("keep") holds only if the greedy
  lives in the tests, which the register says.

### Gaps
- None beyond those named.

## 5. Findings and recommended corrections

### Takeaway
Two findings are blocking for an integration that composes prices for this maintainer:
- converting the additive markup's unit and VAT basis;
- slots silently priced with a grid tariff of 0.

Neither is a flaw in the engine's logic. Both are missing duties of the price adapter, which the
report rightly calls the most valuable component. The rest are important corrections to the money
figures, the evidence plan and N1-specific tariff handling, plus minor text fixes.

### Cited Findings
| Finding | Severity | Affected decision or section | Recommended correction |
|---|---|---|---|
| The default markup "0.08 DKK/kWh incl. VAT" is off by ×100, ×1,000 or ×1.25 unless the adapter normalises EDS's unit and VAT; too small a markup makes the engine wait for forecast days | Blocking | N1, N3, N16, O4 | Make unit and VAT normalisation an explicit integration duty; store the markup in DKK/kWh incl. VAT and convert it; refuse a source whose VAT state is unknown |
| EDS silently prices a date with no DataHub row at grid tariff 0, making the day look 0.11–1.1 DKK/kWh cheaper | Blocking | N1, N8 | Verify a grid tariff exists for every slot, or read DataHub directly; price uncovered slots pessimistically and flag them |
| Every money figure assumes quarter billing; on hourly billing (6 kWh a night) the timer is worth ≈1,090, ranking ≈410, spot-ranking loss ≈150 DKK/yr | Important | Headline; tariff section; N1's reason | State the billing basis and add the hourly figures |
| EDS's "N1" is area 131 only; areas 016 and 344 have different 2027 rows | Important | N1, adapter, measurement table | Add "his N1 charge owner" to the measurements; key the adapter on GLN + charge type code |
| N1's 2027 rows move the seasons (winter through April, again from 1 Nov) and shift periods one hour (April for 131; 29 Mar–22 Jun for 344) | Important | "Winter from 1 October"; D13; the experiments | Never hardcode periods or seasons; flag boundary changes; ask N1 to confirm; re-run the experiments on dated rows |
| No Carnot history can come from the recorder: EDS has excluded `forecast` since 2025-09-13 | Important | Measurement table; N17 | Drop the recorder row; log Carnot runs with their fetch time now |
| The EDS forecast's basis was never verified; it is now: tariffs, template and VAT are added to Carnot's spot | Important (positive) | Section on HA integrations; N1 | Say EDS is on the same basis when tariffs are on; keep refusing mixed bases (Strømligning, Nord Pool) |
| Ramps inside the hour reach ≈0.36 DKK/kWh at 17:00–18:00 | Minor (hourly billing); important (quarter billing) | O11, N2 | Keep N2; average by timestamp; check EDS's resolution option |
| An 11 kW plan for a car taking 3.7–7.4 kW runs out of night at needs of 15 kWh or more (14–275 of 301 nights) | Important | D16, N6, measurement table | Plan on measured session power from the first week; add a one-phase case to the measurements |
| A post-2027 capacity term, the fuse and base load, and solar's piecewise price | Important (watch) | N1, N2, D13 | Reserve an optional per-slot power ceiling; specify how a solar caller passes cheap energy |
| The contract type is not an adapter input | Minor | N2 | Make the product type an adapter setting |
| Index-based EDS attributes break on DST days and when tomorrow is missing at midnight | Minor | Adapter | Read only timestamped attributes and check dates |
| The headline's "600–1,100" does not match the computed 730–1,090 | Minor | Headline | Use 730–1,090 (quarter billing) or the hourly figures |
| Register row S1 says "23–38 %" | Minor | S1 | "23–32 %" |
| The summary's verdict counts omit L1, L4, O10, O5, S2 and S4 | Minor | Summary | Align it with the register |
| "as motor.md §6.2 now says" states the opposite of motor.md | Minor | Missed targets section | "unlike motor.md §6.2 today" |
| Removals leave orphaned fields, tunables, codes, the §6.4 formula and the §5 actions | Minor | D20, D28, O7, N9, N13, N15 | List them in the register so the naming pass (O3) catches them |
| N12 conflicts with the report's own objection to option (b) | Minor | N12, O1 | State the threshold relative to tonight's prices |
| The default markup comes from elpriser.org, not Carnot | Minor (labelled uncalibrated) | O4, N16 | Ship it off, or as an explicit placeholder, until his Carnot logs give a number |

### Inferences
- Reasoning: no finding overturns the report's main line. Tariff timing comes first, ranking
  tonight's totals second, forecasts and chaining third, and the price adapter is the most valuable
  component. For this maintainer the first point is stronger than the report says.
- The cheapest checks, in order:
  1. confirm his N1 charge owner and EDS settings: tariffs on, VAT, unit, and 60-minute resolution;
  2. start logging Carnot runs with their fetch time;
  3. ask N1 whether the 2027 rows are intended.

### Gaps
- The maintainer's EDS configuration, N1 area, supplier and product are unknown to every note and
  to this review.
