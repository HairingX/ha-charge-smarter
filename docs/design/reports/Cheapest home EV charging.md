# Tariff timing wins; forecasts refine the plan

In Denmark in 2026, the cheapest way to charge an EV at home is to rank hours by the **total price
per kWh drawn from the wall**: spot, the grid company's time-of-use tariff, Energinet's tariffs,
elafgift and VAT. Ranking by spot alone is not enough. Since elafgift fell to 0.008 DKK/kWh for
2026–27, the tariff's swing from night to the 17–21 winter peak (0.106 to 0.956 DKK/kWh excl. VAT
at Radius) is as large as the typical daily spot spread. That tariff structure alone, which a plain
midnight timer captures, is worth about 600–1,100 DKK a year against charging on arrival. Ranking
tonight's known total prices adds roughly 470–630 DKK more. Buying cheap energy days ahead adds at
most 300–820 DKK, and that is with perfect foresight and before battery wear.

The maintainer finds that forecasts get the trend over about six days right even when their daily
levels are wrong. That held in the only Danish test available: forecasts ranked the coming days
with a Spearman correlation of about 0.7–0.8, and picked the cheapest of six days 50–71 % of the
time, against 17 % by chance. But the test covers one volatile October and one forecast provider,
and it is not Carnot, which the maintainer probably uses.

The planning engine should therefore:
- take total prices in slots of variable length;
- mark forecasts up by a fixed amount that depends on lead time, never by a percentage;
- buy the coming days' expected need through demands spread across the forecast horizon, which is
  where the trend view belongs, rather than through a trend switch or a price percentile;
- keep that extra stored energy below a precautionary ceiling of about 55–60 % SoC, where battery
  wear steps up;
- put the partly used slot in the most expensive hour chosen, and price each session start;
- accept targets that are overdue;
- give the integration charging windows to enforce, not car commands that an Enyaq on core Home
  Assistant cannot carry out.

Most of the 29 decisions stand. D16, D19, D20, D22, D26 and D28 should change, and O1, O2, O4, O7,
O8, O9, O11 and O12 can now be answered. The facts about prices, tariffs and Home Assistant were
re-opened at their sources and hold. Three things rest only on small samples or on reasoning: the
size of the forecast markup, the money in O1, and every Enyaq-specific physical number. The
maintainer's own logs are the cheapest way to settle them.

## Grid tariffs make a midnight timer worth more than any optimiser

