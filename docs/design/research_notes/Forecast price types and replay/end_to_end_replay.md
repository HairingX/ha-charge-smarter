# End-to-end replay of the planning engine with only the information it would have

Simulation engineer's notes, 2026-11-06. Every number below is either from a source opened on
that date or my own measurement with the scripts in
[`experiments/replay/`](experiments/replay/README.md); "Reasoning" marks inference.

## Method and data, read this first

### Takeaway
A rolling replay re-plans one Enyaq-like car every hour and at every plug-in, from the prices the
integration would have at that minute, and executes the first part of each plan. It covers
31 days with real forecast runs (2026-10-07 to 2026-11-06, DK1 and DK2) and twelve months for the
policies that need no forecast (2025-11-07 to 2026-11-06, DK1, DK2 and SE3), on hourly and on
quarter-hour billing. The forecast evidence is one month: 31 overlapping runs per area, 30
distinct target days with outcomes.

### Cited Findings
- **Prices.** Energi Data Service `DayAheadPrices`, quarter-hour spot in DKK/MWh for DK1, DK2
  and SE3, 38,596 rows per area from 2025-10-01 00:00 to 2026-11-06 23:45 (fetched 2026-11-06,
  before the 2026-11-07 prices were out) — [DayAheadPrices](https://api.energidataservice.dk/dataset/DayAheadPrices).
- **Tariffs.** `DatahubPricelist` rows, fetched the same day — [DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist):
  - N1's rows carry the owner name "N1 A/S - 131" (a query for "N1 A/S" returns 0 rows). Its
    "Nettarif C" (code CD), DKK/kWh excl. VAT, low / high / peak: 0.0867 / 0.2600 / 0.7801
    (2025-10-01 → 12-01), 0.0680 / 0.2041 / 0.6124 (December 2025), 0.0879 / 0.2636 / 0.7907
    (2026-01-01 → 04-01 and 2026-10-01 → 2027-01-01), 0.0879 / 0.1318 / 0.3426 (2026-04-01 → 10-01).
    The low rate is the same in summer and winter 2026.
  - Radius "Nettarif C" (DT_C_01): 0.0976 / 0.2929 / 0.8788 (2025-10-01 → 2026-04-01),
    0.1062 / 0.1593 / 0.4141 (summer 2026), 0.1062 / 0.3185 / 0.9556 (2026-10-01 → 2027-01-01).
  - Energinet system + transmission tariff 0.135 (2025) and 0.115 (2026); elafgift 0.72 (2025)
    and 0.008 (2026) DKK/kWh.
  - Every N1 and Radius tariff row has resolution `PT1H`, `P1D` or `P1M`; a query for rows with
    resolution `PT15M` valid from 2026-01-01 returns none, while `PT1H` returns rows. Grid
    tariffs therefore stay hourly while energy is priced per quarter (own query).
- **Composition** (as the integration would do it, N1 of the report): total = (spot + grid tariff
  of the local date and clock hour + Energinet + elafgift) × 1.25, supplier markup 0. The hourly
  product is the simple mean of the four quarter spot prices plus the hourly tariff; Tænk
  confirms that hourly prices are "et simpelt gennemsnit af priserne i de fire kvarterer" and
  that a customer gets quarter prices only by asking for such a product — [Tænk, 29 Sep 2025](https://taenk.dk/forbrugerliv/bolig/flere-elpriser-i-doegnet-giver-minimale-besparelser).
  SE3 is modelled as spot × 1.25 with no time-of-use tariff and no flat parts (an assumption,
  not a description of any Swedish grid company).
- **Forecasts.** All 31 elpriser.org archive runs per area, issued 2026-10-06 to 2026-11-05,
  raw spot DKK/MWh excl. VAT with P10/P90 — [elpriser.org OpenAPI](https://elpriser.org/api/openapi.json).
  Each run is used only from its `generatedAt` time (12:12–12:27 UTC, i.e. about 14:15 local
  before 25 October and 13:15 after). Carnot was never called.
- **What the archive itself shows about publication.** In 3 of the 31 runs (issued 2026-10-29,
  10-31 and 11-05, generated 12:13–12:20 UTC = 13:13–13:20 CET) the next day was not yet marked
  as published and carried no prices; all three are after the switch to CET, so 3 of 11 CET
  runs (own count from the archive files). The archive's "actual" days have 24 hourly values
  even on the 25-hour day 2026-10-25; the repeated 02:00 hour is missing (own check against
  `DayAheadPrices`). DST days have 100 (2025-10-26, 2026-10-25) and 92 (2026-03-29) quarters
  (own count).
- **The forecasts in this window were biased low.** Mean of (actual − forecast) per day, DK1,
  by lead day counted from the last published day: +177 (lead 1, 28 days), +255, +276, +281,
  +289, +276, +260, +328 DKK/MWh (lead 8, 24 days); the day was under-forecast on 62–79 % of
  days at every lead; hourly MAE 330 → 546 DKK/MWh. DK2: +306 → +517 DKK/MWh, under-forecast on
  78–85 % of days, MAE 404 → 673 — own measurement, [`fcerr.py`](experiments/replay/fcerr.py).
  This matches the maintainer's experience that his forecast is "always lower than the outcome".
- **Car and household.** 77 kWh usable, 11 kW wall, 90 % wall-to-battery (constant); taper case
  7.5 kW wall from 65 % SoC. Floors from the report: departure floor = max(40 % idle,
  20 % arrival + planned trip energy), completion buffer 20 min, safety 15 %, P0/P1 charge to
  80 % (or the trip's floor if higher), soft-stock ceiling 60 % (55 % variant).
- **Schedules** (random draws per seed, the same draws for every policy):
  1. weekday commute 07:30–16:30, 15–25 kWh uniform; the integration plans each commute at the
     90th percentile of the last 20 observed (25 kWh until it has 5);
  2. the same plus one long trip a week, Saturday or Sunday 09:00–19:00, 50–60 kWh, in the
     calendar five days ahead;
  3. irregular: on 60 % of days a trip departing 06:00–20:00, 1–10 h, 5–45 kWh, announced exactly
     24 h ahead; the integration's expected daily use is the mean of the last 14 days.
- **Information at each re-plan.** Published prices to the end of tomorrow from 13:00 local,
  otherwise to the end of today; the newest run already generated; trips already announced;
  consumption already observed. Beyond the published prices: the forecast for P3–P6b, the N8
  proxy (tariff + max(last published day's spot for that hour, its daily mean) + 0.10 DKK/kWh)
  for P2's next departure. Re-plan every 60 min (15-min variant) and at every plug-in.
- **Policies** as in the brief; P7 is perfect foresight of prices and consumption re-planned
  daily over ten days with the exact DP; P7c the same under the 60 % soft-ceiling rule (the fair
  oracle for the ceiling policies). Costs are DKK incl. VAT, adjusted for end-of-window SoC at
  P7's average price; "vs P2" values are paired means over the seeds (sd in brackets). Seeds:
  10 for DK1 hourly, 5 for DK2, quarter-hour billing and the sensitivities, 3 for the year.
- **Bookkeeping checks.** 0 missed targets for every greedy policy in every run below; the DP
  policies fell short of a floor 0.1–0.3 times a month on average, by 0.4 kWh or less (grid
  rounding). Arrivals under 20 % happen 2–5 times a month for P2 because a commute sometimes
  exceeds the p90 estimate it was planned with; stock-holding policies have fewer. Reasoning: the
  estimate of the last 20 draws from 15–25 kWh rarely falls more than about 2 kWh below 25, so
  these arrivals are a few percent below 20 %, never near empty.

### Inferences
- Reasoning: the 31-day window is a single autumn month with prices that were, per the report,
  unusually volatile; monthly results ×11.8 are "an October-like year", not a forecast of a year.
- Reasoning: with overlapping runs and one weather season, the independent forecast evidence is
  roughly four to five weekly regimes, not 31 days.

### Gaps
- Carnot runs could not be tested (no key, and the brief forbids calling it). elpriser.org is a
  stand-in with a similar low bias in this month.
- No forecast archive exists before 2026-10-06, so the forecast policies cover neither summer
  nor the 1 October season change.

## How much do the forecast-based policies add over P2, after bias? Is any of them worse?

### Takeaway
Under the recommended 60 % ceiling, every forecast policy beat P2 on average in this month,
P3 by 44–52 DKK (DK1) and 58–86 DKK (DK2) per 31 days, about 4–7 % of the bill and 60–90 % of
what a perfect-foresight planner under the same ceiling could gain. Only P4 with a markup was
ever worse than P2 (3 of 30 seeds). How the forecast is corrected hardly matters: markups of
0 to 0.10 DKK/kWh, bias correction and anchoring land within about 10 DKK of each other, except
P4 with a markup in the long-trip schedule (36 DKK worse than P3). The ceiling decides the
money: without it the same forecasts gain about three times as much, with the car above 60 %
about a third of the time.

### Cited Findings
DK1, hourly billing, 10 seeds, 2026-10-07 → 11-06, own measurement ([`run.py fc_dk1`](experiments/replay/run.py),
data: [DayAheadPrices](https://api.energidataservice.dk/dataset/DayAheadPrices), [DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist),
[elpriser archive](https://elpriser.org/api/openapi.json)). DKK per 31 days, adjusted; schedules 1 / 2 / 3.

| Policy | Cost | vs P2 | Seeds worse than P2 | Regret vs P7 | h > 55 % | h > 60 % | Starts* |
|---|---|---|---|---|---|---|---|
| P0 charge on plug-in | 1680 / 2290 / 1267 | +828 / +1114 / +427 | 30/30 | +1025 / +1279 / +630 | 627 / 579 / 671 | 541 / 489 / 654 | 24 / 28 / 20 |
| P1 midnight timer | 897 / 1261 / 892 | +45 / +85 / +51 | 29/30 | +241 / +250 / +254 | 530 / 462 / 600 | 380 / 308 / 570 | 23 / 27 / 20 |
| P2 known prices, greedy | 852 / 1176 / 840 | 0 | — | +197 / +164 / +203 | 0 / 71 / 84 | 0 / 68 / 62 | 36 / 42 / 35 |
| P3 markup 0 | −39.1 / −47.7 / −51.2 vs P2 | | 0/30 | +158 / +117 / +152 | 118 / 102 / 177 | 0 / 59 / 63 | |
| P3 markup 0.05 | −39.6 / −48.5 / −51.7 | | 0/30 | | | | |
| P3 markup 0.08 | 809 / 1126 / 789; −43.7 (2.5) / −49.7 (14.9) / −51.8 (18.8) | | 0/30 | +153 / +115 / +151 | 120 / 108 / 178 | 0 / 65 / 63 | 36 / 40 / 32 |
| P3 markup 0.10 | −45.8 / −49.3 / −53.2 | | 0/30 | | | | |
| P3 0.08, +0.10 from 48 h | −43.7 / −50.8 / −52.2 | | 0/30 | | | | |
| P3 0.08, ceiling 55 % | −27.2 / −37.1 / −42.7 | | 0/30 | | 0 / 68 / 86 | 0 / 59 / 63 | |
| P4 bias-corrected, markup 0 | −45.8 / −33.1 / −50.0 | | 0/30 | | 120 / 137 / 194 | 0 / 94 / 65 | |
| P4 bias-corrected, 0.08 | −40.5 / −13.7 (18.5) / −47.3 | | **3/30** (all schedule 2) | +156 / +151 / +155 | 151 / 184 / 220 | 0 / 129 / 65 | |
| P5 anchored, markup 0 | −49.5 / −55.3 / −53.9 | | 0/30 | +147 / +109 / +149 | 192 / 260 / 269 | 0 / 201 / 68 | |
| P5 anchored, 0.08 | −46.0 / −44.8 / −49.6 | | 0/30 | | 203 / 308 / 292 | 0 / 212 / 68 | |
| P3 0.08, **no ceiling** | 697 / 1054 / 700; −155.6 / −122.0 / −140.1 | | 0/30 | +41 / +42 / +63 | 299 / 238 / 260 | 264 / 199 / 242 | 28 / 34 / 35 (old count) |
| P7c foresight, 60 % rule | −59.3 / −54.9 / −86.1 | | | +137 / +109 / +117 | 132 / 109 / 227 | | |
| P7 foresight | 656 / 1012 / 638; −196.6 / −164.2 / −202.7 | | | 0 | 314 / 255 / 392 | 299 / 239 / 360 | |

\*Starts per 31 days. P0 and P1 never split a session. For P2 and P3 the counts are from the
`starts` re-run (5 seeds), in which a partly used slot that continues a running session starts at
once; the first runs started every partly used slot late, which split some sessions and gave
44 / 50 / 42 for P2. Costs are identical under both rules.

- **Share of the attainable gain.** P3 (0.08) recovers 74 / 91 / 60 % of P7c's gain over P2 and
  22 / 30 / 26 % of P7's (own arithmetic on the table).
- **DK2, Radius tariffs, 5 seeds** (`run.py fc_dk2`): P3 (0.08) −61.6 / −85.9 / −58.3 DKK vs P2;
  P4 −75.7 / −85.6 / −60.8; P5 −76.9 / −74.6 / −58.4; P7c −80.4 / −76.1 / −95.2; P7 −223.9 /
  −185.7 / −211.5. No DK2 forecast policy was worse than P2 in any seed.
- **Without the ceiling, the correction matters a little more but not consistently**
  (`run.py extra`, 5 seeds, DKK vs P2). DK1: markup 0 −154.7 / −124.5 / −131.5; 0.08 −155.6 /
  −122.0 / −140.1; 0.20 −155.9 / −110.4 / −148.3; P4 −140.9 / −102.7 / −129.6; P5 −145.6 /
  −96.9 / −136.4. DK2: markup 0 −172.4 / −146.5 / −140.2; 0.08 −187.0 / −160.5 / −141.5; 0.20
  −195.2 / −156.9 / −153.7; P4 −187.1 / −152.6 / −141.9; P5 −187.7 / −133.7 / −153.5.
- **Where the energy goes.** In this window P2 bought 89 % of its energy in the 00–06 low
  period and none in 17–21; P3 91 %, P7 94 %; P0 put 57 % in the peak (DK1, all seeds).
- **What a later publication does to P3** (3 seeds): tomorrow's prices known at 18:00 instead of
  13:00 cost +10 / +18 / +19 DKK a month; known only from midnight +117 / +148 / +79
  (`run.py publication`).

### Inferences
- The forecast gain over P2 in an October-like month is about 40–60 DKK in DK1, roughly
  500–700 DKK a year if every month were like it (×11.8). Reasoning: October 2026 had larger
  day-to-day moves than the year (report), so this is an upper half estimate; summer is untested.
- None of the forecast policies is worse than P2 on average; only P4 with a markup was worse in
  3 of 30 seeds, all in the long-trip schedule. The forecast's large low bias did not turn the
  forecast policies negative because the ceiling lets them pre-buy at most about one day, and
  because the hard target of the next departure is always bought from published prices.
- Bias correction (P4) against the same markup without it changed the result by −15 to +36 DKK
  a month: it helped in DK2 (−2 to −15, with and without the ceiling) and hurt in DK1 (+1 to +36)
  except schedule 1 at markup 0 (−7). It shifts all forecast days up by 0.2–0.4 DKK/kWh, which
  acts like a large markup; reasoning: a 15-day rolling bias in a month whose bias itself drifted
  is not a reliably better level estimate than none. Anchoring (P5) was slightly better than
  plain P3 without markup in DK1 (−3 to −10 DKK) but holds more stock (h > 55 % up 50–155 %).
- The markup size the report left open (0.05–0.10) does not matter under a 60 % ceiling: the
  spread between 0, 0.05, 0.08 and 0.10 is ≤ 7 DKK a month in every schedule. A ceiling makes the
  markup almost irrelevant; without the ceiling markups from 0 to 0.20 span 1–23 DKK, with no
  consistent best value.

### Gaps
- One month, one provider, one season; no Carnot. Whether the gain survives a calm summer month
  or a forecast that is unbiased cannot be measured until the archive is longer (from about
  April 2027).
- Battery wear is not in the money. The no-ceiling gain (≈ 70–110 DKK a month more) is bought
  with 200–265 hours a month above 60 %; whether that is worth it is the ageing question the
  report left open.

## Does the greedy-vs-DP choice matter once the realistic information set is used?

### Takeaway
No, for money. With only published prices the exact DP and the corrected greedy pay the same to
within ±1 DKK a month and ±16 DKK a year in DK1 and DK2; with forecasts, soft targets and the
ceiling the DP was 1–22 DKK a month worse, not better. The DP's cost lies elsewhere: plan time
(30–47 ms mean, up to 130 ms on quarter-hours) and, with a 0.25 kWh SoC grid, a reach rounding
that loses 9 % of every quarter-hour slot. The DP only wins money where the total price goes
negative, which in this data happened only in the SE3 model without flat charges.

### Cited Findings
Own measurement (`run.py fc_dk1`, `fc_dk2`, `year`, `sensitivity`, `grid`), paired by seed:

| Comparison | Window | DK1 | DK2 | SE3 (no tariff, spot × 1.25) |
|---|---|---|---|---|
| P6a − P2 (known prices only), hourly | 31 days | +0.0 / +0.2 / +0.4 | −0.2 / −0.3 / +0.2 | — |
| P6a − P2, hourly | 12 months | +10.9 / +15.5 / +10.2 | +8.9 / +13.2 / +10.2 | −198.2 / −74.3 / −131.3 |
| P6b − P3 (0.08, 60 %), hourly | 31 days | +0.6 / +10.4 / +6.2 | +0.6 / +21.6 / +6.7 | — |
| P6a − P2, taper 11 → 7.5 kW from 65 % | 31 days | +0.6 / −3.8 / −6.5 | — | — |
| P6b − P3, taper | 31 days | −1.9 / +12.2 / +1.0 | — | — |

- **Plan time per call** (this container, four replays in parallel, CPython 3.13, DK1): P2
  greedy < 0.1 ms mean, max 8 ms; P3 greedy with a 9-day forecast horizon 0.8–1.7 ms mean, max
  21 ms; P6a DP 4.5–6 ms mean, p95 8–15, max 28–65 ms (hourly) and 15–19 ms mean, p95 26–35, max
  42–126 ms (quarter-hour known part); P6b DP over the forecast horizon 32–39 ms mean, p95 37–49,
  max 95–113 ms (hourly) and 41–47 ms mean, p95 50–59, max 67–130 ms (quarter-hour); P7 over ten
  days 38–51 ms hourly and 140–210 ms on quarter-hours.
- **SoC grid.** With a 0.25 kWh grid the DP's reach per slot at 9.9 kW battery power is 39 steps
  per hour (9.75 kWh, −1.5 %) and 9 per quarter (2.25 kWh, −9.1 %); with 0.2475 kWh it is exactly
  40 and 10 (own check with `fulldp.precompute`). Switching to 0.2475 changed costs by −0.5 to
  +0.3 DKK a month on hourly billing and −3.9 to +0.3 on quarter-hour billing, and cut the
  quarter-hour DP's charge starts from 214 / 311 / 218 to 84 / 99 / 87 a month (P6a) and P7's
  from 209 / 306 / 210 to 47 / 74 / 50. A 0.33 kWh grid changed hourly costs by ≤ 0.5 DKK.
- **Negative totals.** Over the twelve months the composed total was negative in 2 DK1
  quarter-hours (minimum −0.075 DKK/kWh), 0 DK2 quarter-hours (minimum +0.205) and 482 SE3
  quarter-hours, 1.4 % (minimum −0.135, spot × 1.25 only) (own count). Only in SE3 did the DP
  hold more stock than the greedy (696 vs 0 hours above 55 % in schedule 1): it fills the car in
  negative hours, which the floors-only greedy never does.
- **Misses.** Neither algorithm missed a target in the realistic replay; the DP fell short by
  0.1–0.4 kWh in a few departures from its rounding (schedule 3).

### Inferences
- Reasoning: under forecast error, solving the planning problem exactly does not buy a better
  realised outcome: both algorithms act on the same wrong forecast, and the first hour, the only
  part executed, is almost always the same. The report's case for the DP rests on carrying more
  objective terms (start cost, soft targets, wear), not on money, and this replay supports
  exactly that reading.
- The P6b − P3 gap (+6 to +22 DKK in schedules 2 and 3) is not grid rounding (a finer grid moved
  it by ≤ 0.5 DKK). Reasoning: the two encode the ceiling differently (the DP caps the SoC
  reachable in a slot, the greedy caps only soft stock), so they do not solve exactly the same
  problem; this should be settled in the engine's tests, not by more replay.
- If the DP is adopted (N14), its SoC grid must be a whole fraction of the energy one slot holds
  at full power, or its reach must not be floored per slot; otherwise quarter-hour plans lose
  9 % of power and fragment.
- Under a total price that can go negative (the SE3 model here, or any product whose total
  carries no tariff or flat charges) the DP's ability to value "free" energy is worth 70–200 DKK a year;
  in Danish totals with tariffs it is worth nothing measurable.

### Gaps
- Timings are from this cloud container, not a Raspberry Pi; scale them by the Pi's slowdown.
- The SE3 model has no flat per-kWh charges; any flat charge above 0.135 DKK/kWh removes every
  negative hour in this year, and with it the DP's SE3 advantage.

## Which defaults or rules change the outcome materially?

### Takeaway
Four things move money by more than 50 DKK a month or 100 DKK a year: the surplus ceiling, the
N8 rule for a departure beyond the published prices (and publication time itself), the price
composition (tariff hour, hourly averaging), and whether the car is charged by a plain timer.
The idle floor, the completion buffer, the markup size, 15-minute re-planning and the taper move
it by a few kroner.

### Cited Findings
Own measurement, DK1 unless stated, paired by seed (`run.py sensitivity`, `publication`,
`faults`, `extra`):

| Rule or default | Change | Effect on cost | Other effects |
|---|---|---|---|
| Soft-stock ceiling (N11) | 60 % → none (P3 0.08) | −112 / −72 / −88 DKK per 31 days | +264 / +134 / +179 h above 60 % |
| | 60 % → 55 % | +17 / +13 / +9 | h > 55 %: 120 → 0 (sched. 1) |
| N8 proxy for the next departure beyond published prices | proxy → deadline clipped to published prices (P2n) | +19 / +104 / +13 per 31 days; +28 / +147 / +21 per year | reasoning: mostly weekends, when Monday's 00–06 is not yet published at plug-in |
| Publication of tomorrow's prices | 13:00 → 14:00 | +11 / +5 / +49 per year (P2) | |
| | 13:00 → 18:00 (after plug-in) | +258 / +180 / +354 per year (P2); +278 / +553 / +114 more for P2n | |
| | only from midnight | +894 / +922 / +745 per year (P2); P2n +1,320 / +3,484 / +1,489 vs P2 | |
| Tariff hour taken in UTC instead of local time | composition fault | +97 / +155 / +60 per year | peak share 2.8 → 7.6 % |
| Hourly price = first quarter instead of mean of four | composition fault | +106 / +163 / +119 per year | |
| Ranking quarters while billed per hour | composition fault | +82 / +109 / +70 per year | starts +78 % |
| Tariff row of the planning date for all slots (stale season or year) | composition fault | 0 / 0 / 0 per year | N1's low rate is unchanged across 1 Oct, and the published part of a plan spans at most 35 h |
| Tariff indexed by position in the day on DST days | composition fault | 0 / 0 / 0 per year | the shifted 02:00 hour lies inside the 00–06 low block |
| Markup 0 → 0.10 (60 % ceiling) | | ≤ 7 DKK per 31 days | |
| Idle floor 40 % → 30 % or 50 % | | 0 for the commute schedules; −11 to +15 for the irregular one | the commute floor (≈ 51 %) is above it |
| Completion buffer 20 → 60 min | | 0 to +5 per 31 days | |
| Re-plan every 15 min instead of 60 | | −0.7 to +1.7 per 31 days | |
| Taper 11 → 7.5 kW from 65 % | | −0.6 to +8.8 per 31 days (greedy) | greedy starts +35 to +57 a month (old count), as its conservative slot capacity spreads energy over more slots |
| Start overhead 0.3 kWh in the DP (N5) | | −2 to +1 per 31 days (hourly), −3 to −2 (quarter-hour) | starts −0.6 to −2.6 a month hourly; on quarter-hours **more** starts (+35 to +40), see the billing section |
| Midnight timer (P1) instead of P2 | | +45 / +85 / +51 per 31 days; +1,484 / +1,992 / +2,292 per year | ≈ 5,500–7,000 h a year above 55 % |

- **The 17:00 peak at plug-in.** Charging on plug-in at 16:30 put 57 % of the energy into 17–21
  in both windows (P0); P2 put 0 % there in October and 2.8 % over the year. In schedule 1
  (seed 1) P2's peak-period energy cost 1.05 DKK/kWh on average against 1.39 for its 00–06
  energy and 0.69 for its high-load energy (own figures). Reasoning: the greedy takes the cheapest
  total in its horizon, so these peak hours were cheaper than the alternatives at the time (the
  summer peak rate is 0.343, and the 00–06 average includes November–December 2025 at the 0.72
  elafgift); they are not wrong hours.
- **Tariff boundaries.** A shift of the tariff hours (the UTC fault, which in winter moves every
  boundary by one hour and in summer by two) is the only boundary fault tested that cost money;
  it moved energy into the 17–21 peak (7.6 % against 2.8 %).
- **Season switch and New Year.** No effect for N1 known-price planning: the low rate is the
  same before and after 1 October 2026, and the elafgift drop on 1 January 2026 is flat across
  the hours one plan compares. Reasoning: a grid company that changes its period boundaries, as
  the report found for TREFOR El-net from 2027, or a forecast policy planning across the
  switch, would be exposed; neither is in this data.

### Inferences
- The ceiling is the single largest lever and it is a battery-wear decision, not a price one.
  The integration's default (55–60 %) costs about 70–110 DKK a month in an October-like month
  (≈ 850–1,300 DKK a year if annualised) relative to no ceiling.
- N8 is not optional. Without a proxy for the next departure the planner must buy before the
  published prices end (reasoning: on a weekend that means Sunday evening at the high-load rate
  instead of Monday 00–06); the loss is 20–150 DKK a year with publication at 13:00, 110–550 with
  publication after plug-in, and 1,300–3,500 when a day's prices arrive only at midnight.
- The price adapter remains worth more than the planner's sophistication: each of the three
  composition faults that cost anything costs 60–165 DKK a year, while the DP gains nothing
  measurable anywhere in Denmark.

### Gaps
- The wear value of the ceiling, the effect of a period-boundary change at a grid company, and
  a real late publication (the replay delays it synthetically) are not measured.

## Quarter-hour billing: what changes against hourly billing?

### Takeaway
Quarter-hour billing saves a planner on published prices 21–92 DKK a year (DK1, DK2) and 61–89
(SE3), with the same plan quality and targets met, but it more than doubles the greedy's charge
starts (36 → 80 a month) and multiplies a 0.25 kWh-grid DP's by four to six. The 0.3 kWh start
overhead did not help on quarter-hours; a grid that fits the slot did. A midnight timer loses
1–18 DKK a year on it. The grid tariff stays hourly, so the engine must accept mixed slots:
quarter energy prices plus an hourly tariff. The quarter-hour DP needs 15–47 ms per plan on
average and up to 130 ms, within the report's 50 ms only on average.

### Cited Findings
- Paired quarter-hour minus hourly billing, adjusted cost (own measurement, `summarise.py --billing`):

| Policy | DK1, 31 days | DK2, 31 days | DK1, year | DK2, year | SE3, year |
|---|---|---|---|---|---|
| P1 timer | +0.2 to +0.7 | +0.6 to +1.0 | +14.5 / +12.1 / +4.5 | +17.8 / +14.7 / +5.8 | +10.1 / +6.9 / +0.9 |
| P2 greedy | −5.2 / −7.2 / −8.7 | −19.9 / −23.6 / −12.8 | −21.0 / −26.4 / −80.8 | −38.7 / −50.8 / −92.2 | −60.6 / −85.5 / −89.0 |
| P3 (0.08, 60 %) | −7.3 / −5.0 / −7.2 | −5.2 / −6.6 / −8.0 | — | — | — |
| P7, both on a 0.2475 kWh grid (raw cost) | −2.5 / −5.4 / −4.7 | — | — | — | — |

- **Charge starts** per 31 days, DK1, 5 seeds, corrected start rule (`run.py starts`), schedules
  1 / 2 / 3:

  | Policy | Hourly billing | Quarter-hour billing |
  |---|---|---|
  | P1 timer | 23 / 27 / 20 | 23 / 27 / 20 |
  | P2 greedy | 36 / 42 / 35 | 80 / 95 / 80 |
  | P3 (0.08, 60 %) | 36 / 40 / 32 | 78 / 87 / 80 |
  | P6a DP, 0.25 kWh grid | 37 / 42 / 35 | 153 / 222 / 157 |
  | P6a with 0.3 kWh start overhead | 36 / 40 / 33 | 191 / 262 / 188 |
  | P6b DP | 37 / 40 / 32 | 150 / 218 / 157 |
  | P6b with start overhead | 34 / 38 / 31 | 191 / 255 / 183 |
  | P7 foresight, 0.25 kWh grid | 24 / 31 / 23 | 183 / 266 / 184 |
  | P6a, 0.2475 kWh grid (old count) | 44 / 52 / 43 | 84 / 99 / 87 |
  | P7, 0.2475 kWh grid (old count) | 25 / 38 / 28 | 47 / 74 / 50 |

  Over the twelve months P2 started 402 / 487 / 365 sessions on hourly and 836 / 1,008 / 790 on
  quarter-hour billing in DK1 (DK2 406 / 487 / 365 → 874 / 1,054 / 829; SE3 393 / 493 / 387 →
  954 / 1,220 / 924). The start overhead cost −3 to +1 DKK a month (own measurement).
- The DataHub tariffs stay hourly (`PT1H`; no `PT15M` rows) — [DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist);
  default hourly-product customers are billed the simple mean of four quarters and must opt in
  to quarter prices — [Tænk](https://taenk.dk/forbrugerliv/bolig/flere-elpriser-i-doegnet-giver-minimale-besparelser).
  Norlys's press chief is quoted there estimating that a family "måske vil kunne spare 200
  kroner om året" by planning around quarter prices — same source.
- Plan time on quarter-hour billing: see the DP section (P6a 15–19 ms mean, p95 26–35, max
  42–126; P6b 41–47 ms mean, p95 50–59, max 67–130).

### Inferences
- The money from quarter-hour billing for an EV planner is 20–90 DKK a year in Denmark, in line
  with the report's 45–75; it is real but smaller than most composition faults (60–165).
- The engine must take quarter slots for the published part and hourly slots for the forecast
  (forecasts are hourly), with the tariff applied per hour (N2 holds).
- The start overhead (N5) as the DP implements it counts a slot as "on" whenever it charged at
  all, so on quarter-hours it rewards chains of partly used quarters, which execution can only
  run as separate sessions; starts rose by 35–40 a month. Reasoning: N5 only works if "on" means
  charging up to the slot's end, so that a partly used slot can sit only at the edges of a
  session, and if the SoC grid lets a full quarter be represented exactly. With a fitting grid
  (0.2475 kWh) the DP's quarter-hour starts fell to about the greedy's (84–99 a month).
- Reasoning: on quarter-hour billing, two to three sessions a night is what cheapest-quarter
  selection does; whether that matters depends on the charger and car (wake-ups, contactor
  cycles), which this replay cannot price.

### Gaps
- Which Danish suppliers offer quarter-hour products and how many households take them was not
  researched here.
- Timings on a Raspberry Pi-class host remain unmeasured.

## Which findings hold across places and billing periods, and which are DK1/N1 hourly only?

### Takeaway
The ordering of the policies, the irrelevance of the DP for money wherever the total carries
tariffs, and the value of N8 hold in DK1/N1, DK2/Radius and the tariff-less SE3 model, on hourly
and quarter-hour billing; the forecast gain and the dominance of the ceiling hold in DK1 and DK2
(SE3 has no forecast archive). What is specific: the absolute DKK, the size of the timer's loss
(about half in SE3, which has no night tariff), the forecast gain (about 40 % larger in DK2,
whose forecasts were more biased), the zero cost of the DST and stale-tariff faults (measured for
N1 only), and the DP's advantage in SE3 (negative totals).

### Cited Findings
Own measurement, twelve months 2025-11-07 → 2026-11-06, hourly billing, 3 seeds, adjusted DKK per
year, schedules 1 / 2 / 3 (`run.py year`):

| | DK1 (N1) | DK2 (Radius) | SE3 (spot × 1.25) |
|---|---|---|---|
| P2 cost | 7,087 / 10,801 / 6,800 | 7,274 / 10,979 / 7,016 | 2,557 / 3,733 / 2,438 |
| P0 − P2 | +5,193 / +7,696 / +3,976 | +6,089 / +8,874 / +4,249 | +2,710 / +3,601 / +1,805 |
| P1 − P2 | +1,484 / +1,992 / +2,292 | +1,337 / +1,848 / +2,093 | +787 / +986 / +902 |
| P2n − P2 | +28 / +147 / +21 | +7 / +135 / +17 | 0 / +62 / 0 |
| P6a − P2 | +11 / +16 / +10 | +9 / +13 / +10 | −198 / −74 / −131 |
| P7 − P2 (foresight headroom) | −2,003 / −1,612 / −1,818 | −2,020 / −1,678 / −1,800 | −1,240 / −1,111 / −1,098 |
| P1 hours > 55 % | 6,329 / 5,528 / 6,967 | same schedules | same |

- In the forecast window DK2's forecast gain was −58 to −86 DKK per 31 days against DK1's −44 to
  −52 (P3 0.08), and its forecast bias was larger (+306 to +517 against +177 to +328 DKK/MWh by
  lead day; `fcerr.py`).
- On quarter-hour billing P2's gain over P1 and the regret ordering were unchanged in all three
  areas (year table above and billing section).

### Inferences
- Robust across places and billing: P0 ≫ P1 > P2 > forecast policies > foresight; the DP adds
  nothing over the corrected greedy when prices carry flat charges and tariffs; the ceiling is
  the dominant forecast-policy setting; N8 is needed wherever a departure can lie beyond the
  published prices; composition faults cost more than algorithm choices.
- Specific to DK1/N1 hourly: the DKK amounts; the zero cost of the stale-tariff and DST-position
  faults (reasoning: any grid company whose period boundary falls in 02:00–03:00 or whose low rate changes
  at a season switch would show a cost); the size of the forecast gain (DK2's was about 40 %
  larger in the same month).
- Reasoning on SE3: without a time-of-use tariff the timer loses about half as much against P2
  (≈ 800–1,000 DKK a year against 1,300–2,300 in Denmark), because the night is not
  systematically cheapest; the planner's value then comes from spot alone.
- The P1 − P2 gap here (1,300–2,300 DKK a year) is two to five times the report's 470–630 for
  ranking tonight's known prices against a midnight timer. Reasoning: these schedules leave the
  car at home in daytime and at weekends, when P2 can use cheap daytime hours that a midnight
  timer never sees, while the report's calculation charged 6 kWh every night; the gap depends on
  how often the car is home when daytime prices are low.

### Gaps
- No forecast archive exists for SE3, so the forecast policies were not run there.
- Only one grid company per Danish area was modelled.
