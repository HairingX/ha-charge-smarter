# Danish electricity price forecasts: horizon, error and the charge-now-or-wait decision

Research for D20, O4 and S1 (`docs/design/decisions.md`, `docs/design/research.md`), done on
2026-10-28. Rule followed: every factual claim cites a page, file or command output that was
opened during this task. "Measured here" marks numbers I computed myself from downloaded data;
the method is stated beside them. "Reasoning" marks my own argument.

Data pulled for the measurements (all on 2026-10-28):
- Energi Data Service `DayAheadPrices`, DK1 and DK2, 2025-10-01 to 2026-10-27, 75,272
  quarter-hour records: `https://api.energidataservice.dk/dataset/DayAheadPrices?start=2025-10-01&end=2026-10-28&filter={"PriceArea":["DK1","DK2"]}&limit=0`.
  The records are at quarter-hour resolution (e.g. `TimeDK` 23:45, 23:30). I averaged them to
  hourly values by local hour.
- elpriser.org forecast archive, all 23 runs issued 2026-10-06 to 2026-10-28 for DK1 and DK2:
  `https://elpriser.org/api/forecast/archive?area=DK1&issued=YYYY-MM-DD` (and `area=DK2`).
  Each run gives a median (`spot_dkk_mwh`) and P10/P90 (`spot_min_dkk_mwh`, `spot_max_dkk_mwh`)
  per hour for the days after the published day-ahead prices.
- The scripts were throwaway and are not kept. The method is described with each result.

## 1. Which forecasts exist for DK1/DK2 beyond day-ahead, and how Home Assistant users get them

### Takeaway
Day-ahead prices for tomorrow are published around 13:00 CET and are exact. Since 1 October
2025 they come in 15-minute units. Beyond that, Danish Home Assistant users have two
free forecast sources I could verify. **Carnot**, through the Energi Data Service integration,
needs a free key; I could find no published accuracy for it. **elpriser.org** needs no key and
publishes median plus P10/P90 for D+2 to D+9 with a stated backtest. Energinet's Energi Data
Service publishes wind and solar forecasts but, in the listing I could read, no price forecast.