**The total price, not spot, decides which hours are cheap.**
- Elafgift is 0.8 øre/kWh "fra 1. januar 2026 til 31. december 2027"
  ([skat.dk](https://skat.dk/erhverv/afgifter-paa-varer-og-ydelser-punktafgifter/nyhedsbrev-afgifter/midlertidig-nedsaettelse-af-elafgiften-i-2026-og-2027)).
  With Energinet's 0.115 DKK/kWh, the part that is flat over the day is only **≈0.12 DKK/kWh excl.
  VAT**, about a tenth of an average total.
- The variable part is the grid company's "Nettarif C" tariff: low load 00–06, high load 06–17 and
  21–24, peak 17–21. Winter rates run from 1 October at most grid companies
  ([Forbrugerrådet Tænk](https://taenk.dk/forbrugerliv/bolig/nettariffer-betydning-for-samlet-elpris)).
- Radius charges 0.106 / 0.319 / 0.956 DKK/kWh excl. VAT for low / high / peak in winter 2026/27
  ([DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist)). The night-to-peak
  swing is **1.06 DKK/kWh incl. VAT**.
- In 2026 the median daily max–min spread of the hourly total incl. VAT was 1.62 DKK/kWh (DK1) and
  1.72 (DK2). Spot alone spreads about 1.0 DKK/kWh excl. VAT ([price note §5][pc]).
- Ranking by spot while being billed the total costs **185–217 DKK/yr** more than ranking by the
  total. On about 70 % of nights the cheapest spot quarter between 17:00 and 07:00 falls outside
  the 00–06 low-tariff block ([price note §5][pc]).
- The red-team panellist re-opened every one of these figures, at skat.dk, in DataHub and at Tænk,
  and confirmed them ([red team §1][rt]).

**Most of the money comes from the cheapest step.** The headline saving of about 1,400–3,000 DKK/yr
(roughly 40 %) is measured against plugging in at 17:00 and charging at once. The red team
recomputed it to within 0.3 %. It also found that most of it is captured by a fixed timer starting
at midnight ([price note §5][pc]; [red team §1][rt]). The table orders the sources of value. Its
figures are own calculations in the notes, on DayAheadPrices and DatahubPricelist data for
2025-10 to 2026-10, with the car plugged in every night.

| Source of saving | DKK per year | Basis and confidence |
|---|---|---|
| Tariff-aware timing: a midnight timer against charging at 17:00 (6 kWh/night, 2026) | ≈730 (DK1) – 1,090 (DK2) | Own calculation ([price note §5][pc]); high |
| Ranking tonight's known **total** prices against the midnight timer | ≈470–630 | Recomputed by the red team ([red team §1][rt]); high |
| Ranking on spot instead of the total: the loss | 185–217 | Own calculation ([price note §5][pc]); high |
| Stored energy across days, **perfect foresight**, with 7.5 / 15 / 30 kWh of headroom | 300–330 / 505–540 / 770–820 | Exact DP on a year of totals ([economist C1][me]); an upper bound |
| The same with a percentile fill rule (O1 c) | 58–173 | Same experiment; about 1/5 of the oracle for the same stock |
| Battery wear if that stock sits above the ageing step | ≈350–2,000 (economist) to ≈500–5,500 (battery engineer) | Reasoning on 18650-cell data and pack prices ([economist C1][me]; [battery §1][be]); low |
| Choosing quarters rather than hours, **only on a quarter-hour product** | ≈45–75 | Own calculation ([price note §3][pc]); high |
| Exact DP over the corrected greedy, on Danish totals | median ≈0; worst week 0.42 EUR (red team) to 9.3 DKK (optimisation engineer) | Re-run and new experiments ([red team §1][rt]; [optimisation E1][oe]); high |

**What the table means for the engine.**
- Its first job is not cleverness. It must receive the right number. D3, prices as opaque numbers,
  stands only if `price` is documented as the **marginal cost per wall kWh, every per-kWh component
  included, on the same basis for known and forecast slots**.
- Under D13, putting that number together is the integration's job. That is harder than it looks.
  - Tariffs change more often than every half-year. Dinel has a separate April step, Zeanet changed
    on 2026-09-01, and TREFOR El-net Øst changes on 2026-12-01.
  - A TREFOR El-net row from 2027-01-01 prices 00–03 at the high rate
    ([DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist)). That moves the
    period boundaries, not just the levels.
  - The Home Assistant price integrations deliver different things. Energi Data Service optionally
    adds tariffs. Strømligning's forecast sensors explicitly exclude "Tariffs, taxes, and supplier
    surcharges" ([Strømligning README](https://raw.githubusercontent.com/mtrab/stromligning/main/README.md)).
    Core Nord Pool excludes VAT and other costs
    ([HA docs](https://www.home-assistant.io/integrations/nordpool/)).
  - A total-price series joined to a spot-only forecast shows a false price cliff where the forecast
    begins ([HA data note][ha]). The adapter must refuse to mix the two bases.

**Negative prices rarely reach a Danish household.**
- Spot was negative in 2.5 % of DK1 quarter-hours and 1.1 % of DK2's over the 13 months to
  October 2026.
- The total was negative in **2 DK1 quarter-hours and never in DK2**. The minimum total was −0.075
  (DK1) and +0.205 DKK/kWh (DK2) ([price note §4][pc]). The red team recomputed this ([red team
  §1][rt]).
- Inside the 17:00–07:00 window the total was never negative in either area ([economist][me]).

D25 should stay, because the engine must not clip at zero, but it needs no special rule. The
scheduling note argued that negative prices contradict O1's lean towards "never". That argument
used spot-only 2025 data, when 6.3 % of DK1 hours were negative. With Danish tariffs in the price,
the gap it measured disappears ([red team §2][rt]).

**Quarter-hour prices matter for correctness, not for money.**
- Day-ahead prices for DK1/DK2 have been set per 15 minutes since delivery day 1 October 2025
  ([APG](https://markt.apg.at/en/news-press/sdac-go-live-of-15-minute-market-time-unit-in-day-ahead-market-coupling-successful-as-of-september-30-2025/);
  [DayAheadPrices metadata](https://api.energidataservice.dk/meta/dataset/DayAheadPrices)).
- Grid tariffs stay hourly.
- Households on the default variable product are billed "et simpelt gennemsnit" (a simple
  average) of the four quarters in each hour
  ([Tænk](https://taenk.dk/forbrugerliv/bolig/flere-elpriser-i-doegnet-giver-minimale-besparelser)).
- For them, choosing quarters inside an hour earns nothing. Even on a quarter-hour product it earns
  only about 45–75 DKK/yr ([price note §3][pc]).

O11 should therefore be closed in favour of a `PricePoint` with an `end` (or a duration) and mixed
15- and 60-minute slots. The integration passes hourly totals for hourly-billed households, and
quarters only where they are both billed and known. The API layer then checks continuity in
absolute time, because DST days have 92 or 100 quarters ([economist C4][me]). The red team points
out that the Home Assistant and prior-art notes overstate this as a question of savings. It is a
question of a correct contract ([red team §2][rt]). Confidence: high.

**D28 should leave the engine.**
- A charger's own price automation may compare its threshold with **spot**. It would then charge
  at 17–21 on a cheap-spot evening that the peak tariff makes about 1.06 DKK/kWh dearer
  ([price note §7][pc]).
- No charger integration exposes its threshold or its price basis.
- Two controllers then fight. Zaptec's Resume only undoes its own Stop, and Easee's "smart
  charging" LED disables its plans
  ([Easee developer](https://developer.easee.com/docs/api-smart-charging);
  [Zaptec README](https://raw.githubusercontent.com/custom-components/zaptec/master/README.md)).
- Step 4 of the decision order would also hide the plan in exactly the hours it fires.
- "Charge whenever cheaper than X" can be expressed inside the engine's own objective (see the
  next section).

The economist and the control/UX engineer both recommend dropping it ([economist D28][me];
[control/UX §7][cu]). Confidence: medium, because nobody could read the chargers' own price basis.

## Forecasts rank days well even when their levels miss by a third

### Error is additive and flattens after the first forecast day

**Known and forecast prices.** Tomorrow's prices are published around 12:45 CET
([Nord Pool](https://support.nordpoolgroup.com/support/solutions/articles/8000077444-about-the-day-ahead-auction-in-nordics-baltics))
and are in Energi Data Service's API by 13:00–14:00. So the part of the horizon with known prices
swings between about 11 and 35 hours over the day. Beyond that, Danish Home Assistant users have
two free forecasts:
- **Carnot**, through the Energi Data Service integration. It gives a point forecast with a free
  key and no published accuracy
  ([connector code](https://github.com/MTrab/energidataservice/blob/master/custom_components/energidataservice/forecasts/carnot/__init__.py)).
- **elpriser.org**. It publishes a median with P10/P90 for D+2 to D+9, and a backtest
  ([OpenAPI](https://elpriser.org/api/openapi.json)).

**Error size.**
- research.md's "MAPE of roughly 8–11 %" could not be found again. MAPE is the wrong metric when
  prices sit near zero ([Lago et al. 2021](https://arxiv.org/abs/2008.08004)).
- elpriser.org's backtest MAE is 149 / 179 / 197 DKK/MWh at D+2 / D+5 / D+9 for DK1, **23–32 % of
  the mean price** ([OpenAPI](https://elpriser.org/api/openapi.json)).
- A three-week live check gave 227–357 DKK/MWh. Adding two more high-price days moved it to 284–419
  ([forecast note §2][pf]; [red team §1][rt]).

**Error growth with lead time.** Error grows roughly as t^0.2–0.3: far slower than √t, and nothing
like linear ([forecast note §3][pf]). The evidence:
- Germany ([Ghelasi & Ziel](https://arxiv.org/abs/2406.00326));
- Sweden's SE3 ([Kjellergren & Lindqvist Sabel 2026](https://lup.lub.lu.se/student-papers/record/9244798/file/9244801.pdf));
- the Danish backtest.

**Error size does not follow the price level.** In the forecast archive, the cheapest quartile of
forecasts had the largest absolute error: 347 DKK/MWh in DK1, against 234 in the dearest quartile
([forecast note §4][pf]).

These findings settle the **shape** of D20/O4, with high confidence:
- no markup on published prices;
- an **additive** markup in the caller's price units, never a percentage. A percentage makes a
  negative forecast more attractive and gives a zero forecast no markup at all;
- a large first step at the first forecast hour, rising by about a third over the following week,
  then flat.

Three refinements from the panel hold up:
- **Count lead time from the last published slot, not from `now`.** A forecast for tomorrow night
  is a D+2 forecast whether it is read at 13:05 or at 23:00 ([economist C2][me]).
- **Do not split each price into a known and an uncertain part.** An additive markup is already
  blind to the known parts (tariffs, Energinet, elafgift).
- **Do not scale the markup by the spread of the call's known prices.** In Denmark that spread is
  mostly tariff. It would double every 1 October with no change in forecast error ([economist
  C2][me]).

**The size of the markup is not supported by any evidence yet.**
- The forecast note first proposed 0.12–0.16 DKK/kWh from an optimiser's-curse bias, then revised
  this to 0.05–0.10.
- The red team re-ran the bias with two more days of actuals: it moved from 114–158 to 184–224
  DKK/MWh in DK1. Roughly half of it was a plain under-forecast of the whole period, and it was
  measured within each day rather than on the cross-day choice that the markup governs ([red team
  §1][rt]).
- Two experiments agree on direction:
  - the forecast note's simulation tolerated 0–100 DKK/MWh and was hurt at 300 ([forecast note
    §7.6][pf]);
  - the optimisation engineer's E5 replay found 0.05–0.10 DKK/kWh incl. VAT best and 0.30 harmful
    ([optimisation §3][oe]).
- The Swedish thesis found the plain median forecast (λ = 0) near-optimal in three of four setups.
  Scoring towards P90 cost 4–18 EUR a year
  ([Kjellergren & Lindqvist Sabel 2026](https://lup.lub.lu.se/student-papers/record/9244798/file/9244801.pdf)).
- A stochastic MPC beat a deterministic point-forecast MPC by only about 1 %
  ([Fernández-Zapico et al.](https://arxiv.org/html/2504.00685v2)).

The consistent reading: **re-planning on point forecasts gets most of the value, and the markup
should be small**. The engine should ship no default, because an additive number carries a
currency (D3, D4). The integration should ship about 0.08 DKK/kWh incl. VAT from the first
forecast hour, 0.10 from D+4 and flat from D+7, marked as uncalibrated ([economist C2][me]).
Confidence: low on the number. It rests on 21–23 overlapping decisions in one month.

### The maintainer's trend view survives its first test

The maintainer finds from long use that forecasts get the direction of the next ~6 days right even
when daily levels are off. The forecast note tested this with the 23 elpriser.org runs of October
2026 ([forecast note §7][pf]).

**What the test found.**
- The forecast called the direction of each day against the last known day right in **73–100 %
  (DK1) and 59–90 % (DK2)** of cases at D+2..D+7. The weekday-last-week baseline scored about
  50–70 %.
- It correlated with actual daily means at **Spearman 0.70–0.80**. The baseline correlated at about 0.
- It picked the actual cheapest of the next six days **50–71 %** of the time, against 17 % by chance.
- Direction was a coin flip for forecast moves below 100 DKK/MWh. Above 300 it was right 87–93 % of
  the time.
- Both facts can be true at once. Levels miss by 230–400 DKK/MWh, but days differed from one
  another by about 340 DKK/MWh on average in that window. The **order** of days survives whenever
  the true differences are larger than the error.

**What the test cannot carry.** The red team reproduced every number. It also stresses that the
runs overlap, so the independent evidence is about three weeks of prices, and that the
Pesaran-Timmermann statistics assume an independence these data lack ([red team §1][rt]).

The economist adds the sharper caveat:
- The October window was unusually volatile. The mean daily move was 350 (DK1) and 333 (DK2)
  DKK/MWh, against 203 and 209 over the year.
- A third of all day pairs in the year moved by less than 100 DKK/MWh, which is coin-flip
  territory ([economist, weakest claims][me]).
- His counterpoint favours the maintainer: in calm weeks there is also little money at stake. The
  right metric is accuracy weighted by the size of the move, not the hit rate.
- Carnot, the forecast the maintainer probably used, was not tested at all: its API needs a
  personal key.

The view is **supported in direction, consistent with the level errors, and uncalibrated**.
Confidence that it holds year-round for Carnot: low to medium, until his logs say otherwise.

**How the trend should enter the engine.** The forecast note simulated a binary switch: "trend up
→ fill now". It recovered 62–80 % of the perfect-foresight saving. Charging "until the next
forecast-cheaper day" recovered 80–97 % ([forecast note §7.6][pf]). The red team rightly notes that
the switch tested was the note's own coarse design, not the maintainer's rule
([red team §1][rt]). The optimisation engineer then replayed 21 real daily decisions with the
elpriser forecasts, the Danish total price and a tapering 75 kWh car ([optimisation E5][oe]):

| Policy | Share of the perfect-foresight saving |
|---|---|
| Daily targets chained across the forecast horizon, markup 0.05–0.10 | 66–78 % |
| A flat value on stored energy | 4–47 % |
| A percentile fill rule | −5 to −30 % (worse than buying each day's need) |

All four panellists who took a position on the mechanism agree. The trend is used best as **day
ranking inside the ordinary cheapest-first choice**, not as a switch.

One condition, which the economist identified, is easy to miss. A markup and a ranking act only on
energy the engine has been told it needs. With no demand in the input for D+3, the engine buys
nothing for D+3, however clearly the trend rises ([economist C2][me]). The trend view therefore
needs the coming days' consumption **in the input**.

### How much to charge beyond tonight's need: the panel's answers to O1

O1 is the one question on which the professions still disagree. The red team's verdict is fair:
none of the positions rests on Danish measurements of what extra stock is worth after wear, so O1
is partly a value judgement between availability, wear and a few hundred kroner ([red team
§2][rt]).

| Position | Holder | Strongest evidence | Weakness found |
|---|---|---|---|
| (a) Never | Physics note | Calendar ageing steps up at about 60 % cell SoC in Keil et al. ([IOP](https://iopscience.iop.org/article/10.1149/2.0411609jes)) | Over-transferred: 18650 cells at 25–50 °C; step not located in MEB displayed SoC ([red team §3][rt]). Forgoes most multi-day value: E5 paid 1.14–1.24 DKK/kWh against 0.71–1.04 for the chain ([optimisation §3][oe]) |
| (c) Percentile, up to 80 % | Driver note | Unannounced trips cause overrides (Electric Nation) | Lost money in E5; 1/5 of the oracle's money for the same stock ([economist][me]); parks the car in the high-fade plateau. The "Danes fill up" reading of Ziras et al. is a misread ([red team §1][rt]) |
| (b) User price threshold | Prior art | evcc, openWB, EV Smart Charging all ship one ([prior-art note][pa]) | Absolute DKK thresholds go stale at every tariff change |
| Fill when the price is negative | Scheduling note | Spot-only 2025 data | The Danish total is almost never negative ([red team §2][rt]) |
| τ (a value per stored kWh) plus a surplus SoC ceiling | Economist | Separates "how much is the energy worth" from "how high may it sit" | A flat τ keeps buying beyond the need; E5's flat value captured only 4–47 % |
| Expected cost of the coming days' need (soft demands plus a concave terminal value plus a wear cost) | Optimisation engineer | E5: 66–78 % of the oracle | 21 decisions, one month, no wear term in the run |
| Next-cheaper-day rule capped at 55 % | Battery engineer | Keil's 10–60 % band is one plateau, so filling below it costs no extra ageing | Wear value is reasoning: 1,000–3,700 DKK per capacity point |
| Floors-only in the engine; caller expands departures over the horizon; opportunistic ceiling 60 % | Control/UX engineer | Reproduces the trend view with no new engine rule | Hard targets on assumed days may report false `PARTIAL` |

**These positions converge more than they differ.**
- Every panellist rejects the percentile (c) and a fixed threshold as the default.
- Every one routes the trend through forecast prices in the ranking.
- Every one caps opportunistic stock below the battery's step, at 55–60 %, rather than at
  `default_target_soc`.
- They disagree on **where the coming days' need is expressed**: hard targets generated by the
  caller (control/UX), soft demands in the engine (optimisation), or a value τ plus a ceiling
  (economist).
- The economist's τ, computed as "the replacement price until the next cheaper day" and capped at
  "floor plus use until then", is a two-step concave terminal value. It is the optimisation
  engineer's formulation in its simplest form.

**Recommendation for O1.** Replace the lean towards (a) with a mechanism, while keeping (a) as the
engine's default when nothing extra is supplied.
- The integration expands the usual departures over the whole price-plus-forecast horizon (D27),
  each with an absence whose energy is learned from the car's history.
- Days beyond the next real departure are marked **soft**, so that a wrong assumption never makes
  the plan `PARTIAL`.
- Forecast slots carry the small additive markup.
- Stock held for soft demands may not exceed an optional `surplus_max_soc` ceiling. The integration
  defaults it to 55–60 %; the engine's default is `None`.
- An optional concave `stored_energy_value_steps` covers energy beyond the horizon and lets a user
  enter a price threshold as an opt-in (option b).

Confidence: medium that this mechanism is right; low on the money (realistically perhaps half of
the 300–820 DKK oracle) and on the ceiling's value. The ageing step's position in the Enyaq's
displayed SoC is unknown; KIT's graphite/NCA cells showed small effects below 80 %
([physics note §5][cp]).

## Exact optimisation earns its place through the objective, not the price

**D22's selection rule is sound. What it lacks is a rule for the partly used slot.**
- The scheduling note reported "D22 as written" at +7.6 % median and +63 % worst on 60 real weeks
  ([scheduling note §1][sa]).
- The red team re-ran the code. The whole gap comes from a **chronological trim**: cutting the last
  hours in time order, as a charge limit would. motor.md never specifies that trim. With a
  price-ordered trim the same selection had zero gap in 60 of 60 weeks. With Danish tariffs added
  to the price, even the chronological trim fell to 2.3 % median ([red team §1, §5][rt]).

The defensible statement is narrower than either note's:
- Cheapest-first, with each slot given to the earliest target still short, is **exact at constant
  power** when the partial slot is the most expensive chosen one, shortened by starting late.
- This follows from the greedy theorem on matroids
  ([Rochester CSC 282 slides](https://www.cs.rochester.edu/~gildea/csc282/slides/C17-amortized.pdf)).
  It was confirmed in 0 of 4,000 random instances and 0 of 300 Danish week-cases
  ([scheduling note §1][sa]; [optimisation E1][oe]).
- It is also what evcc does: "start as late as possible"
  ([evcc planner.go](https://github.com/evcc-io/evcc/blob/master/core/planner/planner.go)).

**With a tapering car the greedy is no longer exact, but the loss is small.** On Danish totals it
gave a median of 0.00–0.03 %, a p90 of 0.9–1.5 % and a worst week of 8.6–15 %, up to about 9 DKK
([optimisation E1][oe]). The red team's tariff variant gave a worst case of 7.1 %, or 0.42 EUR a week
([red team §1][rt]).

That settles O9: drop `is_top_up`, never cut a partial slot with a charge limit, and shorten the
dearest chosen slot. Confidence: medium-high.

**Whether to replace the greedy with an exact dynamic programme is a real disagreement.**

The optimisation engineer's case for the DP (medium-high confidence) is about what the objective
must carry, not about price ([optimisation §1][oe]). The other notes ask it to carry:
- a cost per session start;
- a charging overhead that makes slow charging dearer;
- soft demands and a terminal value for O1;
- a wear holding cost;
- caps that limit charging in the segment before a target;
- a best-effort shortfall;
- the markup and the late tie-break.

A price ranking can express almost none of these. Each one bolted onto a greedy is a new place for
a missed-target bug, and the prior-art note found that every missed-target bug in evcc lived in
exactly such add-on rules ([prior-art note][pa]).

The DP over (slot, SoC on a 0.25 kWh grid, on-state) has these properties:
- it carries all of those terms in one O(T·S·2) pass;
- it replaces pass 1, pass 2 and D23's check;
- it is deterministic with a fixed tie-break. emhass's HiGHS solver, by contrast, stops within a 1 %
  MIP gap ([emhass optimization.py](https://github.com/davidusb-geek/emhass/blob/master/src/emhass/optimization.py)).

The red team's case against (it found the evidence "weaker than stated") is also strong:
- On Danish totals the DP gains little money ([red team §5][rt]).
- Nothing yet shows that chaining, forecasts or a DP add a measurable amount on top of ranking
  tonight's known prices for a typical commuter.
- The physics note doubts the 11 → 7.5 kW taper is real. Without a taper, the corrected greedy is
  exact.

**The recommendation is conditional.** If O1's soft demands and D19's start cost are adopted, as
recommended here, the DP is the only standard-library method that carries them, and it should
replace pass 2. If the maintainer keeps floors-only and drops the start cost, the corrected greedy
suffices. Either way, both the corrected greedy and a brute-force DP become test oracles, and the
counterexamples CE-A to CE-D become regression tests ([scheduling note §7][sa]). Confidence:
medium.

**Performance.** motor.md §7 sets a budget of 10 ms for `plan()`. That budget cannot hold for
quarter-hour input in pure CPython.

| Setting | Timing | Source |
|---|---|---|
| Full DP with every term on, 168 hourly slots, 0.5 kWh grid | 13 ms | E2 ([optimisation][oe]) |
| Same, 0.25 kWh grid | 26 ms | E2 |
| A mixed horizon: 35 h of quarters, then hours | 41 ms | E3 |
| 672 quarter-hour slots | 100 ms | E2 |
| The red team's re-timing of the plain DP | consistent with the above | [red team §1][rt] |

Coarser grids are no free speed-up. At 15-minute slots, grids of 0.5 kWh or more produced plans
that missed a floor once re-simulated, unless rounding is conservative ([optimisation E3][oe]).
Restate the budget as about 50 ms on desktop CPython, called through Home Assistant's executor.
The HA developer documentation requires heavy computation to run off the event loop in any case
([HA blocking operations](https://contributors.home-assistant.io/core/internals/blocking-operations/)).

That answers O8. Under a DP, `simulation_step_minutes` only sets the precision of a precompute that
takes 1–2 ms. The real precision knob is `soc_resolution_kwh`: 0.25 kWh, rounded conservatively.
Under a greedy, the step must divide 15 minutes, so 3 or 5, not 6. The open risk is Raspberry-Pi
hardware, which nobody timed.

**A start cost tames fragmentation.** The optimisation engineer's E4 re-planned 120 nights every 15
minutes on quarter prices. Results:

| Engine setting | Session starts per night | Cost |
|---|---|---|
| No start cost | 3.0 | — |
| A start overhead of 0.3 kWh × price, with `is_currently_charging` as the initial on-state | 1.2 | +0.19 % |

Re-planning itself added almost no churn ([optimisation E4][oe]). A hard minimum session is worse:
evcc's "slot too short" rule made a plan needing about 7 minutes miss its target, until a fix in
October 2026 ([evcc #34466](https://github.com/evcc-io/evcc/issues/34466)).

D19 should become a soft `start_overhead_kwh`. Confidence: medium-high. The result comes from one
experiment on quarter prices, and the right kWh value is unmeasured.

**Missed targets and missing prices.**
- **A missed target must not vanish.** Under D10 a call after `target.at` no longer sees the
  target. After an overrun, evcc switched to the next day's plan and stopped at 70–90 %, until a
  plan lock fixed it ([evcc #24339](https://github.com/evcc-io/evcc/issues/24339)).
  - O10's proposal to "skip with a warning a target whose buffer starts in the past" would recreate
    that bug.
  - The engine should accept **overdue** targets, charge them as soon as possible within their
    cap, and report `TARGET_OVERDUE`.
  - The integration persists the target until it is met, the car is unplugged, or the user
    dismisses it ([optimisation §2][oe]; [control/UX §4][cu]).
- **The plan must cover all available time**, not only the hours with prices, as motor.md §6.2 now
  says.
  - Unpriced slots get a pessimistic decision price.
  - Danish tariffs are published months ahead, so the integration can always pass tariff plus a
    spot proxy, marked `is_forecast`. That keeps the 00–06 block, about half the value, when spot
    is missing.

Confidence: high for the engine side, medium for the fallback prices.

## The Enyaq's physics are mostly unmeasured; its cells prefer under 60 %

**Efficiency falls at low power, and a constant plus an overhead captures that.**
- Kia e-Niro (one car on a dynamometer, 21–23 °C): 87.2 % wall-to-battery on three phases at 16 A,
  80.3 % on one phase ([Reick et al. 2021](https://arbor.bfh.ch/bitstreams/67fb6c67-ed54-4535-a0fb-f43b55a2a3f5/download)).
- ADAC 2026: under 7 % loss at an 11/22 kW wallbox for five cars including the MEB ID.7, and 9.1–12.8 %
  at reduced power
  ([firmenauto.de on ADAC](https://www.firmenauto.de/management/fuhrparkmanagement/e-auto-ladeverluste-adac-vergleich-steckdose-wallbox-fuenf-elektroautos/)).
- ADAC estimates 100–300 W of control-unit draw while charging
  ([autohaus.de on ADAC](https://www.autohaus.de/nachrichten/autohandel/adac-test-stromverluste-durch-schnellladen-vermeiden-3231295)).
- The model `P_batt = η·P_wall − P_aux` with η ≈ 0.93 and P_aux ≈ 0.2 kW reproduces every one of
  these: effective efficiency is 0.91 at 11 kW, 0.88 at 4.1 kW and 0.79 at 1.4 kW ([battery
  §2][be]).

D16 should gain an optional `charging_overhead_kw` (default 0), and state that curves, energy and
cost are wall-side. D26 should be split: drain while parked stays out of the model, because each
call reads a fresh SoC; the overhead while charging goes in. For the Enyaq at 11 kW, use 0.90–0.93,
not the e-Niro's 0.87 or evcc's generic 0.85. Confidence: high for the structure, medium for the
values.

**Partial slots: full power for part of the slot.** IEC chargers cannot signal less than 6 A, which
is about 4.1 kW on three phases ([Reick et al.](https://arbor.bfh.ch/bitstreams/67fb6c67-ed54-4535-a0fb-f43b55a2a3f5/download)),
and low current is the least efficient way to charge. So a partly used slot should run at full
power for part of the slot. That is also the evcc rule above. Switching phases on MEB needs a
session restart and belongs to solar control (D13).

**The 11 → 7.5 kW drop is unexplained, and must not go into the curve until it is.** Three causes
fit the number, and only per-phase logging can tell them apart:
1. **A car-side current cut on all three phases**, about 16 → 11 A. The battery engineer judges this
   most likely, possibly temperature-linked or pacing towards a departure time.
2. **A phase drop under voltage sag.** Two phases × 16 A needs 235 V to give 7.5 kW, and the MEB
   forum reports say "just under 7 kW".
3. **A charger-side limit**, such as load balancing ([battery §2][be]; [physics §1][cp]).

The red team classes the phase-drop explanation as unsupported, though correctly labelled as a
hypothesis ([red team §5][rt]). The battery engineer's test needs two or three logged sessions, one
on a cold night:

| What the log shows | Cause | Where it belongs |
|---|---|---|
| All three phases fall together at a repeatable SoC, while the offered current stays at 16 A | Car-side limit | `car_power_soc_steps` |
| One phase goes to 0 A after it sags | Phase drop | Under-delivery, which the buffer absorbs |
| The offered current falls first | Charger or load balancing | Caller-side handling (D13) |
| The drop starts at a clock time | Car pacing to its timer | Set the car to immediate charging |

Until then the motor.md example `[(65, 7.5)]` is illustrative only.

**Cold changes efficiency as well as power.**
- The only cold-efficiency data are for DC: 39 % at −25 °C against 93 % at +25 °C
  ([JRC, Trentadue et al. 2018](https://ses.jrc.ec.europa.eu/sites/default/files/publications/evaluation_of_fast_charging.pdf)).
- Škoda's representative says the pack is heated to 23 °C while charging at a station, and advises
  "Always set your departure time"
  ([Rehak thread](https://threadreaderapp.com/thread/1615643925703786496.html)).

D6 should therefore cover efficiency and overhead as well. The caller learns one number, k = wall
kWh per % SoC (about 0.84 for a new Enyaq 85), per temperature band from its own meter-versus-SoC
history ([battery §4][be]).

**Battery wear is a step, not a slope, and the step sits below the default target.**
- Keil et al. found calendar ageing in plateaus, with "a marked step … at about 60 % SoC for the NCA
  and NMC cells" and a steep further rise at 100 % for NMC
  ([IOP abstract](https://iopscience.iop.org/article/10.1149/2.0411609jes)).
- Volkswagen's MEB guidance:
  - "For daily usage, Volkswagen recommends setting the charging target at 80%";
  - 100 % before long trips, "driving off as soon as possible after charging is completed";
  - parking for more than 12 hours at 30–80 %
    ([VW Canada](https://www.vw.ca/en/electric-vehicles/about-electric-vehicles/battery-tech-and-maintenance.html)).
- Real fleets lose about 1.5 % a year when mainly AC-charged, and SoC habits matter little "unless
  they spent extended periods close to full or empty charge"
  ([Geotab via Yahoo Finance](https://finance.yahoo.com/news/geotab-data-points-modest-rise-141059571.html)).

The battery engineer values one point of capacity at 1,000–3,700 DKK, from a 10–15 kEUR MEB pack
price ([ecomento](https://ecomento.de/2022/02/24/elektroauto-batterie-ersatz-ist-teuer/)) and a
warranty threshold of 70 %. He estimates that parking above the step rather than below it costs
0.5–1.5 points a year in a Nordic climate, about 5.5 DKK per day held above the step. Storing
energy above the step then pays only for a forecast gain of about **0.3 DKK/kWh per day held**
([battery §1][be]). This is reasoning on lab cells and an assumed temperature scaling, so
confidence is low. It still explains why every panellist puts the O1 ceiling at 55–60 % rather than
80 %, and why `default_target_soc` = 80 should remain a cap for trips and one-off charging, not a
nightly target.

**The late tie-break is free, with one condition.** Among equal marked-up prices, prefer the latest
slot. It costs nothing, cuts hours at high SoC, and leaves a warmer pack at departure in winter.
It is also what evcc does ([evcc sort.go](https://github.com/evcc-io/evcc/blob/master/core/planner/sort.go)).

The ADAC's advice to charge straight after driving loses to the 17–21 peak tariff, which costs
about 0.85 DKK/kWh more excl. VAT ([battery §1][be]).

The control/UX engineer's objection stands: the tie-break pushes the last window against the
buffer, leaving no later hour to recover in. Accept it only with two safeguards:
- curves built from a low percentile of observed session power;
- deadline-critical windows that no hysteresis rule may delay ([control/UX §2][cu]).

**Defaults: the professions converge on these.**

| Setting | Driver note | Battery engineer | Control/UX | Recommendation | Confidence |
|---|---|---|---|---|---|
| `default_target_soc` | 80 | 80 (VW, Battery Care) | 80, as a cap, not nightly | **80** | High |
| `default_arrival_soc` | 20 | 20 | 20 | **20**, easy to lower | Medium (reasoning from Franke's 20–25 % unused range, [TU Chemnitz](https://www.tu-chemnitz.de/tu/pressestelle/aktuell/5618/en)) |
| `min_safety_soc` | 10–15 | 20 | 15, and must be below arrival | **15** | Medium |
| `min_idle_soc` | 40–50 | 40 (never above 55) | 50 | **40**; 50 acceptable | Low–medium |
| Opportunistic ceiling (new) | — | 55 | 60 | **55–60**, precautionary | Low |
| `charge_complete_buffer_minutes` | 20 | 20 | 20 | **20** | Medium |

Two reasons decide the close calls:
- **`min_safety_soc` must sit below `default_arrival_soc`.** Otherwise every trip that goes exactly
  to plan lands on the safety floor and triggers price-blind charging at peak tariff ([control/UX
  §3][cu]). O10 should warn about it.
- **`min_idle_soc` = 40 rather than 50 leaves headroom below the 55–60 % ceiling.** That headroom is
  where the multi-day money lies: the economist puts it at 10–25 points ([economist C1][me]).

The red team adds a correction. The driver note's case for a high idle floor leaned partly on a
misreading of Ziras et al.: the 40 % of re-plugs within 24 hours is measured per charger and peaks
at 24 hours. It does not show that cars skip days ([red team §1][rt]). The remaining case is
Electric Nation:
- overrides in 2.5 % of sessions after the novelty phase;
- mostly for an unplanned extra journey;
- a third of users pressed it only to test it
  ([Electric Nation Final Report](https://commercial.nationalgrid.co.uk/downloads-view-reciteme/64378)).

That is UK network-managed charging in 2017–19, and its transfer to Danish price control is
unsupported.

Two changes to how `min_idle_soc` applies are recommended at medium confidence ([control/UX §3][cu]):
- it should also be a floor at every departure;
- its deadline should be the expected plug-out (the next departure, else 07:00), not 24 hours.

## Home Assistant can hold a charger but cannot wake an Enyaq

**No charger has a clean, symmetric start and stop.**
- **Zaptec** starts charging on plug-in by default. Its "Resume" "will only start charging if the
  charger was stopped by a 'Stop charging' command". It also recommends changing the available
  *current* at most every 15 minutes
  ([Zaptec README](https://raw.githubusercontent.com/custom-components/zaptec/master/README.md)).
- **Easee** says "Pause and resume are the commands you should use, not start and stop", and resets
  its charger dynamic limit "after plugging in a car or rebooting the charger"
  ([easee_hass wiki](https://raw.githubusercontent.com/wiki/nordicopen/easee_hass/ChargingControl.md);
  [Easee developer](https://developer.easee.com/docs/current-limits-and-control)).
- **OCPP**: turning the Charge Control switch back on "does not force a new session to start"
  ([OCPP guide](https://home-assistant-ocpp.readthedocs.io/en/latest/user-guide.html)).

The control/UX engineer's conclusion follows, at high confidence ([control/UX §1][cu]):
- The engine's control contract should be the `windows` and `should_charge_now`.
- The integration asserts a level state, ALLOW or HOLD, on every cycle and every charger event, and
  verifies it by reading power back.
- Edge commands such as `START_CHARGING` and `STOP_CHARGING` can be lost. They become informational.
- By default the HOLD is reactive, applied after plug-in. Its leak is at most about 0.4 DKK per
  plug-in, and it fails "wet": with Home Assistant down, the car still charges.

**The Enyaq's data reality.** In Home Assistant 2026.11 the core Škoda integration replaces
MySkoda, whose README announces it "will stop working in October 2026"
([MySkoda README](https://raw.githubusercontent.com/skodaconnect/homeassistant-myskoda/main/README.md)).
The core integration:
- is read-only, with sensors only;
- polls every 5 minutes;
- exposes no capture timestamp for SoC;
- has no wake, refresh or charge-limit control
  ([HA next docs](https://next.home-assistant.io/integrations/skoda/);
  [sensor.py](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/skoda/sensor.py)).

The Škoda API behind it has no wake endpoint and allows 20 requests per hour per VIN
([Škoda Public API](https://public.api.connect.skoda-auto.cz/docs)). The red team re-opened all of
this ([red team §1][rt]). It has three consequences:
- `WAKE_UP_CAR`, `REQUEST_SOC_REFRESH` and `SET_CHARGE_LIMIT` should leave the engine's action list,
  because D2 forbids commands whose target may not exist. The integration stops at the planned SoC
  by holding the charger, using a SoC it projects from the charger's session energy.
- `car_max_soc` (D18) becomes configuration. The integration infers that the car's own limit was
  reached when the car reports `conserving` while the plan says charge.
- `soc_last_updated` gives way to a `soc_source` (car-reported, projected or assumed). The
  integration detects a reading taken before the last drive by comparing it with the mileage
  sensor ([control/UX §2][cu]).

**O7 has a clear answer: charge first.** "Wake first" never ends on a car that cannot be woken. The
cost of being wrong is bounded: buying a 15 % floor at the worst peak instead of at night costs
at most about 12 DKK ([control/UX §2][cu]). When the last known SoC is below `min_safety_soc`, the
integration should charge at once, bounded by the projected SoC, and re-plan when a fresh reading
arrives. An unknown SoC counts as 0 for the safety rule only, as evcc does
([evcc docs](https://docs.evcc.io/en/features/limits)). Confidence: high.

**The 20-minute buffer covers actuation, not a wrong power model.**
- The driver note cited Octopus's "up to 30 minutes" as actuation lag. At source it is a delay in
  detecting a plug-in through the car's API ([Octopus FAQ](https://octopus.energy/intelligent-faqs)),
  so it does not size D8.
- Start lag through a charger is minutes, which 20 minutes covers.
- A failure to start needs a person. Verifying at the first window of the night catches it hours
  before departure.
- Planning 11 kW and getting 7.5 kW on a 20 kWh need finishes **51 minutes late**. No buffer covers
  that. Learned curves and re-planning on projected SoC do ([control/UX §2][cu]).

Keep D8 at 20 minutes. Whether "inside the buffer and still short → charge anyway", evcc's
`planDeadlineCritical`, should become an exception to D8 is the maintainer's call
([optimisation §2][oe]).

**Manual controls need no engine change (O12).**

| Control | Behaviour | Engine mapping |
|---|---|---|
| "Charge now to X %" | Session-scoped; ends at unplug; banner and cost hint, following Electric Nation and evcc's "1x" | A session-scoped override of `min_safety_soc` to X |
| "Pause until …" | Always with an expiry | A caller-side HOLD |
| One-off "ready by" | Dated target | A `ChargeTarget` |
| Smart charging off | Hands off: ALLOW for good, so the charger behaves as without the integration | Engine not called |

Sources: [control/UX §4][cu]; [evcc docs](https://docs.evcc.io/en/features/modes). Confidence: high,
except whether an explicit pause should beat the safety floor, which is medium-low.

**What the user must see at plug-in.** Four things build trust: ready-by status with any shortfall,
the next charging start, the expected cost, and the SoC with its source. A plan that starts at
03:00 otherwise looks broken at 22:00. A Danish driver organisation has asked operators to explain
slow charging better ([Mobilsiden](https://mobilsiden.dk/?p=287502); [driver note §5][dr]). D29 and
the per-target output should therefore carry the shortfall and the next start (part of L1).

**O2:** add an optional `min_soc_at_end` on `AbsenceWindow`, defaulting to `default_arrival_soc`.
The interface never asks for it. Confidence: high.

## Conclusion

The research turns the question from "which algorithm?" into "which number?".

**Where the money is.**
- The Danish household's saving is decided first by the grid tariff, which a midnight timer
  already captures.
- Next, by ranking tonight's known total prices, which the engine as designed already does.
- Only third, and by a few hundred kroner, by anything that needs forecasts, chaining or exact
  optimisation.
- That reorders the work. The integration's price adapter, which must compose the total correctly
  through every tariff change, is worth more than the planner's sophistication. A mistake there,
  ranking on spot or joining a spot-only forecast to a total, costs more than the gap between a
  greedy and a DP.

**What the forecasts give.** The maintainer's trend view is right in a precise sense: forecasts
carry day **ranking**, not day levels. The way to use it is not a trend rule but giving the engine
the coming days' expected consumption, so that ordinary cheapest-first ranking can act on the
forecast. That makes the integration's model of the car's daily use, learned from charger energy,
the hinge of O1. It also makes a battery-wear ceiling necessary, because ranking alone would
happily park the car at 80 %.

**The evidence that is still missing is cheap.** Three gaps are the weakest links: the markup's
size, the Enyaq's taper and efficiency, and SoC staleness. None needs more desk research. All
three can be settled within weeks by logging data that Home Assistant already sees, and the
markup within a season. The integration should therefore log from its first release, before the
engine's defaults are frozen.

## Decision register: every ID the research touches

Verdicts: **keep** (stands as written), **keep+** (stands, with an addition or clarification),
**change** (the text should change), **answer** (an open question that can now be closed),
**open** (still open). "Current text" abbreviates [decisions.md][dec].

| ID | Current text (abbreviated) | Verdict | Recommended change | Confidence |
|---|---|---|---|---|
| D1 | Engine imports only the standard library | keep | The DP is pure Python. networkx would need vendoring; PuLP needs a Rust extension and an external solver ([PuLP docs](https://www.coin-or.org/pulp/main/installing_pulp_at_home.html)) | High |
| D2 | Car- and charger-agnostic; every value arrives with each call | keep+ | The engine emits no command whose target may not exist (wake, refresh, charge limit) | High |
| D3 | kW, kWh, hours, SoC; prices are opaque numbers | keep+ | Document `price` as the marginal cost per wall kWh, every per-kWh component incl. VAT, same basis for known and forecast slots | High |
| D4 | No hardcoded domain values; defaults only for tunables | keep+ | Engine defaults for the markup, start cost, ceiling and terminal value are empty or `None`. Danish defaults live in the integration, marked uncalibrated | High |
| D5 | Never returns text | keep+ | New codes: `TARGET_OVERDUE`, estimated or missing prices, car stopped at its own limit, "a fresher SoC would change the plan", a stock-reason code | High |
| D6 | Temperature, weather, altitude folded into the curves by the caller | keep+ | Also into efficiency and overhead: the caller passes a seasonal k (wall kWh per % SoC) or a winter overhead | Medium |
| D7 | Caps are hard; a target's cap wins; plan to cap and report `PARTIAL` | keep+ | Define a cap as the ceiling on charging in the segment ending at that target, not on SoC carried through it | Medium (reasoning, one harness case) |
| D8 | Completion buffer absolute, global, 20 min | keep | 20 min covers actuation and verification lag. Document that it does not cover a wrong power model. The exception "inside the buffer and short → charge" is the maintainer's call | Medium |
| D9 | Best effort; never break a cap or the buffer; report the shortfall | keep | Implement as a shortfall penalty. In the integration, deadline-critical charging beats every hysteresis rule | High |
| D10 | Pure function; no state | keep | `is_currently_charging` is the initial on-state. Plan lock, missed-target memory and hysteresis stay in the caller | High |
| D11 | Three layers; API validates and corrects | keep+ | The API checks continuity in absolute time, mixed slot lengths, DST days of 92/100 quarters, and overdue targets (accepted) | High |
| D12 | Simulates the charge step by step with both curves | keep+ | Under a DP the simulation precomputes reach and wall energy per SoC state, and produces the reported windows | High (if DP) |
| D13 | Planning function, not a policy engine | keep | Tariffs are composed by the caller: that is half the value. Removing D28 is consistent with this | High |
| D14 | One module per concern; no strategies until a second implementation | keep | `planner` holds the chosen algorithm. The corrected greedy and a brute-force DP live in the tests as oracles | High |
| D15 | `AbsenceWindow` and `ChargeTarget`, linked by the caller | keep+ | Optional `min_soc_at_end` (O2); targets may be overdue; a `soft` flag for assumed future use | Medium-high |
| D16 | Two curves; power = lower × efficiency | change | Add optional `charging_overhead_kw` (`P_batt = η·P_wall − P_aux`). Curves, energy and cost are wall-side. Mark the 11 → 7.5 kW example as unverified | High (structure); medium (values) |
| D17 | `charger_max_session_kwh`, optional | keep | Not examined by the research | — |
| D18 | `car_max_soc`, a hard ceiling | keep+ | On core Škoda it cannot be read, so it is configuration. The integration detects a car-side stop (`conserving`, `SuspendedEV`) and passes the current SoC for the rest of the session | Medium |
| D19 | `min_session_kwh` soft, e.g. 2 kWh | change | Replace with `start_overhead_kwh` × slot price per session start, with the on-state from `is_currently_charging`. Never a hard minimum | Medium-high (E4, one experiment) |
| D20 | Forecast prices carry a markup; costs raw; stepped curve proposed | change | Additive in the caller's units, never a percentage. Zero for published prices; steps keyed on lead time from the last published slot; a large first step, about +30 % to D+7, flat after | High (shape); low (size) |
| D21 | Every warning code has a fixed `params` schema | keep | Covers the new codes | High |
| D22 | Cheapest first over the horizon, in two passes | change | Specify the partial slot: the most expensive chosen slot, shortened by starting late, never cut by a charge limit. Replace pass 2 by an exact DP over (slot, SoC 0.25 kWh, on-state) if the D19/O1 terms are adopted; otherwise keep the corrected greedy. Both serve as test oracles | Medium |
| D23 | Chain feasibility checked in pass 1 | keep | Still reported as `INFEASIBLE_TRIP_CHAIN`; under a DP it is read from V = ∞ | Medium-high |
| D24 | `energy_kwh` required; 0 allowed | keep | — | High |
| D25 | Negative prices supported and used | keep | No special rule. The Danish total was negative in 2 DK1 quarter-hours in 13 months | High |
| D26 | Not modelled: CC/CV, parasitic drain, restart cost, charger offline | change | Split. Parked drain stays out. Overhead while charging goes in through D16; restart cost through D19 | Medium |
| D27 | Weekday patterns and recurrence are the caller's | keep+ | The caller expands usual departures over the whole price-plus-forecast horizon, with learned consumption. This is the precondition for the trend to act | Medium-high |
| D28 | The charger's own low-price automation may charge below `charger_auto_threshold` | change | Remove from the engine and from decision-order step 4. At most an advanced, default-off integration feature | Medium |
| D29 | Output carries `feasibility` and a per-target status and SoC | keep+ | Add the per-target shortfall and the next charging start. Expected cost is already in the windows | Medium-high |
| L1 | Advice in the output, deferred | change | Bring forward: next start, cost, shortfall, and a stock-reason code ("charging to 63 %: Thu–Sat forecast dearer") | Medium |
| L3 | A completion buffer per target, deferred | keep | Still deferred; the caller may raise the global buffer in winter | Medium |
| L4 | Charging back to `min_idle_soc` after the last target, deferred | change | Superseded by `min_idle_soc` as a floor at every departure, with its deadline at the expected plug-out | Medium-low |
| O1 | Charge beyond the floors when cheap? Lean (a) never | answer | See new decisions N10–N12: soft future demands, an optional concave stored-energy value, and an optional surplus ceiling (55–60 %). Engine default = (a). Reject (c) and (d); (b) only as an opt-in through the value steps | Medium (mechanism); low (money, ceiling) |
| O2 | Where is the arrival SoC stated? | answer | Optional `min_soc_at_end` on `AbsenceWindow`, defaulting to `default_arrival_soc` (default 20 %) | High (field); medium (value) |
| O3 | Naming pass before the contract is built | open | Add `price` → `price_per_kwh_total` (or document it), the new fields, and removing "trip" names. Do it after these decisions | — |
| O4 | Shape and defaults of the forecast markup | answer (shape); open (size) | `forecast_markup_steps: [(lead_hours, amount)]`, engine default empty. Integration ≈0.08 DKK/kWh incl. VAT at the first forecast day, ≈0.10 from D+4, flat from D+7, uncalibrated. Optional per-point markup with no default factor. No spread scaling; no known/uncertain split | Medium (shape); low (size) |
| O5 | What do open-source planners do? | answer | Answered by the prior-art note. Borrow the late tie-break, the partial-slot trim, a start cost, the on-state input and a caller-side plan lock. No precedent exists for chained targets, a markup or a buffer | High |
| O6 | Per field: what the API corrects and what it refuses | open | Partly answered: continuity in absolute time; mixed slot lengths; DST; overdue targets accepted, not skipped | Medium |
| O7 | Stale SoC below `min_safety_soc`: wake or charge first? | answer | Charge first, bounded by the projected SoC. An unknown SoC counts as 0 for the safety rule only. Staleness never blocks planning. Replace `soc_last_updated` with `soc_source` (+ age) | High |
| O8 | Default `simulation_step_minutes` | answer | Under a DP: precompute only; the precision knob is `soc_resolution_kwh` = 0.25 with conservative rounding. Under a greedy: 3 or 5 (must divide 15), not 6 | High |
| O9 | Is `is_top_up` needed; when is `SET_CHARGE_LIMIT` emitted? | answer | Drop `is_top_up`. A partial slot is set by window times. The engine never emits `SET_CHARGE_LIMIT`; the integration stops on projected SoC | Medium-high |
| O10 | Further validation | change | Add: warn when `min_safety_soc ≥ default_arrival_soc`. Reject "skip a target whose buffer has started"; accept it as overdue. Markup bounds: additive and non-negative | Medium-high |
| O11 | Price slots shorter than an hour | answer | `PricePoint` gains `end`; 15/60 mixed; hourly by default; budget ≈50 ms in the executor instead of 10 ms | High (contract); medium (budget) |
| O12 | Manual controls in the integration, not designed | answer | "Charge now to X" (session-scoped safety override), "Pause until" (expiry), one-off ready-by, smart off = hands off | High; medium-low for pause beating the safety floor |
| S1 | Forecast error by hours ahead | answer in part | "8–11 % MAPE" not found; correct research.md. MAE is 23–38 % of the mean, growing as t^0.2–0.3. Calibration needs a season of logged forecasts | Medium |
| S2 | How evcc, emhass, openWB, OpenEMS plan | answer | See O5 | High |
| S3 | How HA integrations expose SoC, plug, limits, power | answer in part | Charger first for plug and charging state; car for SoC. Škoda read-only. Staleness still unmeasured | Medium-high |
| S4 | How far greedy falls from optimum | answer | The corrected greedy is exact at constant power. With a taper on Danish totals: p90 ≈1–2 %, worst week 7–15 % (≤ ~9 DKK). "As written" depends on the unspecified trim | Medium-high |

## New decisions to add

Proposed IDs are placeholders, for the maintainer to number.

| Proposed | Decision | Reason | Confidence |
|---|---|---|---|
| N1 | `price` is the total marginal cost per wall kWh, every per-kWh component incl. VAT, on the same basis for known and forecast slots. The integration composes it and refuses to mix bases | Tariffs are half the value; spot-only ranking loses 185–217 DKK/yr | High |
| N2 | `PricePoint(start, end, price, is_forecast[, markup])`; mixed 15/60-minute slots; resolution chosen by the billing product (hourly by default) | 15-minute market since 2025-10-01; default products bill the hourly average | High |
| N3 | Forecast markup is additive, keyed on lead time from the last published slot; the engine default is empty | Error is roughly constant in price units and grows as t^0.2–0.3 | High (shape) |
| N4 | The partial slot is the most expensive chosen slot, run at full power and starting late. Ties go to the later slot | Exactness (matroid argument), 6 A minimum, efficiency, wear | High |
| N5 | `start_overhead_kwh` replaces `min_session_kwh`; `is_currently_charging` is the initial on-state | Cuts starts from 3.0 to 1.2 a night for +0.19 % | Medium-high |
| N6 | Optional `charging_overhead_kw`; curves, energy and costs are wall-side | Overhead of 100–300 W makes slow charging dearer | Medium |
| N7 | Overdue targets are accepted and charged as soon as possible within their cap (`TARGET_OVERDUE`). The integration persists them until met, unplugged or dismissed | evcc #24339 | High |
| N8 | The plan covers all available time; unpriced slots get a pessimistic decision price. The integration fills gaps with tariff + spot proxy as `is_forecast` | Missing spot must not throw away the 00–06 block | Medium |
| N9 | Control contract = `windows` + `should_charge_now`. The integration asserts ALLOW/HOLD as a level with read-back. Car commands leave the engine | Chargers lose edges; core Škoda has no wake or limit | High |
| N10 | Targets may be marked soft (assumed future use); missing one never makes the plan `PARTIAL` | Lets the caller expand departures over the forecast horizon without false alarms | Medium |
| N11 | Optional `surplus_max_soc`: stock held for soft demands or stored value stays below it (integration default 55–60 %) | Calendar-ageing step; ranking alone would park at 80 % | Low–medium |
| N12 | Optional concave `stored_energy_value_steps: [(kwh, value_per_kwh)]`; empty = O1(a); a user threshold is one step | Covers energy beyond the horizon and option (b) without a flat buy-forever value | Low |
| N13 | `min_idle_soc` is also a floor at every departure; its deadline is the expected plug-out | Unannounced trips; the 24 h horizon lands after departure | Medium |
| N14 | Algorithm: an exact DP over (slot, SoC 0.25 kWh, on-state) once N5, N10–N12 are in; the corrected greedy and a brute-force DP as test oracles; CE-A–CE-D as regression tests. Budget ≈50 ms desktop CPython, in the executor | Only standard-library method carrying the whole objective | Medium |
| N15 | `soc_source` (car-reported, projected, assumed) replaces `soc_last_updated`; O7 charges first | No capture timestamp or wake on core Škoda | High |
| N16 | Danish defaults (markup, ceiling, floors, start cost) live in the integration and are labelled uncalibrated until the measurements below exist | Every size rests on one month or on reasoning | High |
| N17 | The integration logs prices, forecast runs, charger and car data from its first release | The cheapest evidence for O1, O4, D16, D26 and O7 | High |

## What remains to be measured

| Measurement | Source | Settles | When |
|---|---|---|---|
| Per-phase current and voltage, offered current, SoC, outdoor temperature at 10–60 s, over 2–3 sessions including a cold night; one session capped at 10 A | Maintainer's charger and car in HA | The 11 → 7.5 kW cause; `car_power_soc_steps` (D16) | Weeks |
| Charger meter kWh against ΔSoC, per temperature band | Maintainer's logs | Efficiency and overhead, k (D16, D26, D6) | Weeks to one winter |
| SoC update cadence; mileage versus battery `last_changed`; parked drain over long absences | Maintainer's Enyaq on core Škoda 2026.11 | O7, `soc_source`, `soc_max_age_minutes` | Weeks |
| Plug-in auto-start and hold lag; command-to-power latency; end-of-charge overrun | Maintainer's charger (brand unknown to every note) | D8 value; adapter design | Weeks |
| Nightly kWh, plug-in and plug-out times, daily use by weekday | Maintainer's charger history | Learned consumption for N10; `min_idle_soc` | Available now if HA kept history |
| His grid company, billing product (hourly or quarter-hour), charger brand | Maintainer | Whether O11 is worth anything to him; which tariff; which adapter | Now |
| Carnot's forecast runs, logged every update, with elpriser.org's archive | Integration log; [elpriser archive](https://elpriser.org/api/openapi.json) (400 days from 2026-10-06) | O4 size; the trend view for Carnot; move-weighted direction accuracy | Both seasons by about April 2027; a full year by October 2027 |
| If his HA recorder kept the Energi Data Service `forecast` attribute, his past Carnot forecasts against actuals | Maintainer's recorder database (retention unverified) | The trend view on the forecast he actually used, immediately | Now, if the data exist |
| The bias of the days a planner waits for, by lead time and season | Re-run of the forecast note's analysis on the cross-day decision | The markup's first step | After a season |
| End-to-end replay: known horizon cut at 13:00, forecasts beyond, 2026 Danish totals, a real schedule, with and without soft demands, ceiling and wear cost | Existing DP harness ([optimisation experiments][oe]) | O1 money net of wear; whether the DP beats the corrected greedy once forecast error is present | Desk work, now |
| DP timing on a Raspberry Pi-class host | Maintainer's HA hardware | The 50 ms budget; grid size | Now |
| Where the calendar-ageing step lies in MEB displayed SoC | No source found; possibly literature on MEB cells | Ceiling 55–60 % against 70–75 % | Open |

[pc]: ../research_notes/Cheapest%20home%20EV%20charging/price_composition_denmark.md
[pf]: ../research_notes/Cheapest%20home%20EV%20charging/price_forecast_uncertainty.md
[cp]: ../research_notes/Cheapest%20home%20EV%20charging/charging_physics_battery.md
[sa]: ../research_notes/Cheapest%20home%20EV%20charging/scheduling_algorithm.md
[pa]: ../research_notes/Cheapest%20home%20EV%20charging/prior_art_software.md
[ha]: ../research_notes/Cheapest%20home%20EV%20charging/home_assistant_data.md
[dr]: ../research_notes/Cheapest%20home%20EV%20charging/driver_behaviour_ux.md
[me]: ../research_notes/Cheapest%20home%20EV%20charging/panel_market_economist.md
[oe]: ../research_notes/Cheapest%20home%20EV%20charging/panel_optimisation_engineer.md
[be]: ../research_notes/Cheapest%20home%20EV%20charging/panel_battery_engineer.md
[cu]: ../research_notes/Cheapest%20home%20EV%20charging/panel_control_ux_engineer.md
[rt]: ../research_notes/Cheapest%20home%20EV%20charging/panel_red_team.md
[dec]: ../decisions.md
