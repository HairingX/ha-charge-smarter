# Biased price forecasts and the three price types (known, expected, trend)

Research for D20, O4 and O11 (`docs/design/decisions.md`) and the maintainer's proposal of three
price types. Done on 2026-11-06. Rule followed: every factual claim cites a page or file that I
opened during this task, or is my own measurement. "Measured here" marks numbers I computed; the
method and the sample are stated beside them. "Reasoning" marks my own argument.

**Data used for every measurement (downloaded 2026-11-06, 10:15 UTC):**
- elpriser.org forecast archive: every run in the archive, 31 per area, issued 2026-10-06 to
  2026-11-05, for DK1 and DK2 (`https://elpriser.org/api/forecast/archive?area=DK1&issued=…`). Each
  run gives an hourly median and P10/P90 of spot in DKK/MWh excl. VAT. The archive "starts on
  2026-10-06; earlier runs were not kept" — [elpriser OpenAPI spec](https://elpriser.org/api/openapi.json).
- Energi Data Service `DayAheadPrices`, DK1 and DK2, 2026-09-01 to 2026-11-06 (12,872 quarter-hour
  rows), averaged to the hour (the default hourly product: hourly price = mean of the four quarters) —
  [DayAheadPrices](https://api.energidataservice.dk/dataset/DayAheadPrices).
- Total price = (hourly spot + grid tariff + Energinet tariffs + elafgift) × 1.25 VAT. Rows from
  [DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist), valid 2026-10-01 to
  2027-01-01, so constant over the whole test window:
  - N1 A/S - 131 "Nettarif C" (DK1): 0.087854 (00–06) / 0.263563 (06–17, 21–24) / 0.79069 (17–21) DKK/kWh.
  - Radius Elnet A/S "Nettarif C" (DK2): 0.106175 / 0.318524 / 0.955573 DKK/kWh.
  - Energinet "Transmissions nettarif" 0.043 + "Systemtarif" 0.072; "Elafgift" EA-001 0.008 DKK/kWh.
  - The formula and the 25 % VAT follow the assumptions at the top of
    `research_notes/Cheapest home EV charging/price_composition_denmark.md`.
- Sample honestly counted: 30 target days with a settled price (2026-10-08 to 2026-11-06), 30 decision
  days (2026-10-07 to 2026-11-05). Runs overlap, and the day-level error has a lag-1 autocorrelation
  of 0.73 (DK1) and 0.76 (DK2), so the **effective number of independent days is about 4–5** (n(1−ρ)/(1+ρ)).
  One autumn month, with two windy low-price spells and one sharp rise in level.
- **Carnot was not called and is untested.** The maintainer's key is rate-limited; Carnot keeps no
  public archive.
- Scripts: `experiments/` beside this file (`bias.py`, `methods.py`, `robustness.py`,
  `quarters.py`, `fetch.sh`; see its README).

## 1. Level bias of the forecast: sign, size, structure, stability

### Takeaway
In this month the elpriser.org median was **too low in both areas, by about 16–22 % of the spot
price in DK1 and 25–34 % in DK2**. On the all-in price that is −0.26 to −0.38 DKK/kWh (DK1, N1) and
−0.42 to −0.62 DKK/kWh (DK2, Radius) incl. VAT. The maintainer's observation holds on average but not
"always": the forecast was too high on windy low-price days and in the cheapest hours. The bias is
**not stable enough to correct with a fixed or slowly rolling number**. It is driven by the price
level: it went from about −130 (first half) to −360 DKK/MWh (second half, DK1) when prices rose to
about 1,900–2,200 DKK/MWh. With 4–5 effective independent days it is not even statistically
distinguishable from zero. What *is* stable is that **the most recent error predicts the next few
days' error** (correlation 0.72–0.78 at D+2, fading to about 0 by D+6). That points to an anchored,
decaying correction (section 2).

### Cited Findings
- **Bias by days ahead of the issue date (measured here).** Error e = forecast median − actual,
  hourly spot DKK/MWh. On the total price the error is e × 1.25 / 1000 DKK/kWh, because every other
  part of the total is known in advance.

  | Days ahead | DK1 n hours / days | DK1 bias (median) | DK1 MAE | DK1 share e<0 | DK1 bias/mean | DK1 bias, total DKK/kWh | DK2 bias (median) | DK2 MAE | DK2 share e<0 | DK2 bias/mean | DK2 bias, total DKK/kWh |
  |---|---|---|---|---|---|---|---|---|---|---|---|
  | D+2 | 720 / 30 | −210 (−181) | 354 | 69 % | −16 % | −0.263 (−12 % of 2.17) | −339 (−319) | 431 | 80 % | −25 % | −0.424 (−18 % of 2.31) |
  | D+3 | 696 / 29 | −254 (−224) | 377 | 75 % | −19 % | −0.318 | −387 (−376) | 483 | 81 % | −28 % | −0.483 |
  | D+4 | 672 / 28 | −268 (−264) | 401 | 74 % | −20 % | −0.334 | −423 (−396) | 513 | 81 % | −30 % | −0.528 |
  | D+5 | 648 / 27 | −288 (−300) | 440 | 74 % | −21 % | −0.360 | −455 (−447) | 563 | 78 % | −32 % | −0.569 |
  | D+6 | 624 / 26 | −288 (−310) | 458 | 74 % | −21 % | −0.361 | −466 (−509) | 585 | 80 % | −32 % | −0.583 |
  | D+7 | 600 / 25 | −263 (−365) | 471 | 70 % | −19 % | −0.329 (−14 % of 2.28) | −435 (−492) | 577 | 80 % | −30 % | −0.544 (−22 % of 2.43) |
  | D+8 | 576 / 24 | −277 | 468 | 68 % | −20 % | −0.346 | −464 | 585 | 79 % | −32 % | −0.580 |
  | D+9 | 552 / 23 | −307 | 532 | 67 % | −22 % | −0.384 | −495 | 656 | 79 % | −34 % | −0.619 |

  The rows share target days, so they are not independent of each other. The bias grows only a
  little after D+2; the MAE grows about 30–50 % from D+2 to D+9.
- **The bias and error are now larger than the earlier notes reported.** With actuals through
  2026-10-27 the DK1 bias was −55 to +42; through 2026-10-29, −62 to −122 —
  `research_notes/Cheapest home EV charging/panel_red_team.md` ("Forecasts"). With 30 target days
  it is −210 to −307 (above). The provider's own backtest MAE for DK1 is 149 (D+2) to 197 (D+9)
  DKK/MWh — [model card](https://huggingface.co/Elpriser/denmark-price-forecast). The live MAE here
  is 354–532, 2.4–2.7× that.
- **By hour of day (measured here, D+2..D+7 pooled, 3,960 forecast-hours per area).**
  - DK1 bias: −140 to −175 in 00–06; −226 to −288 in 07–12; −341 to −458 in 13–19, deepest at 17:00
    (−458); back to −184 at 23:00. MAE 347–364 at night, up to 545 at 17:00.
  - DK2 bias: −257 to −280 in 00–05; −621 at 17:00; MAE 401–426 at night, 686 at 17:00.
  - **Night hours 00–05, where an EV charges:** bias −156 DKK/MWh (DK1) = **−0.195 DKK/kWh total**;
    −267 (DK2) = **−0.333 DKK/kWh total**.
  - So the forecast under-predicts the daytime and evening peak more than the night: its within-day
    shape is too flat.
- **By price level (measured here, D+2..D+7, quintiles).**
  - By the *actual* price: the cheapest fifth (DK1 −4..849) was over-forecast, bias +295 (only 15 %
    of errors negative); the dearest fifth (1,837..4,209) under-forecast by −737 (99 % negative).
    DK2: +202 and −1,007. Binning on the outcome exaggerates this (regression to the mean), so
    two other cuts follow.
  - By the *forecast* price, which the engine can see: −59 (cheapest fifth) to −438 (dearest) in DK1;
    −124 to −650 in DK2. The higher the forecast, the more it under-shoots.
  - By the *known level at issue* (mean of the published days D and D+1): DK1 −374, −252, −111,
    +19 for the four lower fifths, and −587 (100 % negative) when the known level was 1,886–2,115.
    DK2: −526, −397, −236, −86, −832. The deepest under-forecast came when the price had just risen
    to a level the model had not seen.
- **Mincer-Zarnowitz fit, actual = a + b × forecast (measured here, D+2..D+7).**
  - All 30 days: DK1 a = −142, b = 1.37; DK2 a = −121, b = 1.54.
  - First 15 target days: DK1 a = +243, b = 0.91; DK2 a = +314, b = 0.96.
  - Last 15 target days: DK1 a = −430, b = 1.71; DK2 a = −417, b = 1.96.
  - A slope above 1 means the forecast's swings are too small. The fit changes sign and size
    between the halves.
- **P10–P90 band (measured here, D+2..D+7).** The actual price was above P90 in 30 % (DK1) and 38 %
    (DK2) of hours and below P10 in 6 %. A calibrated band would give 10 % each. The provider
    reports 80.5 % / 80.3 % coverage in its backtest — [model card](https://huggingface.co/Elpriser/denmark-price-forecast).
- **Stability (measured here).**
  - Day-level error, mean over all runs and horizons D+2..D+7 per target day: DK1 mean −245, sd 376,
    negative on 80 % of the 30 days, ranging from +463 (2026-10-24, actual daily mean 253) to −1,060
    (2026-10-29, actual 2,224). DK2: mean −378, sd 423, negative on 80 %, +314 to −1,170.
  - Lag-1 autocorrelation of that series: 0.73 (DK1), 0.76 (DK2). Effective n 4.6 and 4.1;
    mean / standard error −1.4 (DK1), −1.8 (DK2). That is not significant at the 5 % level.
  - First 15 vs last 15 target days: DK1 −132 vs −358; DK2 −221 vs −535.
  - Per run (mean error over its settled D+2..D+7 hours): DK1 from +257 (run of 10-20) to −823
    (10-27); negative in 77 % of 30 runs. DK2 +169 to −929; negative in 90 %.
- **The most recent error predicts the next ones (measured here).** Correlation, over decision
  days, between the error of the run issued the day before on the day just published (D+1), and the
  error of the latest run on later days, both as daily means:

  | Later day | D+2 | D+3 | D+4 | D+5 | D+6 | D+7 |
  |---|---|---|---|---|---|---|
  | DK1 (n = 29…24) | +0.72 | +0.56 | +0.44 | +0.23 | +0.02 | −0.14 |
  | DK2 | +0.78 | +0.59 | +0.42 | +0.29 | +0.08 | −0.16 |

- **The provider's own explanation.** The model card says "a model trained on the older, calmer
  prices tends to run too low when the level rises". Its backtest "ends on 2026-07-30, before the price
  rise of September 2026". The model's daily level is kept, while its intraday shape is blended with a
  seasonal profile, because the raw curve "ranks hours _worse_ than a plain 4-week seasonal profile".
  It is "retrained from scratch and re-uploaded daily (12:10 UTC, after the day-ahead auction
  publishes)". It publishes MAE only, no signed bias — [model card](https://huggingface.co/Elpriser/denmark-price-forecast)
  (read 2026-11-06). The archived runs carry a `shapeBlend` of 0.00–0.44 (measured here).
- **Runs made before the auction.** The runs of 2026-10-29, 10-31 and 11-05 were generated before
  the next day's prices were out. They list that day as "forecast" with no values (measured here).
  All other runs list D and D+1 as published and forecast D+2..D+9.
- **Carnot.**
  - Its site gives no model, accuracy or bias. It speaks of "den bedste periode inden for de næste
    5 dage" — [carnot.dk](https://www.carnot.dk/).
  - A search for a public description of Carnot's method or accuracy found none — [search
    "Carnot elpris prognose model metode"]; [search "Carnot.dk elprisprognose kunstig intelligens
    nøjagtighed"]. Not found.
  - The Energi Data Service integration's Carnot connector requests `daysahead=7` and drops only
    today's entries (`if tmpdate.day != now.day`), so **tomorrow's forecast is kept**. It passes the
    prediction through without unit, VAT or tariff conversion in that file —
    [forecasts/carnot/__init__.py](https://raw.githubusercontent.com/MTrab/energidataservice/master/custom_components/energidataservice/forecasts/carnot/__init__.py).

### Inferences
- Reasoning: the maintainer's "always lower" is right in sign on 77–90 % of runs and 80 % of
  days in this month, in both areas. It is wrong in the hours an EV cares about most: on windy
  low-price days the forecast was *too high* (by +200 to +460 DKK/MWh), and in the cheapest fifth of
  actual hours it was too high 79–85 % of the time. A rule "the forecast is low, so add X" would be
  wrong exactly when it matters, when a cheap day is coming.
- Reasoning: the error behaves like a **level that lags the market**. It is persistent from day to
  day and largest just after a rise in level, and the model card says the same. That is the error
  structure an anchor on the latest published day can remove, and a long rolling average cannot.
- Reasoning: the run issued on D already knows D+1's settled prices. Yet its error on D+2 still
  correlates 0.72–0.78 with the error it made on D+1 the day before. So the forecast does not fully
  use information it has at issue time, and a simple post-processing can exploit that. (An optimal
  h-step forecast has errors that are "at most MA(h−1)"; see section 4. The correlation here is with
  information already known at issue, so this is a sign of inefficiency, not just overlap.)
- Reasoning: on the total price the bias is diluted by the known parts. In DK1 it is −12 to −17 % of
  the total against −16 to −22 % of spot, but it is the same in DKK/kWh. An additive correction in
  price units does not care which composition the caller passes, as long as the correction is
  computed on the same composition (section 3).
- The findings hold in **both areas**: sign, horizon profile, deeper error in day and evening
  hours, compression (slope > 1), dependence on level, persistence. DK2's bias is about 1.5–1.6×
  DK1's in DKK/MWh.

### Gaps
- One month (30 target days, 4–5 effective), autumn only, one provider. A calm period, summer, and
  a falling-price regime are not in the sample. The sign of the bias could reverse when prices fall
  (the windy days hint at this). This cannot be tested yet.
- **Carnot: untested** (no calls allowed); no public description of its method or bias found.
- Whether the elpriser.org model's bias shrinks once it has trained on the new price level is not
  known; the archive will show it.

## 2. Methods to use a biased forecast, defined and measured

### Takeaway
Ranked by the money a replanning charger saves, in both areas: **(c) an anchored shift that
decays over a few days > (a)/(b) markups and rolling bias corrections ≈ the raw forecast ≫ (d) shape
only or (e) rank only**. The anchored, decaying shift kept 84–94 % of the perfect-foresight saving
over a no-forecast planner, against 71–87 % for the raw forecast. Shape-only and rank-only methods
kept 8–61 %: **throwing away the forecast's level, even a biased one, cost more than the bias did**.
The trend is useful, as the maintainer says, but only when it is tied to the forecast's own value for
a slot whose price is now known. Which correction is used matters much less than using the
forecast at all. In DK1, total price, 30 kWh battery: raw 1.395, best method 1.357, and no forecast
1.624 DKK/kWh charged. With 30 decisions and 4–5 independent days, differences of a few points are
noise. Only the ordering (c) > raw > (d)/(e), seen in both areas and both halves, is evidence.

### Cited Findings
- **Decision set-up (measured here, `methods.py`).**
  - Decision day D, after the day-ahead auction. Prices are known through D+1, and the run issued
    on D forecasts D+2... Each method uses only what is known then: the errors of earlier runs on
    days up to D+1.
  - Each method gives an expected spot price per hour for D+2..D+7; the known tariff, Energinet
    tariffs, elafgift and VAT are then added.
  - Definitions (f = median of run D):
    - **raw**: f.
    - **(a) a+m**: f + m, with m in DKK/kWh on the total price, 0.05–0.4.
    - **(b) b_mean**: f minus the mean error at the same days-ahead over the last 14 settled target days.
    - **(b) b_lin**: a + b·f, least squares on the last 14 settled target days.
    - **(c) c_shift**: f + δ, where δ = actual mean of D+1 − the previous run's forecast mean for D+1.
    - **(c) c_decay**: f + w_k·δ, with w = 1, .75, .5, .25, 0, 0 for D+2..D+7.
    - **(c) c_same**: the previous run itself, shifted by δ. This is "the same run's forecast for
      tomorrow".
    - **(c) c_scale**: f × (actual mean D+1 / previous-run forecast mean D+1).
    - **(d) d_day**: known mean of D+1 + (f − that day's mean of f), i.e. within-day shape only.
    - **(d) d_horizon**: known mean of D+1 + (f − mean of f over D+2..D+7), i.e. shape and trend
      around the known level.
    - **(d) d_cont**: known mean of D+1 + (f − mean of f on D+2), i.e. the trend continues from the
      known level.
    - **(e) e_qmap**: the rank of each forecast hour mapped onto the distribution of the known hours
      of D and D+1.
    - **persist**: D+1's actual, same hour.
- **Level accuracy, spot DKK/MWh, D+2..D+7 (measured here, 3,816 forecast-hours per area).**

  | Method | DK1 bias / MAE | DK1 D+2 | DK1 D+5 | DK2 bias / MAE | DK2 D+2 | DK2 D+5 |
  |---|---|---|---|---|---|---|
  | raw | −264 / 419 | −209 / 357 | −280 / 438 | −428 / 531 | −349 / 441 | −455 / 567 |
  | a+0.3 | −24 / 358 | +31 / 326 | −40 / 376 | −188 / 415 | −109 / 339 | −215 / 455 |
  | b_mean | −152 / 384 | −105 / 319 | −131 / 410 | −226 / 430 | −159 / 336 | −212 / 448 |
  | b_lin | −126 / 375 | −34 / 307 | −151 / 396 | −182 / 408 | −52 / 298 | −226 / 448 |
  | c_shift | −87 / 368 | −7 / **255** | −105 / 393 | −136 / **382** | −19 / **246** | −171 / 407 |
  | c_same | −96 / 367 | −52 / **237** | −113 / 399 | −145 / 387 | −56 / **244** | −182 / 421 |
  | c_decay | −179 / 360 | −7 / 255 | −236 / 400 | −289 / 434 | −19 / 246 | −384 / 513 |
  | c_scale | −104 / 420 | +7 / 296 | −127 / 456 | −172 / 403 | −6 / 262 | −228 / 428 |
  | d_horizon | −145 / 490 | −66 / 354 | −163 / 524 | −164 / 511 | −48 / 353 | −197 / 541 |
  | d_cont | −113 / 419 | −37 / 317 | −130 / 442 | −150 / 451 | −39 / 336 | −184 / 478 |
  | e_qmap | −170 / 509 | −93 / 359 | −176 / 558 | −188 / 531 | −39 / 357 | −234 / 583 |
  | persist | −148 / 533 | −37 / 342 | −186 / 584 | −165 / 555 | −39 / 351 | −208 / 602 |

  The anchor cuts the D+2 error by about 30 % (DK1) and 45 % (DK2). By D+5 its advantage has mostly
  gone, as the correlation table in section 1 predicts.
- **Ranking inside the forecast days D+2..D+7 (measured here, 24 decisions whose six days are all
  settled, total price).** Spearman is over 144 hours, and over 6 days, each day scored by the mean
  of its 4 cheapest hours. The cheapest-day hit counts how often the chosen day was the actual
  cheapest (chance 1 in 6 = 17 %). Regret is the actual price of the 4 hours picked minus the
  actual 4 cheapest, in DKK/kWh.

  | Method | DK1 hour ρ | DK1 day ρ | DK1 cheapest day | DK1 regret | DK2 hour ρ | DK2 day ρ | DK2 cheapest day | DK2 regret |
  |---|---|---|---|---|---|---|---|---|
  | raw, a, c_shift, c_scale, d_horizon, d_cont | 0.84 | 0.53 | 54 % | 0.282 | 0.85 | 0.53 | 46 % | 0.269 |
  | b_mean | 0.83 | 0.52 | 58 % | 0.287 | 0.84 | 0.51 | 50 % | 0.257 |
  | c_decay | 0.83 | 0.64 | 54 % | 0.229 | 0.80 | 0.63 | 58 % | 0.217 |
  | c_same | 0.82 | 0.45 | 46 % | 0.351 | 0.83 | 0.43 | 42 % | 0.329 |
  | d_day | 0.69 | 0.27 | 21 % | 0.519 | 0.71 | 0.34 | 33 % | 0.568 |
  | e_qmap | 0.83 | 0.54 | 62 % | 0.183 | 0.84 | 0.53 | 54 % | 0.203 |
  | persist | 0.66 | – | 38 % | 0.617 | 0.68 | – | 33 % | 0.633 |

  A constant shift does not change the order of the forecast hours, so most methods tie here. The
  hourly ρ is high mostly because the known tariff (peak 17–21) orders the hours.
- **Charge now or wait (measured here).** Buy the 4 cheapest hours before the end of D+3 (28
  decisions) or D+5 (26). Known hours run from D 14:00 to D+1 23:00; the rest are forecasts. Mean
  regret against perfect foresight is in DKK/kWh, total price. "Waited" is the share of decisions
  that took a forecast hour; "paid" is the share of those waits that beat the cheapest known hours.

  | Method | DK1 D+3 regret | waited / paid | DK1 D+5 regret | DK2 D+3 regret | waited / paid | DK2 D+5 regret |
  |---|---|---|---|---|---|---|
  | known prices only | 0.221 | 0 % | 0.355 | 0.224 | 0 % | 0.352 |
  | raw | 0.119 | 75 % / 62 % | 0.204 | 0.123 | 79 % / 64 % | 0.190 |
  | a+0.1 | 0.114 | 75 % / 62 % | 0.198 | 0.108 | 71 % / 70 % | 0.182 |
  | a+0.3 | 0.120 | 71 % / 65 % | 0.189 | 0.102 | 68 % / 68 % | 0.160 |
  | b_mean | 0.119 | 75 % / 62 % | 0.183 | 0.110 | 71 % / 70 % | 0.171 |
  | b_lin | 0.130 | 71 % / 65 % | 0.197 | 0.107 | 64 % / 72 % | 0.152 |
  | c_shift | **0.087** | 57 % / 69 % | 0.158 | **0.088** | 50 % / 79 % | **0.148** |
  | c_decay | 0.093 | 61 % / 65 % | 0.184 | **0.086** | 57 % / 75 % | 0.172 |
  | c_scale | **0.082** | 61 % / 76 % | **0.154** | 0.094 | 61 % / 76 % | 0.156 |
  | d_horizon | 0.190 | 75 % / 52 % | 0.245 | 0.179 | 46 % / 69 % | 0.198 |
  | d_cont | 0.167 | 79 % / 64 % | 0.234 | 0.149 | 54 % / 67 % | 0.188 |
  | e_qmap | 0.293 | 75 % / 43 % | 0.290 | 0.299 | 82 % / 48 % | 0.288 |
  | persist | 0.264 | 89 % / 52 % | 0.461 | 0.279 | 93 % / 46 % | 0.477 |

- **Rolling replanning simulation (measured here, `methods.py`).**
  - Set-up: every day at 14:00 the planner solves a linear program over the known hours plus 6
    forecast days. The car is away 07–17 and uses 10 kWh per day at 07:00. The charger gives 11 kW,
    and the battery holds 30 or 50 kWh of headroom.
  - Only the next 24 hours are carried out, at actual prices, and the stock carries over. 30 decision
    days. Energy left at the end is valued at the period's mean night price.
  - "Oracle" is the same planner with actual prices over its 7-day window; "known only" plans on
    published prices alone. The table shows the share of the oracle's saving over known-only.

  | Method | DK1 total 30 | DK1 spot 30 | DK1 total 50 | DK1 spot 50 | DK2 total 30 | DK2 spot 30 | DK2 total 50 | DK2 spot 50 |
  |---|---|---|---|---|---|---|---|---|
  | oracle, DKK/kWh used | 1.313 | 0.830 | 1.088 | 0.650 | 1.351 | 0.843 | 1.125 | 0.662 |
  | known only, DKK/kWh used | 1.624 | 1.072 | 1.624 | 1.072 | 1.668 | 1.092 | 1.668 | 1.092 |
  | raw | 73 % | 79 % | 72 % | 79 % | 74 % | 87 % | 71 % | 74 % |
  | a+0.1 | 73 % | 85 % | 74 % | 83 % | 74 % | 82 % | 66 % | 74 % |
  | a+0.3 | 56 % | 67 % | 60 % | 68 % | 80 % | 89 % | 80 % | 87 % |
  | a+0.4 | 40 % | 62 % | 50 % | 65 % | 78 % | 84 % | 70 % | 78 % |
  | b_mean | 66 % | 78 % | 67 % | 73 % | 87 % | 86 % | 81 % | 81 % |
  | b_lin | 49 % | 60 % | 49 % | 60 % | 83 % | 84 % | 73 % | 74 % |
  | c_shift | 77 % | 78 % | 77 % | 77 % | 86 % | 87 % | 81 % | 77 % |
  | **c_decay** | **85 %** | **87 %** | **84 %** | **84 %** | **90 %** | **90 %** | **89 %** | **94 %** |
  | c_same | 79 % | 80 % | 82 % | 78 % | 79 % | 80 % | 78 % | 78 % |
  | c_scale | 86 % | 87 % | 83 % | 84 % | 84 % | 87 % | 80 % | 80 % |
  | d_day | 32 % | 43 % | 42 % | 41 % | 46 % | 51 % | 31 % | 34 % |
  | d_horizon | 52 % | 49 % | 55 % | 55 % | 36 % | 35 % | 40 % | 42 % |
  | d_cont | 38 % | 45 % | 46 % | 54 % | 48 % | 61 % | 51 % | 57 % |
  | e_qmap | 22 % | 21 % | 29 % | 20 % | 17 % | 17 % | 8 % | 14 % |
  | persist | 6 % | 43 % | 0 % | 16 % | 7 % | 40 % | 1 % | 8 % |

  In money, DK1 total 30 kWh: no forecast 1.624, raw 1.395, c_decay 1.358 DKK/kWh. Over the 300 kWh
  of the month that is about 69 DKK for using the forecast at all and about 11 DKK more for the best
  correction (my arithmetic).
- **Split-half check (measured here, `robustness.py`; 15 decisions per half, each half restarted;
  values above 100 % are possible because the oracle only sees 7 days).**
  - c_decay was at least as good as raw in 14 of 16 half-sample cells. It was below by 1 and 3
    points in the other two.
  - The undecayed c_shift was worse than raw in all four DK1 second-half cells (67–70 % vs 71–82 %)
    and in three DK2 second-half cells.
  - d_horizon was below raw in 15 of 16 cells.
  - Decay weights 1/.5, .5/.25 and 1/.75/.5/.25 were within a few points of each other.
  - a+0.1 against raw: ±15 points either way, with no consistent sign.

### Inferences
- Reasoning: **what each method needs.**
  - (a) needs nothing but a number. It is equivalent to a crude bias correction here, because the
    forecast is low; a+0.3 removed DK1's mean bias but helped DK2 and hurt DK1 in the simulation.
    It fails on the windy days when the forecast is too *high*.
  - (b) needs an archive of the integration's own past forecasts paired with settled prices, at
    least two weeks, kept per horizon. It lags a change in level by about its window. b_lin was
    the least robust; its coefficients change sign between halves (section 1).
  - (c) needs one thing: the forecast that was in hand *before* the latest publication, for the
    slots that publication covers, plus the settled prices for them. With elpriser.org that is the
    previous day's run; with Carnot it is the same feed's forecast for tomorrow, read before about
    13:00 (the connector keeps tomorrow). It adapts within one day.
  - (d) and (e) need only the current forecast and the known prices. That is why they are attractive,
    and why they fail: the known level of D+1 is a worse guess for D+4 than even a biased forecast.
- Reasoning: the decay weights in c_decay were chosen after seeing the correlation table, so its
  lead is partly in-sample. The safer statement is about the shape: **a full shift at the first
  forecast day, fading to none by about the fourth to fifth day after it**. All decaying variants beat
  the undecayed shift in the second half, which is where the full shift over-corrected.
- Reasoning: **the anchored shift is the "trend" type made usable.** It keeps the forecast's own
  day-to-day changes and replaces only its level, taken from the most recent comparison with a known
  price. The maintainer's trend, combined with "via a known anchor", is method (c), provided the
  anchor is the forecast's value for a slot that is now known. It is not (d), where the anchor is the
  known price level alone.
- Reasoning: ratio anchoring (c_scale) did as well as the additive shift here, but it divides by a
  forecast that can be near zero or negative. In DK1 2.7 % of hours were ≤ 0 over the past year
  (`research_notes/Cheapest home EV charging/price_forecast_uncertainty.md` §4). The additive form
  is the safe default; ratio is at most an option when the forecast for the anchor slot is clearly
  positive.
- Reasoning on D20's markup: once the systematic level error is removed by the anchor, the markup
  only has to price the residual uncertainty (the optimizer's curse). In this sample no markup size
  from 0.05 to 0.2 DKK/kWh could be told apart from zero, and 0.3–0.4 helped one area and hurt the
  other. The evidence still supports an engine default of zero and a small, caller-set markup.

### Gaps
- Not tested: c_decay combined with a markup; anchoring per hour of day (the night bias is smaller
  than the daily mean bias, so a daily shift may over-correct night hours); anchoring on the P10/P90
  band.
- The simulation is stylised: fixed daily use, one absence a day, no efficiency, no target dates,
  and a 7-day-window oracle rather than a global optimum.
- 30 decisions in one month cannot separate methods within about 10 points; the ordering (c) > raw >
  (d)/(e) is the robust part.
- Carnot not tested.

## 3. Contract: how known, expected and trend prices enter the engine

### Takeaway
Keep the engine's input to **two kinds, KNOWN and EXPECTED**, each a price per slot with its own
start and end, in the caller's units. **TREND should not be an engine price kind.** Turning a trend,
or a biased level, into an expected price needs three things the engine does not have:
- the forecast that was in hand before the last publication (state over time, D10);
- the split of the price into a forecast part and known tariff and tax parts (D3: prices are opaque);
- a source-specific rule.

Provide that conversion as a **pure helper in the same library**, outside `plan()`, which the
integration calls; the engine stays a pure, currency-agnostic function. Slots of different
lengths are handled by step mapping in the engine. The settlement period (hourly or quarter-hourly
billing) and the shaping of daily values are the integration's job. Nothing in this needs Denmark:
it needs a market whose day-ahead prices are published once a day, and a forecast that covered
the newly published slots.

### Cited Findings
- **The engine's principles.**
  - Prices are "opaque numbers in whatever currency the caller uses" (D3).
  - The engine is "A pure function. Same input, same output. No state between calls, no memory of an
    earlier plan" (D10); "Caching, debounce, hysteresis … and persistence belong to the integration".
  - Today's input is `PricePoint(start, price, is_forecast=False)`, "one per hour (sub-hour slots are
    a later question)" (O11).
  - Sources: [motor.md](../../motor.md) §1, §4.5; [decisions.md](../../decisions.md).
- **Known prices are quarter-hourly.** The 15-minute day-ahead unit went live for delivery on
  1 October 2025 "in all European bidding zones" — [APG](https://markt.apg.at/en/news-press/sdac-go-live-of-15-minute-market-time-unit-in-day-ahead-market-coupling-successful-as-of-september-30-2025/)
  (as cited in `price_forecast_uncertainty.md` §1). The `DayAheadPrices` rows used here are at
  :00/:15/:30/:45 (measured here).
- **Forecasts are hourly.** Both the elpriser.org archive (`hour` 0–23) and the Carnot connector
  (one `prediction` per `utctime`) are hourly — [OpenAPI spec](https://elpriser.org/api/openapi.json);
  [Carnot connector](https://raw.githubusercontent.com/MTrab/energidataservice/master/custom_components/energidataservice/forecasts/carnot/__init__.py).
- **Grid tariffs are hourly.** All DataHub tariff rows have resolution `PT1H` or `P1D`
  (`price_composition_denmark.md` §3). The N1 and Radius rows used here are `PT1H` (measured here).
- **How far quarter prices stray from their hour (measured here, `quarters.py`, 1,609 hours,
  2026-09-01 to 2026-11-06).**
  - The mean |quarter − hour mean| is 61 DKK/MWh (DK1) and 64 (DK2).
  - A fixed pattern by hour and quarter explains part of it; 44–45 remains.
  - The pattern is a ramp within hours where the price moves: hour 17 runs −189, −44, +66, +167
    (DK1); hour 08 runs +122, +50, −28, −144. Maximum ±193 DKK/MWh.
- **What the anchor needs exists in both Danish sources.** elpriser.org keeps every past run
  ([OpenAPI spec](https://elpriser.org/api/openapi.json)). The Carnot connector keeps tomorrow's
  forecast, so its pre-publication forecast for tomorrow is readable before about 13:00 ([connector
  code](https://raw.githubusercontent.com/MTrab/energidataservice/master/custom_components/energidataservice/forecasts/carnot/__init__.py)).

### Inferences
- **Reasoning, the recommended engine input.**
  ```
  PriceKind = KNOWN | EXPECTED
  PricePoint(start, end, price, kind=KNOWN, origin=None, spread=None)
  ```
  - `price` is in the caller's units and composition (spot only, or all-in). It is the price of the
    settlement period that contains the slot.
  - `origin` (EXPECTED only) is the end of the last published slot the expectation was anchored to.
    The D20/O4 markup is keyed on `start − origin`: the lead from the last publication, not from
    `now`, as the market-economist panel argued.
  - `spread` (optional) is a per-point uncertainty in price units, e.g. P90 − P50 when a source gives
    a band. A markup rule may use it in place of the step table.
  - KNOWN points carry no markup. Costs are always computed on `price` (D20).
- **Reasoning, why TREND stays out of the engine (option A weighed against option B).**
  - **A: the engine takes TREND points (a dimensionless index) and converts them with an anchor.**
    - For: it mirrors the maintainer's three types, and one implementation serves every caller.
    - Against, and decisive:
      - (1) The anchor that works (method c) is the forecast for slots that are now known, which by
        then the source has replaced. Only a caller that remembered it can supply it, so the call
        would have to carry a second, historical price series.
      - (2) The engine sees opaque totals and cannot tell spot from tariff and tax. A ratio index
        applied to an all-in price would scale the grid tariff and the taxes. An index given per day
        could only be spread flat over the day, wiping out the tariff's peak 17–21 and the
        forecast's own day shape.
      - (3) A dimensionless index plus the engine's own conversion adds tunables (decay weights,
        additive or ratio) and validation (O6, O10) to a core meant to trust clean input (D11).
      - (4) Section 2 showed that an index without a known-slot anchor (d_horizon, e_qmap) performs
        badly. So TREND points without an overlap would have to be refused anyway.
  - **B: the integration converts every source into EXPECTED before the call (recommended).**
    - The integration already owns persistence (D10), reads the tariffs, and knows each source's
      quirks: elpriser.org's previous run, Carnot's pre-13:00 tomorrow, the runs made before the
      auction.
    - To avoid each caller re-inventing it, put the conversion in the library as a pure,
      standard-library helper outside `plan()`, for example:
      ```
      anchor_forecast(forecast, anchor_forecast, anchor_known, decay_days=(1, .75, .5, .25),
                      mode=ADDITIVE) -> list[PricePoint(kind=EXPECTED, origin=…)]
      ```
    - It works on the *uncertain component only* (spot), before the caller adds known tariffs and
      taxes. It accepts a level forecast in any currency or a dimensionless index:
      - for an index, the anchor fits the level (additive) or the scale (ratio, only when the anchor
        forecast is clearly positive);
      - with no anchor available it returns the forecast unchanged, rather than a shape-only guess.
- **Reasoning, mixed slot lengths (the coordinator's point 1).**
  - **Engine.**
    - It accepts slots of any length.
    - It builds its grid from the union of all slot boundaries, so the finest input, e.g. 15 minutes,
      sets the step.
    - A price given for a longer slot applies unchanged to every finer piece inside it (a step).
    - It never interpolates or invents a shape.
    - This needs O11 resolved as "slot = start and end", and `simulation_step_minutes` must divide
      the shortest slot.
  - **Integration, settlement period.**
    - It passes the price of the *billed* period. Under hourly billing it averages the four quarter
      prices to the hour before the call. Otherwise the engine would choose "cheap quarters" whose
      price nobody bills.
    - Under quarter-hour billing it passes the quarter prices as they are.
    - The engine needs no setting for this: it sees what it is billed.
  - **Integration, hourly expected prices under quarter billing.**
    - Step mapping is the honest default. The fixed intra-hour ramp of up to about ±190 DKK/MWh
      (measured above) is real, but smaller than the forecast error (MAE 350–450 at D+2).
    - The helper may add the mean quarter pattern learned from recent known quarters, as an option.
  - **Integration, daily expected values** (a source that gives one level per day):
    - The integration composes the hourly or quarter-hourly expected price: daily expected spot,
      times or plus a within-day spot shape (from an hourly forecast when present, else the last
      known day's shape), plus the known tariff per slot.
    - It must not hand the engine a flat daily total.
- **Reasoning, nothing Danish (the coordinator's point 3).**
  - The anchor is defined as "the latest published day-ahead slots, compared with the forecast that
    covered them before publication". That exists wherever day-ahead prices are published once a day:
    every SDAC bidding zone, and other once-daily auctions.
  - The decay is in days since that publication, not in clock hours or CET.
  - The shift is additive in the caller's currency, applied to the component the forecast covers.
  - VAT, tariffs and taxes are added by the market's adapter after anchoring, so the helper holds no
    Danish constant.
  - Defaults are relative: the weights. Any amount, such as a markup, is set by the caller in its
    own units (D3, D4).
- **Reasoning, the maintainer's three types in this design.**
  - (1) Known → KNOWN.
  - (2) Expected (a level) → EXPECTED, after the anchor removes the level bias.
  - (3) Trend (shape only) → an input of the helper, which turns it into EXPECTED by anchoring on the
    overlap with known slots. The engine never sees a dimensionless number.
- **Holds in both areas.** The design does not depend on which area or grid company; the measured
  ordering of methods behind it was the same in DK1/N1 and DK2/Radius.

### Gaps
- How Carnot's feed behaves after 13:00 (whether its tomorrow values are replaced by actuals,
  revised, or left) is not verified without a key. The integration must log the pre-publication
  values itself.
- A source with no overlap at all (a forecast starting after the published horizon, with no past
  runs kept) cannot be anchored; for it, only the raw level or a markup remains. Its share of real
  users is unknown.
- O11 details (the `simulation_step_minutes` default for 15-minute slots, DST days of 92/100
  quarters) are not settled here.

## 4. Literature on recalibration and bias correction

### Takeaway
Electricity-price-forecasting literature mostly means by "recalibration" re-estimating the model
daily on a rolling window, and it warns that the choice of window is risky. Post-processing in that
literature turns point forecasts into distributions. Weather forecasting has the closest analogue to
what this engine needs: a decaying-average correction of the mean error, operational at NCEP since
2006, which "works well for the first few days" and **fails when the error regime changes**. That is
the same failure the rolling corrections (b) showed here. Forecast-evaluation theory says that errors
predictable from information known at issue (a non-zero intercept, a slope ≠ 1) mean bias. No study
was found on correcting multi-day price forecasts for EV charging.

### Cited Findings
- **Decaying-average bias correction (weather ensembles).** An "adaptive (Kalman Filter type)
  algorithm". The bias estimate is updated each day by "the weighted average of the new forecast
  error … with a weight of w, and the previous average, with a weight of 1-w". Weights of 1, 2 and
  10 % were tried; "the 2% work better for most regions and seasons". "Preliminary results show that
  an adaptive, regime dependent bias correction method works well for the first few days" —
  [Cui, Toth, Zhu, Hou, Unger & Beauregard, NCEP manuscript](https://www.emc.ncep.noaa.gov/gmb/ens/papers/manuscript_thorpex_bocui.pdf).
- **Its failure at regime changes.** "applying decaying method leads to a degradation of forecast
  accuracy during transition seasons". "The Ebc2% method is failed in March and April, when error
  characteristics experience a dramatic change within a period of ~50-60 days … This outdated
  information leads to degrading forecast … most pronounced for longer forecast lead times". "The
  Ebc10% is slightly better than the Ebc2%" —
  [Guan, Zhu & Cui, AMS 2014 extended abstract](https://ams.confex.com/ams/94Annual/webprogram/Manuscript/Paper232804/AMS94_extabs_hg_20140220.pdf).
- **Mincer-Zarnowitz.**
  - Regress y(n+h) = α + β·y(n+h|n) and "Test the joint hypothesis α = 0, β = 1. If the
    coefficients are different, it indicates systematic bias in the historical forecasts".
  - Optimal forecasts are "Unbiased"; "1-step-ahead errors are white noise"; "h-step-ahead errors are
    at most MA(h-1)".
  - Source: [Hansen, "Evaluating Forecasts", UW-Madison Econ 390 lecture](https://users.ssc.wisc.edu/~bhansen/390/2010/390Lecture23.pdf).
- **Recalibration in EPF means daily re-estimation.**
  - Models are "continuously recalibrated on daily basis to incorporate the input of recent data".
  - "The amount of past data employed for estimation defines the calibration window"; windows of
    8 weeks, 12 weeks, 3 and 4 years were used.
  - "it might be desirable to employ only recent data, e.g. to avoid estimating effects that no
    longer play a role".
  - Source: [Lago, Marcjasz, De Schutter & Weron 2021, arXiv:2008.08004](https://ar5iv.labs.arxiv.org/html/2008.08004).
- **Choosing the window is risky.** "the variability of prediction errors across windows of
  different lengths and across datasets can be substantial", so "selecting ex-ante one window is
  risky"; "averaging forecasts across different calibration windows is a robust alternative" —
  [Marcjasz, Serafin & Weron 2018, Energies 11(9):2364, abstract](https://ideas.repec.org/a/gam/jeners/v11y2018i9p2364-d168385.html).
- **Post-processing of point forecasts in EPF is about distributions.** Three methods for "converting
  point forecasts of day-ahead electricity prices" into probabilistic ones: Quantile Regression
  Averaging, Conformal Prediction and Isotonic Distributional Regression. Their combination beat
  "state-of-the-art Distributional Deep Neural Networks" on German and Spanish data —
  [Lipiecki, Uniejewski & Weron 2024, Energy Economics 107934, arXiv:2404.02270](https://arxiv.org/abs/2404.02270v2) (abstract).
- **The provider's own post-processing.**
  - P10/P90 are widened by conformal multipliers of 1.7–2.2×, because "LightGBM's raw quantile spread
    covers only 50-55% of outcomes".
  - The daily level is kept and the intraday shape blended with a seasonal profile.
  - Source: [model card](https://huggingface.co/Elpriser/denmark-price-forecast).
- **Hybrid error correction.** A day-ahead model combining a techno-economic model with statistical
  models; the abstract gives no correction formula or numbers —
  [Watermeyer, Möbius, Grothe & Müsgens 2023, arXiv:2304.09336](https://arxiv.org/abs/2304.09336) (abstract only).
- **Optimizer's curse.** Choosing the option with the lowest estimate makes the chosen option dearer
  than estimated, even with unbiased estimates (Smith & Winkler 2006, as cited and quoted in
  `price_forecast_uncertainty.md` §5; not re-opened here).

### Inferences
- Reasoning: the NCEP experience maps onto this data. A slow correction (2 %, about 50–60 days of
  memory) failed at transitions; here, the 14-day mean (b_mean) and the 14-day linear fit (b_lin) did
  worse than a one-day anchor in the month with a sharp rise. The "10 %" variant doing better there
  points the same way: when regimes shift, short memory wins.
- Reasoning: the anchored shift with decay is a decaying-average correction with w = 1 on the latest
  day's error, applied with a weight that shrinks with lead time. The literature supports it for
  "the first few days" and warns against it at long leads. That matches the measured correlation
  falling to about 0 by D+6.
- Reasoning: Marcjasz et al. suggest a hedge. Averaging a one-day anchor with a slower estimate (for
  example 0.7 × the anchor + 0.3 × a 14-day mean) may be more robust than either alone. Not tested here.
- Reasoning: the band was under-covered at the top (30–38 % of actuals above P90). So a `spread`
  taken from P90 − P50 would be too narrow in a rising regime, not too wide. The same anchor shift
  should apply to P10/P90 if they are used.

### Gaps
- No published study of bias correction for multi-day (D+2..D+7) electricity price forecasts used
  in a scheduling decision was found.
- Cui et al. 2012 (Weather and Forecasting 27) itself was not opened; the NCEP manuscript and the
  AMS 2014 abstract were.
- Mincer & Zarnowitz 1969 was not opened; the lecture notes were.

## 5. What this means for D20, O4, O11 and the maintainer's proposal

### Takeaway
- The maintainer is right on all three observations, with two corrections:
  - the forecast is usually, not always, low; it was high on the cheap windy days;
  - the trend is useful only when tied to a known price through the forecast's own value for that
    price's slots. "Shape around today's level" did worse than the biased level.
- The design that follows:
  - the engine takes KNOWN and EXPECTED points with start/end and an `origin`;
  - the integration, through a pure library helper, turns any forecast or trend into EXPECTED by
    an additive anchored shift that fades over about four days;
  - D20's markup stays, keyed on the lead from `origin`, with no default amount in the engine.
- These conclusions held in DK1/N1 and DK2/Radius, in both halves of the month, and on spot and
  total prices. Carnot is untested.

### Cited Findings
- Anchored, decaying shift: 84–94 % of the oracle's saving in all eight simulation cells, against
  71–87 % raw, 8–61 % for shape-only and rank-only methods; not below raw in 14 of 16 half-sample
  cells (section 2, measured here).
- Bias: −16 to −22 % of spot in DK1 and −25 to −34 % in DK2, unstable in size, 4–5 effective days.
  Anchor error correlation with the next days: 0.72–0.78 at D+2, about 0 by D+6 (section 1, measured
  here).
- D20 as written uses `price × (1 + markup / 100)` — [motor.md](../../motor.md) §6.4. O4 proposes
  "A stepped curve `[(hours_ahead, percent), ...]`" — [decisions.md](../../decisions.md).

### Inferences
- Reasoning for O4:
  - Additive, not percent; keyed on the lead from the last publication; engine default 0.
  - No calibrated default amount exists. Markups of 0.05–0.2 DKK/kWh were indistinguishable from
    0, and 0.3–0.4 split the two areas.
  - The systematic part of the error belongs to the anchor in the integration, not to the markup.
- Reasoning for O11: slots with start and end; step mapping in the engine; billed prices and the
  shaping of daily values in the integration.
- Reasoning for the integration: it must log the forecast it holds just before each publication.
  That costs one day's forecast per day, which it then compares with the published prices. It is
  also the archive that will, in a few months, allow the decay weights and any markup to be
  calibrated on Carnot as well as elpriser.org.

### Gaps
- One month, one provider, a rising market. The weights and any markup need a longer archive
  (elpriser.org keeps 400 days from 2026-10-06; Carnot must be logged).
- Carnot untested.