### Cited Findings
- **Day-ahead publication.** Nord Pool day-ahead prices are published at 13:00 CET — [Kjellergren & Lindqvist Sabel, Lund University master's thesis 2026, §5.2](https://lup.lub.lu.se/student-papers/record/9244798/file/9244801.pdf). A forecast maker quoted on ing.dk says tomorrow's prices are known by 13:00 — [ing.dk, 2023](https://ing.dk/artikel/podcast-saadan-laver-man-detaljeret-prognose-de-kommende-dages-elpriser-265746). I could not open Nord Pool's own page with the auction times: the [day-ahead page](https://www.nordpoolgroup.com/en/trading/Day-ahead-trading/) and the [15-min MTU FAQ](https://www.nordpoolgroup.com/en/trading/transition-to-15-minute-market-time-unit-mtu/faq/) rendered without content.
- **15-minute market time unit.** It went live in the Single Day-Ahead Coupling "on the trading day of 30 September 2025 for the delivery day of 1 October 2025", "in all European bidding zones and across bidding zone borders" — [APG](https://markt.apg.at/en/news-press/sdac-go-live-of-15-minute-market-time-unit-in-day-ahead-market-coupling-successful-as-of-september-30-2025/). Energi Data Service `DayAheadPrices` for DK1/DK2 are quarter-hourly (measured here, records at :00/:15/:30/:45). Its old `Elspotprices` dataset "is no longer updated. For data after 2025-09-30 see Day-Ahead Prices" (Energi Data Service catalogue, `https://api.energidataservice.dk/meta/dataset`). This bears on O11.
- **Energi Data Service (Energinet).** The catalogue lists `DayAheadPrices`, `Forecasts_Hour` ("Forecast of wind and solar power with a resolution of one hour"), `Forecasts_5Min` and `CO2EmisProg`. It lists no spot-price forecast dataset (`https://api.energidataservice.dk/meta/dataset`, fetched 2026-10-28). Caveat: the call returned 100 datasets and may be truncated.
- **Carnot, through the Home Assistant Energi Data Service integration** (MTrab/energidataservice, v1.6.22, commit 4b4085d of 2026-10-25):
  - The README offers "AI generated price forecasts for your selected region, provided by Carnot", described as "a 5 day price forecast for the next week". A Carnot API key is required, free of charge — [README](https://github.com/MTrab/energidataservice).
  - The connector calls `https://whale-app-dquqw.ondigitalocean.app/openapi/get_predict?region=dk1|dk2&energysource=spotprice&daysahead=7` with `apikey` and `username` headers. It reads `predictions[].prediction` and `utctime`, and drops today's entries. Its regions are only `DK1` and `DK2` — [forecasts/carnot/__init__.py](https://github.com/MTrab/energidataservice/blob/master/custom_components/energidataservice/forecasts/carnot/__init__.py), [regions.py](https://github.com/MTrab/energidataservice/blob/master/custom_components/energidataservice/forecasts/carnot/regions.py) (read from a clone of the repository).
  - The integration polls Carnot every 30 minutes (`CARNOT_UPDATE = timedelta(minutes=30)`). It exposes the result as a `forecast` attribute on the price sensor, with attribution "and forecast from Carnot" — [__init__.py](https://github.com/MTrab/energidataservice/blob/master/custom_components/energidataservice/__init__.py), [sensor.py](https://github.com/MTrab/energidataservice/blob/master/custom_components/energidataservice/sensor.py).
  - The forecast is a single number per hour: no interval or quantiles (same connector source).
- **Carnot's own site** speaks of recommendations "inden for de næste 5 dage" (within the next 5 days). It gives no accuracy figures and no description of a forecasting model — [carnot.dk](https://www.carnot.dk/). A search for Carnot accuracy found nothing — [search: "Carnot elpris prognose hvor præcis nøjagtighed"]; the result was not found.
- **elpriser.org** (API `/api/forecast`, no key, "No key, no rate limit, full CORS", "Free for any use"):
  - It covers "Today and the next nine days, hour by hour", for DK1 and DK2. Days with a published price are `type: "actual"`.
  - Model days carry `price` (the median) and `min`/`max`, which are "the model's P10 and P90, widened until they cover 80 % of outcomes in backtests". A heuristic fallback uses the four-week same-weekday min/max instead.
  - The API offers price modes including tariffs, net tariffs (by grid company GLN) and VAT.
  - An archive of past runs (raw spot, DKK/MWh, excl. VAT) starts 2026-10-06 and is kept 400 days — [OpenAPI spec](https://elpriser.org/api/openapi.json).
- **elpriser.org model card.** The model is LightGBM quantile regression (P10/P50/P90) per area for days 2–9 ahead; "Days 0-1 are published prices, not modelled". It is retrained daily at 14:10 UTC after the day-ahead auction publishes — [Hugging Face, Elpriser/denmark-price-forecast](https://huggingface.co/Elpriser/denmark-price-forecast).
- **elforbrug.nu.** Another Danish forecaster, Henrik Møller Jørgensen of elforbrug.nu, said in 2023 that his "Prognoserne rækker fem dage frem" (forecasts reach five days ahead), made "Ved hjælp af AI og en lang række datakilder". No accuracy was stated — [ing.dk](https://ing.dk/artikel/podcast-saadan-laver-man-detaljeret-prognose-de-kommende-dages-elpriser-265746).
- **Strømligning.** Its API covers Danish hourly rates and network costs, licensed CC BY-NC 4.0. The search results showed no forecast endpoint — [search result for stromligning.dk/api/docs](https://stromligning.dk/api/docs) (page itself not opened, so a forecast endpoint is unconfirmed).
- **Tibber.** [Tibber developer docs](https://developer.tibber.com/docs/guides/pricing) rendered without content. I could not access them.

### Inferences
- Reasoning: a Danish user who wants a forecast with an uncertainty band can only get one today
  from elpriser.org. Carnot, the source the main HA integration uses, gives a point forecast
  with no band and no published accuracy. So the engine cannot assume quantiles are always
  available. A per-price `confidence_upper` (O4) should stay optional, with a markup fallback.
- Reasoning: published prices extend to the end of tomorrow after about 13:00 CET, so the
  "known" horizon swings between about 11 and 35 hours over the day. Forecasts cover the rest
  of a 7-day horizon.
- Reasoning: since 1 October 2025 the published prices are quarter-hourly, while both
  forecasts are hourly. The contract will see mixed resolutions (O11).

### Gaps
- Carnot: no accuracy, update cadence of the model itself, or methodology found. The README
  says "5 day", while the code requests `daysahead=7`; how many days actually come back was not
  verified (needs a key).
- Nord Pool, Volue/Montel and other commercial providers: not checked. Nord Pool's pages were
  unreadable.
- Tibber: whether it offers any price forecast beyond tomorrow is unknown (could not access the docs).

## 2. Measured forecast error by horizon, and which metric to use

### Takeaway
For Danish prices, forecasts from D+2 onward have a mean absolute error of roughly a quarter to
a third of the mean price: about 150–200 DKK/MWh (0.15–0.20 DKK/kWh) on spot. That is several
times the "8–11 % MAPE" in `research.md`, which I could not find again. MAPE is the wrong metric
here; the literature recommends MAE-type and relative-MAE metrics for points, and pinball
loss/CRPS for quantiles.

### Cited Findings
- **elpriser.org v3 backtest** (rolling origin, April 2025–July 2026, monthly retraining). MAE as a share of the mean price:
  - DK1: ~25 % for T+1..2 and ~30 % for T+3..9.
  - DK2: ~27 % and ~31 %.
  - Baselines: a seasonal 4-week heuristic gets ~35–38 %, naive persistence ~41–46 %.
  - Hit rate for the cheapest hour falling in the predicted top-3: 69 % (DK1), 70 % (DK2).
  - After calibration, P10–P90 coverage is 80.5 % / 80.3 %. The raw LightGBM quantile spreads covered only "50-55% of outcomes", fixed with conformal multipliers of 1.7–2.2×. The authors call the backtest figures "a floor".
  - Source: [Hugging Face model card](https://huggingface.co/Elpriser/denmark-price-forecast).
- **Same provider, MAE in DKK/MWh** (486-day backtest, 2025-04-01 to 2026-07-30), "23–32 % of the mean price, against 35–38 % for a four-week same-weekday average" — [OpenAPI spec](https://elpriser.org/api/openapi.json):

  | Horizon | DK1 MAE | DK2 MAE |
  |---|---|---|
  | D+2 | 149 | 165 |
  | D+5 | 179 | 192 |
  | D+9 | 197 | 211 |

  The model card's "T+1..2" and the spec's "D+2" label the first forecast day differently.
- **Swedish SE3, multi-day forecast for EV charging** (Volvo Cars / Lund; out-of-sample 2025-01-01 to 2026-05-01). nMAE = MAE / mean price. The best model (Random Forest) by lead band, hours after model initialisation — [Kjellergren & Lindqvist Sabel 2026, Table 5.8](https://lup.lub.lu.se/student-papers/record/9244798/file/9244801.pdf):

  | Lead (h) | 18 | 19–24 | 25–30 | 43–48 | 49–58 | 60–72 | 73–96 | 97–120 | 121–144 | 145–168 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | nMAE % | 22.7 | 29.0 | 36.8 | 38.5 | 40.2 | 41.7 | 44.4 | 47.9 | 50.3 | 52.3 |
  | MAE €/MWh | 7.64 | 12.79 | 17.20 | 20.10 | 20.72 | 22.11 | 23.47 | 25.47 | 26.82 | 27.72 |

  R² falls "from 0.835 at h=13–18 to 0.27–0.33 at h=145–168". The abstract says "the broader price pattern remains clear over the first two to four days".
- **Measured here, elpriser.org archive, 3 weeks of live runs** (issued 2026-10-06 to 2026-10-28). Method: hourly medians from each run compared with Energi Data Service day-ahead prices averaged to the hour. Days ahead are counted from the issue date. P10–P90 coverage target is 80 %. The sample is small (13–20 forecast days per horizon, overlapping runs, one October), so this illustrates; it does not calibrate.

  | Days ahead | DK1 MAE (DKK/MWh) | DK1 MAE/mean | DK1 cover | DK2 MAE | DK2 MAE/mean | DK2 cover | DK2 bias (fc − actual) |
  |---|---|---|---|---|---|---|---|
  | D+2 | 227 | 23 % | 83 % | 273 | 27 % | 80 % | −136 |
  | D+3 | 241 | 24 % | 82 % | 305 | 30 % | 77 % | −158 |
  | D+4 | 247 | 24 % | 78 % | 298 | 28 % | 77 % | −157 |
  | D+5 | 279 | 26 % | 78 % | 332 | 30 % | 73 % | −160 |
  | D+6 | 298 | 28 % | 79 % | 368 | 33 % | 75 % | −175 |
  | D+7 | 325 | 31 % | 84 % | 371 | 35 % | 82 % | −136 |
  | D+8 | 287 | 28 % | 81 % | 331 | 31 % | 77 % | −122 |
  | D+9 | 357 | 35 % | 83 % | 400 | 38 % | 77 % | −116 |

  In this window, mean actual prices were about 1,000–1,100 DKK/MWh. DK1 bias ranged from −55 to +42.
- **The "8–11 % MAPE" figure.**
  - I did not find it.
  - The closest published Nordic figure is in the open epftoolbox benchmark. For the Nord Pool *system price*, day-ahead, test period 27.12.2016–24.12.2018, MAPE is 5.46–6.36 % and sMAPE 5.00–5.66 % — [Lago, Marcjasz, De Schutter & Weron 2021, Applied Energy 293:116983, Table 2](https://arxiv.org/abs/2008.08004) (PDF read).
  - That dataset is one where "the prices are always positives, zero prices are rare, and prices spikes seldom occur" (same paper, §3.2). It is a day-ahead forecast of a different price than DK1/DK2, in a calmer period.
- **Metric choice.**
  - Lago et al.: "since MAPE values become very large with prices close to zero (regardless of the actual absolute errors), the MAPE is usually dominated by the periods of low prices and is also not very informative". For EPEX-DE the MAPE was 83–133 % while sMAPE was 14.7–17.2 %, "due to prices in Germany being negative and very close to 0".
  - They argue "a better metric is the relative MAE (rMAE)", which "should always be" included. They prefer linear (absolute) losses because "in most electricity trade applications, the underlying risk, profits, and costs depend linearly on the price and on the forecasting errors".
  - Source: [Lago et al. 2021](https://arxiv.org/abs/2008.08004) (PDF read).
- **Probabilistic evaluation.**
  - It "boils down to 'maximizing sharpness subject to reliability'". The pinball loss is "arguably the most popular" proper scoring rule, and CRPS integrates it.
  - For price *paths* (ensembles) "the recommended option is the energy score", but its "use in EPF is limited".
  - Source: [Maciejowska, Uniejewski & Weron 2023, Oxford Research Encyclopedia, arXiv:2204.11735](https://arxiv.org/abs/2204.11735) (PDF read).
  - The same principle heads Nowotarski & Weron's probabilistic EPF review (RSER 81, 2018) — [IDEAS abstract](https://ideas.repec.org/p/wuu/wpaper/hsc1607.html). I could not access its full text (the PDF host timed out).

### Inferences
- Reasoning: for a charging planner the cost of a wrong decision is linear in price error ×
  kWh. So MAE in price units, together with error at the cheap end of the ranking (section 4),
  is the right yardstick for calibrating O4; MAPE is not. Negative and near-zero prices
  (section 4) make MAPE undefined or explosive in exactly the hours the engine wants.
- Reasoning: the published elpriser MAE (149–211 DKK/MWh) and my 3-week check (227–400) are
  both far above 8–11 % of price. A markup of a few percent would be much smaller than the
  actual error.

### Gaps
- No published accuracy for Carnot, Tibber, Nord Pool or Volue/Montel forecasts for DK1/DK2.
- No published DK1/DK2 error per single day ahead (D+2, D+3, …, D+7) beyond the three points in
  the elpriser spec. My table is three weeks of one month.
- Nowotarski & Weron 2018 full text: could not access.

## 3. How error grows with horizon: linear, √t, or saturating?

### Takeaway
Error grows **less than linearly and less than √t**. The big step is from known (zero error) to
the first forecast day. After that, multi-day error rises slowly, about +30 % from day 2 to day
7–9, and levels off after about a week. A stepped curve with a large first step and a gentle,
flattening rise is supported in shape; a linear-in-hours markup is contradicted.

### Cited Findings
- **Germany, day-ahead prices, 2018–2024**, RMSE in EUR/MWh by horizon in days — [Ghelasi & Ziel, arXiv:2406.00326, Table 6](https://arxiv.org/abs/2406.00326) (PDF read):

  | Model | 1 d | 7 d | 14 d | 30 d | 90 d | 360 d |
  |---|---|---|---|---|---|---|
  | Current | 24.41 | 43.59 | 47.80 | 54.36 | 66.34 | 97.29 |
  | Expert | 24.17 | 41.80 | 48.09 | 60.54 | 74.79 | 187.91 |
  | Naive | 39.46 | 47.21 | 53.12 | 61.84 | 72.62 | 98.38 |
  | Week dummies | 76.95 | 76.92 | 77.17 | 77.79 | 78.78 | 80.17 |

  "while the expert model performs best for the day-ahead setting … other models outperform it for higher horizons" (same paper).
- **Germany/Austria EPEX, 1–28 days ahead with futures.** For the best model the error "reaches a convergence point after approximately one week". The mean MAE over the 4-week horizon is 7.19 EUR/MWh — [Steinert & Ziel, arXiv:1801.10583](https://arxiv.org/abs/1801.10583) (read via [ar5iv](https://ar5iv.arxiv.org/html/1801.10583); the per-horizon figure is described only in prose).
- **Sweden SE3.** nMAE rises from 29.0 % at 19–24 h to 52.3 % at 145–168 h (table in section 2). The authors attribute the decline "mostly [to] the loss of weather forecast skill at multi-day leads". The "10–90 % quantile band widens with lead time … the rate of widening is steeper in the winter window" — [Kjellergren & Lindqvist Sabel 2026](https://lup.lub.lu.se/student-papers/record/9244798/file/9244801.pdf).
- **Denmark.**
  - elpriser.org DK1 MAE is 149 → 179 → 197 DKK/MWh at D+2 → D+5 → D+9 — [OpenAPI spec](https://elpriser.org/api/openapi.json).
  - My 3-week check rose from 227 (D+2) to 325–357 (D+7–D+9), not monotonically (D+8 < D+7). Same pattern for DK2 (section 2 table, measured here).

### Inferences
- Reasoning: power-law exponents fitted to these numbers (my arithmetic, error ∝ t^k):
  - Germany, Current model, 1 d → 7 d: 24.4 → 43.6, ×1.79 for ×7 horizon, k ≈ 0.30.
  - SE3, ~21 h → ~156 h: 29.0 → 52.3 %, ×1.80 for ×7.4, k ≈ 0.29.
  - DK1 elpriser, D+2 → D+9: ×1.32 for ×4.5, k ≈ 0.19.
  - √t would be k = 0.5 and linear k = 1. All three are well below √t.
  - The German and SE3 curves both run from day 1 *forecast* to day 7. For this engine, day 1
    is published, so the forecast part starts at D+2, where the curve is already flatter
    (k ≈ 0.2).
- Reasoning: this matches the mean-reversion argument in `research.md`. It also shows that
  error does not saturate *within* a week in all data (SE3 keeps rising to 168 h), but it
  rises slowly. Ghelasi & Ziel's naive and week-dummy models show where it ends: a
  climatological error that the week-dummy model reaches at every horizon (≈77–80 EUR/MWh in
  Germany).
- Reasoning: the linear proposal that was rejected (5 % + 0.2 %/h) puts at 168 h a markup of
  38.6 %, 7.7× its first-hour value. The data says the error at D+7 is about 1.3–1.8× that at
  the first forecast day. The rejection is supported.

### Gaps
- No Danish per-hour-ahead error curve from a peer-reviewed source.
- How the error curve of Carnot (the forecast most HA users have) grows is unknown.

## 4. Is a percentage markup the right shape? Prices near zero or negative

### Takeaway
No. Forecast error in Danish prices is roughly constant in *absolute* terms, not proportional
to the price level. In relative terms it is largest exactly in the cheap hours the engine
picks, and a percentage cannot treat zero or negative prices sensibly. An **additive** markup
in price units (or an upper quantile, where available) is the shape the evidence supports.

### Cited Findings
- **Low and negative prices are common in Denmark** (measured here; Energi Data Service, hourly averages, 2025-10-01 to 2026-10-27):

  | | DK1 | DK2 |
  |---|---|---|
  | Hours ≤ 0 | 2.7 % | 1.3 % |
  | Hours within ±75 DKK/MWh (≈ ±10 EUR/MWh) of zero | 7.7 % | 7.1 % |
  | Mean / median price | 779 / 759 DKK/MWh | 794 / 775 DKK/MWh |
  | Price range | −234 to 5,518 DKK/MWh | — |

  DK1's share of hours ≤ 0 reached 7 % in April, May and July 2026.
- **Measured here: absolute error does not scale with the forecast level.** Same 3-week archive, all horizons pooled, binned by the forecast median into quartiles:

  | Forecast-level quartile (DKK/MWh) | DK1 MAE | DK1 relative | DK2 MAE | DK2 relative |
  |---|---|---|---|---|
  | Lowest (DK1 −78..791; DK2 −16..706) | 347 | 63 % | 348 | 74 % |
  | Highest (DK1 1,250..2,201; DK2 1,132..2,070) | 234 | 16 % | 330 | 25 % |

  The middle quartiles fall in between.
- **MAPE breaks near zero.** In Lago et al., Germany's MAPE (83–133 %) was about 10× its sMAPE because of negative and near-zero prices — [Lago et al. 2021](https://arxiv.org/abs/2008.08004).
- **The band widens with volatility, not just with level.** SE3's quantile band widened faster in winter, "where absolute price variability is larger" — [Kjellergren & Lindqvist Sabel 2026](https://lup.lub.lu.se/student-papers/record/9244798/file/9244801.pdf).
- **The engine's own contract.** It supports negative prices (D25) and treats prices as opaque numbers (D3) — `docs/design/decisions.md`. Its current formula is `adjusted_price = price × (1 + markup / 100)` — `docs/design/motor.md` §6.4.

### Inferences
- Reasoning: under `price × (1 + m)`, a forecast of −100 DKK/MWh with m = 20 % becomes
  −120. The markup makes an uncertain negative hour look *more* attractive, the opposite of
  its purpose. A forecast of 0 gets no markup at all, while my measurement shows the cheapest
  quartile has the *largest* absolute error. The multiplicative form fails where it matters
  most.
- Reasoning: the price the caller hands the engine may be spot only, or spot plus tariffs,
  taxes and VAT; elpriser's API offers both. In Denmark the fixed parts are large, so a
  percentage of the total price and a percentage of spot differ several-fold. An additive
  markup in the same units as the price stays the same either way. A markup tied to
  spot price movements is unaffected by fixed fees, while VAT scales both price and error alike.
- Reasoning: an additive markup needs a scale. D3 says prices are opaque, so either:
  - (a) the caller sets the steps in its own price unit (it knows the currency and whether
    tariffs are included); or
  - (b) the engine scales a dimensionless step by a robust spread of the prices in the call,
    e.g. the mean absolute deviation of the known prices. That keeps D3 intact.

  (b) is my own suggestion; no source tested it.
- Reasoning: when a quantile band is supplied (elpriser.org), the band itself is an
  additive, horizon- and regime-aware uncertainty. A `confidence_upper` per price fits the
  evidence better than any fixed curve. Section 5 shows that using P90 itself as the price is
  too conservative.

### Gaps
- My scale check is three weeks of one provider in one month. A year of archived forecasts
  (the elpriser archive keeps 400 days, from 2026-10-06) would settle it.
- No published study of additive versus multiplicative risk adjustments for EV charging found.

## 5. Which decision rules the literature recommends, and whether stateless re-planning is enough

### Takeaway
The closest study to this engine is Volvo/Lund 2026, on home EV charging with multi-day SE3
forecasts. It found that ranking days by the **median** forecast, re-deciding at every plug-in
with fresh forecasts, and picking the exact hours only from published prices was near-optimal.
Adding a risk premium toward P90 *cost* money in 3 of 4 setups. Stochastic MPC beat
deterministic MPC by only about 1 % in an EV-hub study. Frequent re-planning on point forecasts
therefore gets most of the value. What it does not remove is the **optimizer's curse**: the
hours a planner picks because they are forecast cheapest come out systematically dearer than
forecast. In Danish data that bias is roughly constant from D+2 to D+9, and it is the clearest
evidence for a markup's size.

### Cited Findings
- **Volvo/Lund: Framework 1, continuous deferral** — [Kjellergren & Lindqvist Sabel 2026, §4.4.4, §5.3.3, App. E.2](https://lup.lub.lu.se/student-papers/record/9244798/file/9244801.pdf):
  - At each plug-in, the algorithm chooses a day K* among now and the next N = 3 days. Each day is scored by `r_h(λ) = (1 − λ)·P50_h + λ·P90_h` over its cheapest slots.
  - It keeps a SoC-floor feasibility set, and "the inter-day decision uses forecasts, the intra-day assignment waits for the day-ahead publication".
  - "If K* > 0 the vehicle does not charge and the algorithm re-runs the following session with fresh predictions … previous-session decisions carry no commitment"; "as the battery depletes F contracts until the algorithm is forced to charge".
  - Result: "λ = 0 is empirically near-optimal in three of four cells, with risk-averse scoring (λ → 1) costing 4–18 EUR/year relative to λ = 0". In the fourth cell (F1 × UC2), λ = 0.5 was marginally better: deferral savings 50.6 vs 49.6 EUR/year.
  - Value of multi-day forecasts: "The marginal annual saving from acting on multi-day forecasts, above and beyond within-day optimisation, falls in the range 44–56 EUR per vehicle per year" at 50 km/day and 7.4 kW.
  - Total savings against doing nothing were 103–168 EUR/year, "but the variation between configurations comes almost entirely from within-day scheduling". The gap to perfect information "stays within 3.6 % of the do-nothing cost".
- **EV charging hub with PV and battery** (Netherlands prices, 24 h horizon, 15-minute steps, re-solved at every step). Cost relative to a perfect-forecast MPC (= 100):
  - deterministic point-forecast MPC 113.65;
  - scenario-based stochastic MPC 112.76;
  - recourse MPC 112.77.

  The text: "decrease the average cost of operation by 0.9%", and "using a point-estimate prediction with no measure of uncertainty (Deterministic MPC) yields acceptable performance" — [Fernández-Zapico, Hofman & Salazar, arXiv:2504.00685v2](https://arxiv.org/html/2504.00685v2).
- **Quantile rules ignore time structure.**
  - Quantile-based battery trading strategies "do not incentivize honest probabilistic forecasting" and "ignore the intertemporal dependence structure of electricity prices". The authors instead "frame battery optimization as a stochastic program based on fully probabilistic forecasts" — [Hirsch & Ziel, arXiv:2604.19580, April 2026](https://arxiv.org/abs/2604.19580) (abstract only).
  - Marginal hourly distributions are "not sufficient to support operational decisions that depend on future trajectories"; "Ensemble forecasts provide a practical remedy", though "'large' means thousands or millions of paths" — [Maciejowska, Uniejewski & Weron, arXiv:2204.11735](https://arxiv.org/abs/2204.11735).
  - Statistical error measures "may not necessarily reflect the economic value" of forecasts (same source, abstract).
- **The optimizer's curse.** "If decision makers select the option with the highest estimate … we should expect the value of the chosen alternative to be less than its estimate", even with unbiased estimates. The authors propose Bayesian adjustment — "disciplined skepticism" — [Smith & Winkler, Management Science 52(3), 2006](https://fds.duke.edu/db/aas/stat/faculty/bob.winkler/publications/278471).
- **Measured here: the optimizer's curse in Danish forecasts.** Same 3-week elpriser archive. For each forecast day, I took the 4 hours with the lowest median forecast (a ~30 kWh charge at 7.4 kW) and recorded three values (DKK/MWh):

  | Days ahead | DK1 chosen actual − forecast | DK1 regret vs true cheapest 4 | DK1 chosen actual − P90 | DK2 chosen actual − forecast | DK2 regret |
  |---|---|---|---|---|---|
  | D+2 | +132 | 80 | −326 | +225 | 87 |
  | D+3 | +158 | 85 | −371 | +243 | 99 |
  | D+4 | +158 | 94 | −345 | +277 | 120 |
  | D+5 | +137 | 96 | −319 | +237 | 90 |
  | D+6 | +158 | 103 | −340 | +255 | 100 |
  | D+7 | +133 | 115 | −466 | +223 | 93 |
  | D+8 | +114 | 128 | −409 | +196 | 98 |
  | D+9 | +118 | 133 | −371 | +259 | 152 |

  DK2's figures include its general under-forecast in this window (bias −116 to −175, section 2). Splitting each day's error into a daily-mean part and a within-day "shape" part gave:
  - DK1: level 185–278, shape 144–195;
  - DK2: level 234–339, shape 156–196.

  So the day-level error is the larger part, and it is the part that decides "today or another day".

### Inferences
- Reasoning: a stateless engine called on every new price or forecast does what Lund's
  Framework 1 does: decide afresh, without commitment, with fresh forecasts. Lund and
  Fernández-Zapico agree that this, with point forecasts, gets most of the available value.
  A full stochastic program or scenario ensemble is not justified for D1's standard-library
  engine: it brings about 1 % and needs path forecasts no Danish source offers.
- Reasoning: re-planning alone does not protect against two failure modes:
  - The optimizer's curse makes forecast-cheap hours look about 120–160 DKK/MWh (DK1)
    cheaper than they turn out. That is roughly 0.12–0.16 DKK/kWh, about 13–16 % of the mean
    price in this window. Without a markup the engine defers too often to a forecast hour that
    will not be as cheap.
  - With hard deadlines a late surprise cannot be undone: the engine may be forced into
    expensive hours (D9). Lund's deferral had a SoC floor and no fixed departures; this
    engine's targets make the downside sharper. That argues for *some* premium, even though
    Lund found λ = 0 near-optimal.
- Reasoning: the measured bias is about flat from D+2 to D+9, while plain MAE grows about
  30 %. This supports a stepped curve with a large first step and a small rise afterwards.
  P90 as the decision price (Lund's λ = 1) overshoots by 300–470 DKK/MWh and was costly in
  Lund. So a full upper quantile is too conservative as a default. A blend in the spirit of
  Lund's λ = 0.5 is roughly consistent with the measured bias: (P90 − P50) at the chosen
  hours ran about 450–600 DKK/MWh (DK1: chosen actual − forecast minus chosen actual − P90),
  and half of that is far above the ~130 bias, so even λ = 0.5 would be above it. A λ of
  about 0.2–0.3 would match the bias. This is my arithmetic from 3 weeks, not a calibrated
  result.
- Reasoning: the "value of waiting" framing gives the same rule in plain terms. Wait for a
  forecast hour only if `known_price − forecast_price > premium(hours_ahead)`, with the premium
  in price units. This is exactly the additive stepped markup applied to ranking. Two further
  points:
  - The engine already ranks known against forecast hours, so the markup *is* the
    value-of-waiting threshold. A separate mechanism is not needed.
  - Lund's split of choosing the day from forecasts and the hours from published prices
    happens on its own in a stateless engine. When the day's prices are published, they replace
    the forecast on the next call.

### Gaps
- No study found of EV charging with hard departure deadlines *and* multi-day forecasts that
  measures the value of a risk premium. Lund had no fixed departures, and Fernández-Zapico has a
  24 h horizon only.
- The cost of the optimizer's curse for a whole charging plan (several hours across days),
  rather than 4 hours per day, is not measured.
- Smith & Winkler: only the abstract read. The Bayesian correction's form for this problem
  is not worked out.

## 6. What this means for D20, O4 and S1

### Takeaway
- D20's principle stands: no markup on published prices, a markup on forecasts, costs on raw
  prices.
- O4's *shape* should change from a percentage to an additive markup in price units (or one
  scaled by the call's own price spread). The steps should be a large first step at the
  first forecast hour and only a gentle rise afterwards.
- S1's "8–11 % MAPE" is not supported. Real DK multi-day error is 23–38 % of the mean price in
  MAE terms.
- Defaults can be bounded by the evidence. Calibrating them needs a longer forecast archive,
  which now exists (elpriser.org, from 2026-10-06).

### Cited Findings
- **D20, known prices carry no markup.** Supported: published day-ahead prices are final and published around 13:00 CET ([Lund thesis](https://lup.lub.lu.se/student-papers/record/9244798/file/9244801.pdf); [ing.dk](https://ing.dk/artikel/podcast-saadan-laver-man-detaljeret-prognose-de-kommende-dages-elpriser-265746)). elpriser.org: "Days 0-1 are published prices, not modelled" ([model card](https://huggingface.co/Elpriser/denmark-price-forecast)).
- **D20, "the further out, the more a forecast must save".** Supported in direction, but weakly after the first forecast day:
  - MAE rises about 30 % from D+2 to D+9 ([elpriser spec](https://elpriser.org/api/openapi.json));
  - error reaches a "convergence point after approximately one week" ([Steinert & Ziel](https://arxiv.org/abs/1801.10583));
  - the measured selection bias is flat from D+2 to D+9 (section 5, measured here).
- **D20, rejection of the linear 5 % + 0.2 %/h.** Supported: growth is about t^0.2–0.3, not linear; percentages misbehave near zero and below ([Ghelasi & Ziel](https://arxiv.org/abs/2406.00326); [Lago et al.](https://arxiv.org/abs/2008.08004); section 4 measurements).
- **O4, stepped curve.** Supported as a mechanism, contradicted as a percentage (section 4).
- **O4, optional per-price `confidence_upper`.** Supported as an input, since one Danish source supplies calibrated P10/P90 ([elpriser spec](https://elpriser.org/api/openapi.json)). Using it at full weight is contradicted: P90-based scoring cost 4–18 EUR/year in Lund ([Lund thesis](https://lup.lub.lu.se/student-papers/record/9244798/file/9244801.pdf)).
- **S1, "MAPE 8–11 % for Nord Pool".** Not found. The closest is the Nord Pool system-price *day-ahead* MAPE of 5.5–6.4 % for 2016–2018 ([Lago et al.](https://arxiv.org/abs/2008.08004)). That is a different price, horizon and period, and MAPE is the wrong metric here (same source).

### Inferences
- Reasoning, a proposed default for O4 that is consistent with the sources but not
  calibrated:
  - Markup 0 for published prices.
  - From the first forecast hour, an additive premium about equal to the measured
    selection bias. For DK1 spot in DKK this was ≈ 0.12–0.16 DKK/kWh in October 2026, or
    13–16 % of that month's mean price, used as an absolute amount and not as a percentage.
  - Rising by about a quarter to a third over the following week, then flat beyond 7 days.

  Expressed against MAE, the published elpriser MAE at D+2 (149 DKK/MWh DK1) is about the
  same size as the measured bias. A first step of about 1× the first-day MAE, rising to about
  1.3× at D+7, is the shape the numbers point to. Treat these as starting values for a
  calibration run, not as findings.
- Reasoning: since D3 forbids units in the engine, the default is best stated relative to the
  call's own prices (for example, a fraction of the mean absolute deviation of the known
  prices), with an override in price units for callers who know their currency. The
  integration, not the engine, should own currency-specific defaults.
- Reasoning: the calibration S1 still needs can now be run on real data:
  - Store each forecast run (the elpriser archive already does, for 400 days; Carnot's must
    be logged by the integration).
  - Then, per hours-ahead bucket, measure the realised-minus-forecast price of the hours a
    greedy planner would have picked, and set each step to that bias. Optionally add a
    term for the asymmetric cost of missing a deadline.

  This targets the planner's actual loss, as Maciejowska et al. and Hirsch & Ziel recommend
  over pure error metrics.

### Gaps
- Defaults calibrated over a full year and both seasons: not available. The elpriser archive
  starts 2026-10-06 and Carnot keeps no public archive.
- Carnot accuracy, the forecast most Danish HA users have: unknown.
- Whether the premium should depend on the deadline's slack (a looser deadline tolerates more
  risk): no source found. This touches D9 and D22.
