# Panel position: electricity-market economist and price forecaster

Written on 2026-10-28 after reading all seven notes in full. Notes are cited by file name and
section, for example `price_forecast_uncertainty.md` §7.6; each of those sections cites its own
primary sources. New sources opened for this paper are linked directly.

**Own calculation.** I wrote `experiments/prices/arbitrage.py` (kept beside the other price
experiments). It answers one question: how much money is there in charging beyond the night's need?
Its setup:

- **Prices.** Energi Data Service `DayAheadPrices`, DK1 and DK2, 2025-10-01 to 2026-10-29: 75,656
  quarter-hour rows ([API query](https://api.energidataservice.dk/dataset/DayAheadPrices?start=2025-10-01&end=2026-10-30&filter=%7B%22PriceArea%22:%5B%22DK1%22,%22DK2%22%5D%7D&limit=0),
  fetched 2026-10-28).
- **Billing.** Hourly: the mean of the four quarters.
- **Total price.** 1.25 × (spot + grid tariff + 0.123). The grid tariffs are N1 area 131 (DK1) and
  Radius (DK2) at the rates in `price_composition_denmark.md` §1. The 2026 flat parts are applied
  throughout, so the 1 January drop in elafgift does not distort the comparison.
- **Car.** Plugged in 17:00–07:00 every night (392 nights), using 7.5 kWh a day, 11 kW.
- **Rules compared.**
  - *Floor*: each night buys that night's need in its cheapest hours.
  - *Oracle*: perfect foresight, which may carry H kWh of extra stock. Solved exactly by a DP on a
    0.5 kWh grid.
  - *O1(c)*: on top of the floor, fill up to H in any hour priced at or below the p-th percentile of
    the prices known at 17:00 (tonight, plus tomorrow 07–24).

Everything labelled **Reasoning** is my argument, not a sourced fact.

## C1 / O1: should the engine charge beyond the required floors, and by what rule?

### Takeaway
Yes, but only by a value rule with a hard SoC ceiling, never by a price percentile. The engine
should buy energy beyond the floors only when the slot's marked-up price is below a
**replacement value τ** that the caller supplies (price units per kWh). It should store that extra
energy only up to a caller-supplied **`surplus_max_soc`**, which by default sits below the
battery's high-wear step. The engine needs these two inputs and nothing else. The integration works
them out from the forecast trend and from the car's learned daily use. A user threshold (O1 b) is
then simply a τ the user types in.

The money is real but modest. With perfect foresight, extra stock earns at most about 300–330
DKK/yr with 7.5 kWh of headroom, 505–540 with 15 kWh and 770–820 with 30 kWh. A forecast captures
part of that. The wear cost is of the same order once the extra stock pushes the car above the
~55–60 % step, and close to zero below it. That is why the cap, not a per-kWh wear term, is the
right control.

### Cited Findings
**The five positions, steelmanned**
- **Battery note: never.** Calendar ageing runs in plateaus. Keil et al. find a marked step at
  about 60 % cell SoC for NMC/NCA, a "high-fade" plateau at 65–95 %, and roughly flat ageing at
  10–60 %. Charging beyond the floors parks energy above the step, so it is "wear bought with money
  saved". If surplus charging is ever allowed, it should be capped at about 55–60 % —
  `charging_physics_battery.md` §5 and §8.
  - Strongest form of the argument: the saving is a few hundred DKK and the wear is uncertain, so
    "never" is the safe default.
- **Driver note: a percentile up to the default target.** Unannounced trips are the main reason
  drivers override smart charging (Electric Nation), and users rarely enter trips. A fill in cheap
  hours, needing no user input, buys trust — `driver_behaviour_ux.md` §1, §3 and §7.
  - Strongest form of the argument: the binding risk is availability, not price.
- **Prior art: a user price threshold.** evcc's smart cost limit, openWB's eco `max_price`,
  EV Smart Charging's price limit and Monta's rules all use one — `prior_art_software.md`
  "Comparison" and "O1".
  - Strongest form of the argument: it is transparent and proven in the field.
- **Scheduling note: give stored energy a value; at least use negative consumer prices.** On DK1
  in Jan–Sep 2025, a floors-only plan lost up to 48 % of a week's optimum, driven by negative
  prices. evcc's optimiser values the energy left at the end of the horizon —
  `scheduling_algorithm.md` §7 (O1 row).
  - Strongest form of the argument: a terminal value is the theoretically correct object, and it
    fits a DP.
- **Forecast note: next-cheaper day.** Charge beyond the floors only for days forecast dearer than
  now by more than the markup. In an October simulation this recovered 80–97 % of the
  perfect-foresight saving, and it needs an assumed daily consumption —
  `price_forecast_uncertainty.md` §7.6.
- **Maintainer: use the forecast trend.** Over 23 elpriser.org runs, the forecast called the
  direction of D+2..D+7 against D+1 right in 82 % of cases (DK1) and 76 % (DK2). It picked the
  cheapest of the next 6 days 50–71 % of the time, against 17 % by chance. A binary
  "trend up → fill" switch was dominated by ranking — `price_forecast_uncertainty.md` §7.1, §7.4
  and §7.6.

**Money at stake (own calculation, method above)**

| Area, 7.5 kWh/night | Floor-only cost | Oracle, H = 7.5 kWh | H = 15 kWh | H = 30 kWh |
|---|---|---|---|---|
| DK1 | 3,238 DKK (1.10 DKK/kWh) | −302 DKK/yr (mean extra stock 3.9 kWh) | −505 DKK/yr (7.5 kWh) | −771 DKK/yr (15.2 kWh) |
| DK2 | 3,297 DKK (1.12 DKK/kWh) | −326 DKK/yr | −539 DKK/yr | −817 DKK/yr |

- **Lower use.** At 5 kWh/night with H = 15, the oracle saves 465 (DK1) and 483 (DK2) DKK/yr.
- **Night-to-night variation.** The night price of the cheapest 7.5 kWh has a standard deviation
  of 0.40–0.41 DKK/kWh incl. VAT. Its mean change from one night to the next is 0.23 (DK1) and
  0.25 (DK2) DKK/kWh.
- **The baseline these savings add to.** Within-night smart charging saves 1,400–3,050 DKK/yr
  against plugging in at 17:00 — `price_composition_denmark.md` §5. Inter-day stock therefore adds
  at most about 20–35 % on top.
- **Lund's figure.** Its estimate of the value of multi-day forecasts is 44–56 EUR per vehicle per
  year (SE3, 50 km/day, 7.4 kW) — `price_forecast_uncertainty.md` §5. At the ECB reference rate of
  7.4741 DKK/EUR on 2026-10-28 ([ECB](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml))
  that is ≈330–420 DKK/yr, inside my oracle range.
- **Knowing only published prices earns almost none of this.** At 17:00 the published prices
  cover tonight, but only 17–24 of the next night, and those hours carry the peak and high-load
  tariffs (`price_composition_denmark.md` §1, §3). (Reasoning from the publication time and the
  tariff periods.)

**O1(c), a percentile rule on the known horizon (own calculation)**

| Rule | DK1 saving | DK1 mean extra stock | DK2 saving | DK2 mean extra stock |
|---|---|---|---|---|
| p = 10, H = 15 | 88 DKK/yr | 7.6 kWh (on 55 % of nights) | 108 DKK/yr | 7.9 kWh |
| p = 25, H = 15 | 84 DKK/yr | 10.8 kWh (on 82 % of nights) | 58 DKK/yr | 11.2 kWh |
| p = 10, H = 30 | 128 DKK/yr | 15.6 kWh | 173 DKK/yr | 16.8 kWh |

For the same stock, the oracle earns about 5× as much.

**Negative consumer prices**
- Total price below zero in the 17:00–07:00 window over the whole year: **0 hours** in DK1 and DK2
  (own calculation, hourly billing, no supplier markup).
- Over all hours of the 13 months: 2 quarter hours in DK1 and none in DK2 —
  `price_composition_denmark.md` §4.
- The scheduling note's 48 % figure used DK1 **spot only**, Jan–Sep 2025, when 6.3 % of hours
  were negative — `scheduling_algorithm.md` §7. Negative hours in DK1+DK2 fell from 629 to 274 by
  late August 2026 — `price_composition_denmark.md` §4.

**Wear, in money**
- **Physical inputs.**
  - Early charging that leaves the car above the step 6 extra hours a night costs an upper bound of
    about 0.7 %/yr extra fade.
  - Keil's plateau gap is about 2.5 points per 10 months at 25 °C.
  - 10–60 % SoC sits on one plateau (≈3 % loss over 10 months at 25 °C).
  - Danish temperatures make all of these smaller (Arrhenius).
  - Source: `charging_physics_battery.md` §5.
- **Price inputs.**
  - BNEF's 2025 survey: BEV packs $99/kWh; China $84/kWh; Europe "56% higher" than China.
    Published 2025-12-09 ([BNEF press release](https://about.bnef.com/insights/clean-transport/lithium-ion-battery-pack-prices-fall-to-108-per-kilowatt-hour-despite-rising-metal-prices-bloombergnef/)).
  - ECB 2026-10-28: USD 1.1133 and DKK 7.4741 per EUR, so 6.71 DKK/USD ([ECB](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml)).
- **Arithmetic (Reasoning).**
  - A pack costs $99–131/kWh, which is 665–880 DKK/kWh.
  - 1 % of a 75 kWh pack is 0.75 kWh, so 1 % of capacity is worth about 500–660 DKK at pack cost.
  - At 0.7 %/yr, wear costs ≈350–460 DKK/yr.
  - Held above the step all year (≈3 %/yr at 25 °C), it costs ≈1,500–2,000 DKK/yr.
  - Pack cost is a *lower* bound on the economic loss, since it leaves out labour, margin and
    residual value. The fade rates are upper bounds for Denmark. These are orders of magnitude,
    not estimates.
- **Throughput.** Energy throughput is unchanged, because the car drives the same kilometres, so
  cycle wear does not change. (Reasoning.)

### Inferences
- **Reasoning, the core economics.** A kWh stored tonight is worth the price of the kWh it replaces
  later. Where the later need is in the schedule, D22 already does this: a cheap hour on day 1 is
  given to the day-5 target if it precedes that deadline (`motor.md` §6.2). This works only if the
  caller generates targets across the forecast horizon (D27), and only up to the caps. O1 is
  therefore only about consumption *outside* the schedule. Its value is the replacement price τ,
  which lies beyond the engine's knowledge. That makes τ an input, as D3 and D13 require.
- **Reasoning, why a cap and not a linear wear term.** Ageing is a step function of SoC (plateaus),
  so the marginal wear of a stored kWh is ≈0 below the step and large when the stock crosses it. A
  ceiling on surplus SoC represents that exactly; a per-kWh wear cost does not.
  - With a floor-level SoC around 30–45 % and a cap at 55–60 %, the headroom is 10–25 points
    (7.5–19 kWh on a 75 kWh pack). That is the 7.5–15 kWh band above, worth roughly 300–540 DKK/yr
    at perfect foresight.
  - Above the step, the wear (≈350–2,000 DKK/yr) eats or exceeds the extra 230–280 DKK/yr that the
    15 → 30 kWh band adds.
  - The battery note and I agree on the cap. We disagree on "never".
- **Reasoning, the proposed rule.**
  - **Engine.**
    - Two optional inputs: `surplus_value` τ (price units per kWh) and `surplus_max_soc` (SoC %).
      Defaults are `None`, which is today's behaviour, lean (a).
    - When both are set, the engine may buy beyond the floors in any available slot whose
      marked-up price is below τ. It never stores surplus above `min(surplus_max_soc, target
      caps)`.
    - In the DP that `scheduling_algorithm.md` §7 recommends, this is a terminal value of τ per kWh
      above the floors, with a SoC bound. In a greedy, it is a third pass over the remaining slots
      in ascending marked-up price.
    - Negative or zero prices need no special rule: any τ > 0 makes them eligible, which honours D25.
  - **Integration, forecast mode, for the maintainer.**
    - For each forecast day d, let r_d be the marked-up price of the cheapest slots that buy one
      day's expected use.
    - Let d* be the first day with r_d ≤ tonight's price.
    - Set τ = min(r_d) over the days before d*.
    - Set `surplus_max_soc` = min(wear cap, floor SoC + expected use until d*).
    - Expected use is learned from the car's history: SoC drop or charger kWh per day.
    - This is the forecast note's next-cheaper rule (§7.6), with the consumption the engine lacks
      supplied by the caller.
  - **Integration, manual mode.** The user sets τ (a DKK/kWh threshold, O1 b) and the cap.
  - **Integration, off.** The default when no forecast is configured.
- **Reasoning, rejecting O1(c).**
  - Danish tariffs make the 00–06 low-load hours the cheapest part of almost every 31-hour known
    horizon (`price_composition_denmark.md` §1).
  - A percentile of the horizon therefore fires on most nights (55–89 % here) whatever the
    multi-day trend. It holds a large stock for one-fifth of the oracle's money.
  - With `default_target_soc` = 80 % as its ceiling, it also sits in the high-fade plateau.
- **Reasoning, rejecting O1(d) and a fixed threshold as the default.**
  - Absolute DKK thresholds go stale every time a tariff changes. Changes were seen on 1 Oct,
    1 Dec, 1 Jan, 1 Apr and 1 Sep (`price_composition_denmark.md` §1), and spot rose 34 % year on
    year (same note).
  - A threshold is fine as an opt-in, which τ already provides.
- **Reasoning, on the driver note.** Availability for unplanned trips is insurance, not price
  arbitrage. It belongs in `min_idle_soc`, which is price-independent and charged in cheap hours,
  as `driver_behaviour_ux.md` §7 itself proposes ("if (a) is kept, raise `min_idle_soc`"). Mixing
  insurance into a price rule makes both badly tuned.
- **Reasoning, on the maintainer's trend.**
  - It is used through τ and through ordinary ranking. A binary switch is not needed (it is
    dominated, §7.6).
  - It matters mostly in volatile weeks. In calm weeks the money at stake is small too, so poor
    direction accuracy there costs little. What counts is accuracy weighted by the size of the
    move, not the hit rate.

### Gaps
- No full-year simulation with real forecasts in the loop exists. The elpriser archive starts
  2026-10-06, and Carnot keeps no public archive (`price_forecast_uncertainty.md` §7 Gaps). The
  forecast-captured share of my oracle figures is therefore not measured. The October
  simulation's 80–97 % is an optimistic bound (see the weakest-claims section).
- My model assumes plug-in every night. Danish data show 40 % of re-plugs within 24 h
  (`driver_behaviour_ux.md` §2), so the real value per car is lower and more variable.
- I applied one grid company and one tariff table per area to the whole year, ignoring the
  December 2025 and other date-specific rows.
- Not found: the price of a replacement Enyaq pack or module; how displayed SoC maps to the cell
  step on MEB; parked self-discharge that would make stock decay (`charging_physics_battery.md`
  §5–§6 Gaps).

## C2 / D20 / O4: shape, unit and size of the forecast markup

### Takeaway
The markup should be **additive, in the caller's price units**, stepped by the **lead time from
the forecast's origin** (hours past the last published price), not by hours from `now`.

- Published prices carry no markup.
- The first forecast day carries ≈0.05–0.10 DKK/kWh on spot excl. VAT, which is
  **≈0.06–0.125 DKK/kWh on a total incl. VAT**.
- The step rises by about a third towards D+7, then stays flat.

The engine ships no numeric default, because D3 makes any additive number unit-bound. The
integration owns the DKK defaults. There is no need to split each price into a known and an
uncertain part: an additive markup is already blind to the known parts. Ranking by forecast plus
this markup captures the trend only for energy the engine has been told it needs, which is why
C1's τ is needed as well.

### Cited Findings
- **Error is additive, not proportional.** In the 3-week elpriser archive, the lowest forecast
  quartile had the largest absolute error (DK1 MAE 347 DKK/MWh, 63 % relative) and the highest
  quartile a smaller one (234, 16 %). A percentage markup makes a negative forecast more attractive
  — `price_forecast_uncertainty.md` §4.
- **Error grows with lead time.** MAE rises about 30 % from D+2 to D+9: elpriser backtest DK1 149 →
  179 → 197 DKK/MWh. Growth is about t^0.2–0.3 — `price_forecast_uncertainty.md` §2–§3.
- **Size.** The optimiser's-curse bias at the chosen hours was +114 to +158 DKK/MWh in DK1. The
  simulation tolerated a premium of 0–100 DKK/MWh and was hurt at 300. Lund found λ = 0 (the
  median) near-optimal in 3 of 4 cells — `price_forecast_uncertainty.md` §5 and §7.6.
- **The known horizon moves.** It swings between about 11 and 35 hours over the day, and error
  should be measured "by hours ahead from the auction, not from now" —
  `price_composition_denmark.md` §7 (D20 bullet); `price_forecast_uncertainty.md` §1 Inferences.
- **Tariffs are known in advance.** They come from DataHub rows published months ahead —
  `price_composition_denmark.md` §1 and §7.
- **Forecasts arrive on a different basis.** Strømligning's forecast excludes tariffs, and
  whether Carnot's includes them is unverified — `home_assistant_data.md` "Price integrations".
- **Rescaling by spread was suggested.** The forecast note proposes scaling a dimensionless step by
  the spread of the call's known prices, and calls it untested — `price_forecast_uncertainty.md`
  §4 and §6.
- **Forecasts give no band from the main source.** Carnot gives a point forecast with no band —
  `price_forecast_uncertainty.md` §1.
- **The within-day spread is mostly tariff.** The tariff swing is ≈0.85 DKK/kWh excl. VAT in
  winter (Radius), as large as the daily spot spread — `price_composition_denmark.md` §1.

### Inferences
- **Reasoning, D3 and the unit.** An additive markup needs a unit. Since the engine must not know
  DKK, `forecast_markup_steps` is `[(lead_hours, amount), ...]` in the caller's units, with the
  engine default empty (no markup).
  - The integration ships Danish defaults: 0 for published prices; 0.08 DKK/kWh incl. VAT from the
    first forecast hour; 0.10 from D+4; flat from D+7.
  - These are mid-range starting values, uncalibrated.
- **Reasoning, against scaling by the spread of known prices.** In Denmark, most of the within-day
  spread of a total price is the tariff structure (peak 17–21), not spot uncertainty. A markup
  scaled by that spread would roughly double every 1 October when winter tariffs start, with no
  change in forecast error. Do not adopt it.
- **Reasoning, VAT and composition.**
  - If the caller passes totals, the spot error reaches the engine multiplied by 1.25 (VAT). The
    DKK default must be stated on the same basis as the prices, so the integration states it incl.
    VAT.
  - Known parts (tariff, Energinet, elafgift) add no error, so a split `known_part` /
    `uncertain_part` adds nothing for an additive markup.
  - The one exception would be a supplier markup charged as a percentage of spot. Whether such
    markups exist is not found.
- **Reasoning, lead from the origin.** A forecast for tomorrow night issued after the auction is
  D+2 whether `now` is 13:05 or 23:00, and its error is that of D+2. The steps should key on hours
  since the last published slot. The caller can pass `forecast_lead_hours` per point, or the
  engine can infer it from the first `is_forecast` point.
- **Reasoning, per-point uncertainty.** Where a band exists (elpriser P10/P90), let the caller
  pass `markup` per point, for example 0.2–0.3 × (P90 − P50), which matched the bias in §5. It
  overrides the step table. Keep it optional: Carnot users will not have it.
- **Reasoning, "the markup already captures the trend" is half true.**
  - Section 7.6's simulation charged *each future day's consumption* at the cheapest forecast day.
    In the engine that happens only for energy the floors demand, which means targets generated
    for future days.
  - With no future targets the engine buys nothing for D+3, and the trend has nothing to act on.
  - So ranking plus markup is the right mechanism for *when*. τ (C1) is needed for *how much*
    beyond the schedule.
- **Reasoning, the markup is small because re-planning fixes errors.**
  - Each call re-decides, and only the energy charged in the current slot is irrevocable
    (`scheduling_algorithm.md` §5). The loss from a wrong wait is the price difference × kWh,
    which is linear.
  - The asymmetric risk is a deadline that forces expensive hours. D8 and the floors already price
    that. A larger markup near tight deadlines is a plausible refinement, but no source tested it
    (`price_forecast_uncertainty.md` §6 Gaps).

### Gaps
- All size evidence is October 2026, one provider (elpriser.org), 23 overlapping runs.
- Carnot, the forecast most Danish HA users have, is untested: it needs a key.
- Not found: whether any Danish supplier charges a percentage-of-spot markup.

## C4 / O11: what the engine is given, and what the integration composes

### Takeaway
The engine is given a contiguous list of `PricePoint(start, end, price, is_forecast[, markup])`:

- `start` and `end` are timezone-aware.
- `price` is the **total marginal price per kWh drawn from the wall**, in caller units: spot,
  supplier markup, grid tariff, Energinet and elafgift, times VAT.
- Slots may be 15 or 60 minutes long and mixed.

The integration chooses the resolution from the user's billing product: hourly averages for the
default hourly product, quarters only for a quarter-hour product. It composes the total, and it
brings forecasts onto the same basis before marking them `is_forecast`. The engine must never
assume 24 hours or 96 quarters in a day.

### Cited Findings
- **Tariffs are half the value.** Ranking by spot instead of the total costs 185–217 DKK/yr. A
  dumb 00:00 timer captures roughly half the smart saving, because of the tariff structure —
  `price_composition_denmark.md` §5.
- **The resolutions differ.** Spot is quarter-hourly since delivery day 1 October 2025; grid
  tariffs are hourly (`PT1H`). Default retail billing is the hourly average of the quarters.
  Following quarters on a quarter product saves only ≈45–75 DKK/yr for an EV —
  `price_composition_denmark.md` §3.
- **DST, verified in the data downloaded for this paper.** DK1 and DK2 have 100 quarter rows on
  2025-10-26 and 2026-10-25 and 92 on 2026-03-29
  ([DayAheadPrices](https://api.energidataservice.dk/dataset/DayAheadPrices?start=2025-10-01&end=2026-10-30&filter=%7B%22PriceArea%22:%5B%22DK1%22,%22DK2%22%5D%7D&limit=0)).
  On transition days, DataHub fills the shifted hour with the previous hour's tariff —
  `price_composition_denmark.md` §1.
- **DKK conversion.** DKK prices in DayAheadPrices are converted from EUR
  (`price_composition_denmark.md` §3). The DKK/EUR ratio in the rows ranged from 7.466 to 7.476
  (own calculation, same data).
- **Sources compose differently.** Energi Data Service (optional tariffs, hourly average by
  default), Strømligning (totals; spot-only forecasts), core Nord Pool (excl. VAT and tariffs) and
  Tibber (`price_total`, with the DSO tariff unverified) all differ — `home_assistant_data.md`
  "Price integrations".
- **Prior art.** evcc, EV Smart Charging, Monta and openWB already handle 15-minute slots —
  `prior_art_software.md` "Pitfalls" 6.
- **Cost of quarter slots.** A DP over 672 quarter slots takes 21–43 ms in CPython, against
  5.7 ms for 168 hours — `scheduling_algorithm.md` §2.

### Inferences
- **Reasoning, the contract.**
  - Add `end` (or a duration), and let the API layer check continuity in absolute time, not in
    local hours.
  - Document `price` as "marginal cost per wall kWh, all per-kWh components included, same basis
    for known and forecast points".
  - Fixed subscriptions stay out, because they do not vary with the plan.
- **Reasoning, resolution.**
  - On an hourly product, passing quarters lets the planner "save" money the bill never shows.
    Pass hourly totals.
  - The engine can still run part of an hour, starting late, which is how evcc trims the partial
    slot.
  - On a quarter product, pass quarters, at the 4× compute cost noted above.
  - Hourly forecasts beyond tomorrow stay hourly. Mixed lengths must be allowed.
- **Reasoning, composition belongs to the integration (D13).**
  - Grid company from location or configuration; the date-specific tariff row (rates change
    several times a year); the local hour, resolved on DST days; Energinet; elafgift; supplier
    markup; VAT.
  - The forecast spot needs exactly the same additions, or the series shows a false cliff where
    the forecast begins (`home_assistant_data.md`).
  - The integration should record per source whether it delivers spot or total, and refuse to mix
    the two.

### Gaps
- Not found: whether Tibber's `price_total` includes the DSO tariff in Denmark; how a supplier
  settles a quarter product on an hourly meter (`price_composition_denmark.md` §3 Gaps).
- Not measured: the DP's timing at 672 slots on Raspberry-Pi-class hardware.

## D28: `charger_auto_threshold`

### Takeaway
Drop it from the engine. The integration can offer "let the charger's own automation run below X"
as an advanced, default-off caller feature. Economically, a threshold rule is a special case of
planning with τ on the same prices. Its price basis on the charger is unknown, and it creates two
controllers.

### Cited Findings
- **Price basis.** If a charger's automation compares spot rather than the total, it will charge
  at 17–21 on a cheap-spot evening that the peak tariff makes ≈1.06 DKK/kWh dearer —
  `price_composition_denmark.md` §7 (D28).
- **Easee.** Its developer page on smart charging does not say what price or threshold Easee
  uses; it leaves the logic to the integrator ([Easee developer: smart charging](https://developer.easee.com/docs/api-smart-charging),
  opened 2026-10-28).
- **Monta.** Its help page offers rules such as "only when electricity costs less than 0.15
  €/kWh". It lets the user add a DSO and fees for its electricity cost, but does not say whether
  the rules use that total ([Monta help](https://monta.com/help/en_US/charging-at-home/smart-charging-explained),
  opened 2026-10-28).
- **No readable threshold.** No charger integration exposes its own price threshold. Two
  controllers conflict: Zaptec "resume" only undoes its own "stop", and Easee's "smart charging"
  LED disables its plans — `home_assistant_data.md` "Charger integrations".
- **Decision order.** Step 4 (`CHARGER_HANDLES_LOW_PRICE`) short-circuits planning whenever the
  current price is below the threshold — `motor.md` §6.1.

### Inferences
- **Reasoning.** The engine already sees every price the charger sees, in a better basis (the
  total). Any "charge whenever cheaper than X" is reproduced exactly by τ = X with a cap (C1),
  and without giving up the plan.
  - D28 has value only if the charger knows something the integration does not. Nothing found
    says it does.
  - Step 4 also hides the plan from the user during exactly the hours it fires.

### Gaps
- Not found: the price basis (spot or total) of Easee's, Zaptec's or Monta's own automations.

## Which claims in the notes are weakest, and how should that limit the decisions?

### Takeaway
The trend evidence (forecast note §7) comes from an unusually volatile month. Day-to-day moves in
its window were about 1.7× the annual average, and over the year a third of day-to-day moves were
below the size where §7.3 found direction to be a coin flip. That limits it to supporting the
*mechanism*: forecasts in the ranking, and τ from the forecast. It cannot support defaults or
claims of 80–97 % capture.

### Cited Findings
- **Volatility in the §7 window (own calculation, DayAheadPrices daily means).**
  - The mean |change in daily mean spot| from one day to the next was 350 (DK1) and 333 (DK2)
    DKK/MWh on 6–29 Oct 2026.
  - Over the whole year it was 203 and 209 (medians 161 and 162).
  - Monthly lows were 95 in Feb 2026 (DK1) and 122 in May 2026 (DK2).
  - 35 % (DK1) and 33 % (DK2) of day pairs moved by less than 100 DKK/MWh.
- **Where direction fails.** §7.3: a move under 100 DKK/MWh is a coin flip (52 % / 45 %) —
  `price_forecast_uncertainty.md` §7.3.
- **The sample.** 23 overlapping runs, one provider, two windy episodes, PT statistics that assume
  independence — `price_forecast_uncertainty.md` §7 Takeaway and Gaps.
- **Other weak bases.**
  - Optimiser's-curse bias and the scale-by-level check: 3 weeks, and DK2 is distorted by a
    general −116 to −175 DKK/MWh under-forecast — `price_forecast_uncertainty.md` §2 and §5.
  - Lund: SE3, no fixed departures — §5.
  - Battery ageing: 18650 cells stored at 25–50 °C; the step's position in displayed MEB SoC
    unknown — `charging_physics_battery.md` §5.
  - Override evidence: UK 2017–19, network-managed rather than price-managed —
    `driver_behaviour_ux.md` source notes.
  - S4 and the O1 negative-price loss: DK1 spot only, 2025, EUR, prices clipped —
    `scheduling_algorithm.md` §7 Gaps.
  - The price note's savings: one grid company per area, every night plugged in, no forecast —
    `price_composition_denmark.md` §5.
- **The research log's figure.** The "8–11 % MAPE" in `research.md` could not be found again;
  measured DK multi-day MAE is 23–38 % of the mean price — `price_forecast_uncertainty.md` §2.

### Inferences
- **Reasoning, what the evidence can and cannot carry.**
  - Decide mechanisms now: an additive markup; τ and the cap; a total-price contract; variable
    slots.
  - Ship every number as an overridable starting value: the markup steps, the wear cap, τ's
    construction.
  - State in `decisions.md` that the values are uncalibrated.
- **Reasoning, the calibration plan.**
  - Log every forecast run the integration receives (Carnot included) and every published price.
  - After 12 months, rerun §5's bias and §7.6's rules, and my oracle, with forecasts in the loop,
    per season.
  - The elpriser archive keeps 400 days from 2026-10-06 (`price_forecast_uncertainty.md` §1), so a
    full year will exist from October 2027.
- **Reasoning, the maintainer's long experience.** It is real evidence, but unlogged and probably
  with Carnot. It is consistent with §7, but it cannot calibrate anything.
- **Reasoning, why calm periods matter less for money than for hit rates.** A coin-flip direction
  on a 100 DKK/MWh move risks about 0.1 DKK/kWh × stock. That is why accuracy weighted by move
  size, not the hit rate, should be the metric for calibration.

### Gaps
- No year-long, both-season, forecast-in-the-loop test exists for any rule.

## Where do the notes contradict each other on facts, and what does the source say?

### Takeaway
Only one factual conflict changes a decision: how often prices are negative, as it bears on O1. The
scheduling note's figures are spot-only 2025 data. For a Danish consumer in 2026 the total price
was not negative in a single night-window hour (own calculation). The other apparent conflicts
come from different periods or definitions, and they reconcile at the source.

### Cited Findings
- **Negative prices.**
  - The notes give three figures:
    - 6.3 % of DK1 hours negative, Jan–Sep 2025, spot (`scheduling_algorithm.md`, harness description at the top);
    - 2.5 % of DK1 quarter hours, Oct 2025 – Oct 2026 (`price_composition_denmark.md` §4);
    - 2.7 % of hours ≤ 0 (`price_forecast_uncertainty.md` §4).
  - They are consistent once period and definition are matched: Norlys counts 274 negative hours
    by late August 2026 against 629 a year earlier (`price_composition_denmark.md` §4).
  - On the basis that matters, the total price, there were 0 negative hours in the night window
    (own calculation) and 2 quarter hours overall (`price_composition_denmark.md` §4).
- **Publication time.**
  - 12:45 CET per Nord Pool support (`price_composition_denmark.md` §3); 13:00 CET per the Lund
    thesis (`price_forecast_uncertainty.md` §1).
  - Energi Data Service advises polling 13:00–14:00 CET. The primary source, Nord Pool, says
    12:45, and the data reaches Home Assistant by 13–14.
- **15-minute go-live.**
  - "30 September 2025" (`home_assistant_data.md`) against delivery day 1 October 2025 (the other
    two notes; APG).
  - APG: "on the trading day of 30 September 2025 for the delivery day of 1 October 2025"
    (`price_forecast_uncertainty.md` §1).
  - Confirmed in the data downloaded here: the first rows are 2025-10-01, quarter-hourly.
- **elpriser.org forecast error.**
  - Backtest MAE 149–211 DKK/MWh against 227–400 in the 3-week check
    (`price_forecast_uncertainty.md` §2).
  - Both are about 23–38 % of the mean price. The October window was priced higher and moved more
    (see the weakest-claims section).
- **Forecast run time.** elpriser runs are "generated around 12:13 UTC" (§7) but the model is
  "retrained daily at 14:10 UTC" (§1). Both come from the same note's sources; not reconciled.
  Not decision-relevant.

### Inferences
- **Reasoning.** The scheduling note's conclusion, "O1 lean (a) is contradicted when prices go
  negative", should be restated for Denmark. Negative totals are economically irrelevant in
  2026–27 at elafgift 0.008. The case for a value of stored energy rests instead on
  night-to-night spot variation (0.23–0.25 DKK/kWh mean change), which my oracle prices at
  300–820 DKK/yr.

### Gaps
- The elafgift from 2028 is not found (`price_composition_denmark.md` §1). If it returns near
  0.72, negative totals vanish entirely, while the inter-day spot variation, and so τ's value, is
  unaffected.

## Summary: recommendation per decision

### Takeaway

| ID | Recommendation | Confidence | What evidence would change it |
|---|---|---|---|
| **O1 / C1** | Replace lean (a) with optional `surplus_value` τ and `surplus_max_soc`, both default `None` in the engine. Integration: forecast mode (τ = replacement price of the coming dearer days, cap = min(wear cap ≈ 60 %, floor + learned use until the next cheaper day)); manual mode (user τ = O1 b); off without a forecast. Reject (c) and (d) | Medium (mechanism); low (cap value, money) | A year of forecast-in-the-loop simulation showing capture < ~30 % of the oracle (drop the feature), or showing gains above the step exceeding the wear cost; MEB measurements placing the wear step elsewhere |
| **O1 money** | Upper bound 300–820 DKK/yr (7.5–30 kWh headroom); realistic with forecasts perhaps half of that; wear above the step ≈350–2,000 DKK/yr at pack cost | Low | A forecast-in-the-loop year; real Enyaq pack replacement price; Danish-temperature calendar-ageing data |
| **D20 / O4 / C2** | Additive markup in caller units; steps keyed on lead from the last published slot; integration default ≈0.08 DKK/kWh incl. VAT at the first forecast day, ≈0.10 from D+4, flat from D+7; optional per-point markup from P90−P50 (×0.2–0.3); no known/uncertain split; no spread-based scaling | Medium (shape); low (size) | Year-long bias of chosen hours by lead time per season (elpriser archive, logged Carnot); evidence of percentage-of-spot supplier markups (would need a split) |
| **O11 / C4** | `PricePoint` gains `end`; 15 and 60 min mixed; aware datetimes, DST days of 92/100 quarters; price = total marginal per wall kWh incl. VAT; resolution chosen by billing product (hourly by default); the integration composes tariffs, taxes and VAT and puts forecasts on the same basis | High | Danish grid tariffs moving to 15-minute resolution; billing rules changing so hourly products settle per quarter |
| **D28** | Drop from the engine; τ covers "charge below X"; any use of a charger's own automation is an advanced, default-off integration feature | Medium | A charger integration exposing a readable threshold on a known (total) price basis, or a charger acting on information the integration lacks |
| **D25** | Keep; no special negative-price rule needed once τ exists | High | Return of frequent negative totals (e.g. elafgift change plus deeper negative spot) |
| **Weak evidence** | Decide mechanisms now; mark all defaults uncalibrated; log forecasts from day one; recalibrate after 12 months | High | — |

### Cited Findings
- Each row rests on the sections above: C1, C2, C4, D28, the weakest claims and the
  contradictions.

### Inferences
- **Reasoning.** The panel's apparent five-way split on O1 reduces to two separable questions. How
  much to value future replacement energy is τ, which belongs to the economist and the forecast.
  How high stored energy may sit is the cap, which belongs to the battery engineer. Reliability
  for unplanned trips is a third question with its own lever, `min_idle_soc`, and must not be
  folded into a price rule.

### Gaps
- None beyond those listed per section.
