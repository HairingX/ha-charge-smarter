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

## 6. What this means for D20, O4, O1 and S1

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
- Revised after the trend test (section 7). Forecasts rank the coming days well even though
  their levels are off. So forecast hours should stay in the ranking with a *small* markup:
  about 0.3–0.6× the first-forecast-day MAE, roughly 50–100 DKK/MWh on DK spot, never above
  about one MAE. The earlier ≈1× MAE is too high.
- O1: the evidence favours charging beyond the floors only when the coming days are forecast
  dearer than now by more than the markup (a next-cheaper-day rule). It does not favour a fixed
  price threshold or a percentile. A separate trend switch is not needed.

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
  - From the first forecast hour, an additive premium. First version: about equal to the
    measured selection bias, ≈ 0.12–0.16 DKK/kWh on DK1 spot in October 2026, or 13–16 %
    of that month's mean price, used as an absolute amount and not as a percentage.
    **Revised in section 7:** the simulation tolerated 0–100 DKK/MWh and was hurt at 300, so
    start lower, at ≈ 0.05–0.10 DKK/kWh.
  - Rising by about a quarter to a third over the following week, then flat beyond 7 days.

  Expressed against MAE, the published elpriser MAE at D+2 (149 DKK/MWh DK1) is about the
  same size as the measured bias. A first step of about 0.3–0.6× the first-day MAE (revised down from 1× after section 7),
  rising to about 1.3× that value at D+7, is the shape the numbers point to. Treat these as starting values for a
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

## 7. Trend direction: does the forecast get the direction of the coming days right?

Added at the maintainer's challenge. From long use, he finds that Danish forecasts get the trend
of the next ~6 days right even when hourly levels are off, and he uses them as a rising/falling
signal. Tested on 2026-10-28/29.

### Takeaway
In the data available, the maintainer's claim holds, and it is compatible with sections 2–5:
- Levels are off by ~25–35 %, but the forecast ranks the coming days well.
- It calls the direction of a day versus the last known day right in 73–100 % (DK1) and
  59–90 % (DK2) of cases at D+2..D+7, against about 50–70 % for naive baselines.
- It picks the actual cheapest of the next 6 days 50–71 % of the time, against 17 % by chance.
- Direction is reliable only when the forecast move is large, above roughly 200–300 DKK/MWh.
  Below 100 DKK/MWh it is a coin flip.

In a simple simulation with a 50 kWh battery, acting on the forecast's *day ranking*
recovered 91–97 % of perfect-foresight savings (80–88 % with 30 kWh). A binary
"trend up → fill now" switch recovered 73–80 % (62–71 % with 30 kWh).

**The sample is tiny**:
- 23 forecast runs (issued 2026-10-06 to 2026-10-28) and 22–24 actual days;
- overlapping runs;
- one autumn month dominated by two windy low-price episodes (DK1 daily means 370 on 10-10
  and 79 on 10-25, against 1,000–1,500 on most days).

It supports the direction of the claim; it does not calibrate any threshold.

### Cited Findings
- **Data and method (measured here).**
  - Forecasts: the elpriser.org archive, 23 runs per area ([API spec](https://elpriser.org/api/openapi.json); `https://elpriser.org/api/forecast/archive?area=DK1&issued=…`).
  - Each run is generated around 12:13 UTC, after the day-ahead auction, so the issue day D and D+1 are published. The forecasts cover D+2..D+9.
  - Actuals: Energi Data Service `DayAheadPrices`, refetched 2026-10-29 to include prices through 2026-10-29, as daily means of the quarter-hours.
- **My own captured forecasts:** none exist; nothing was logged before this task. **Carnot:** could not get; the API needs a personal key (see section 1). So only one provider is tested.
- **Day-by-day volatility in the sample** (measured here). Mean |day-to-day change| of the daily mean was 344 DKK/MWh (DK1) and 329 (DK2). The daily means for DK1, 6–29 Oct:

  | | | | | | | | |
  |---|---|---|---|---|---|---|---|
  | 06: 1504 | 07: 1442 | 08: 985 | 09: 630 | 10: 370 | 11: 950 | 12: 1470 | 13: 1047 |
  | 14: 1209 | 15: 1228 | 16: 1566 | 17: 1144 | 18: 1212 | 19: 1550 | 20: 1340 | 21: 1482 |
  | 22: 1106 | 23: 1013 | 24: 253 | 25: 79 | 26: 682 | 27: 690 | 28: 1558 | 29: 2224 |

  DK2 follows closely.

#### 7.1 Direction hit rate, each day versus the last known day (D+1)

"Hit" means sign(forecast mean D+k − actual mean D+1) equals sign(actual D+k − actual D+1).
The baseline "weekday last week" uses actual(D+k−7) as the forecast. The Pesaran-Timmermann
(PT) statistic tests against independent signs; a value above 1.645 rejects independence at the
5 % level, one-sided, *if* the observations were independent, which overlapping runs are not.
Measured here.

| Horizon | n | DK1 forecast | DK1 last week | DK1 PT | DK2 forecast | DK2 last week | DK2 PT | Share of actual rises (DK1) |
|---|---|---|---|---|---|---|---|---|
| D+2 | 22 | 73 % | 50 % | 2.24 | 59 % | 50 % | 1.11 | 55 % |
| D+3 | 21 | 81 % | 62 % | 3.17 | 71 % | 62 % | 2.57 | 52 % |
| D+4 | 20 | 100 % | 65 % | 4.59 | 90 % | 70 % | 3.72 | 45 % |
| D+5 | 19 | 74 % | 63 % | 2.11 | 74 % | 68 % | 2.27 | 58 % |
| D+6 | 18 | 89 % | 56 % | 3.49 | 67 % | 56 % | 2.16 | 56 % |
| D+7 | 17 | 82 % | 65 % | 2.96 | 76 % | 65 % | 2.59 | 53 % |
| Mean of D+2..D+7 vs D+1 | 17 | 82 % | 59 % | 2.82 | 76 % | 59 % | 2.35 | — |

#### 7.2 Direction against the issue day D ("relative to today")

Same method, with D as the reference (measured here).
- The forecast hit rate at D+2..D+9 was:
  - DK1: 100, 100, 80, 74, 83, 82, 81, 67 %;
  - DK2: 82, 86, 85, 68, 67, 71, 75, 67 %.
- D+1 is published, so it is always right.
- Baselines:
  - **Momentum** (the known change D→D+1 continues): 82, 76, 70, 58, 61, 47, 56, 40 % (DK1). It decays to coin-flip by D+5.
  - **Weekday last week**: 47–67 %.
- The mean over D+1..D+6 versus D: forecast 83 % (DK1) and 78 % (DK2), weekday last week 61 %.
- Pure persistence ("tomorrow = today") predicts no change, so it has no direction and gives no
  baseline. Momentum stands in for it.

#### 7.3 Hit rate by the size of the forecast move

All runs and horizons D+2..D+9 pooled, against D+1, in DKK/MWh (measured here):

| Forecast move | DK1 hit rate | DK2 hit rate |
|---|---|---|
| < 100 | 52 % (n=25) | 45 % (n=22) |
| 100–200 | 67 % (n=21) | 36 % (n=14) |
| 200–300 | 89 % (n=19) | 59 % (n=17) |
| ≥ 300 | 93 % (n=83) | 87 % (n=95) |

Against D the pattern is the same (DK1 67 / 70 / 79 / 95 %; DK2 47 / 42 / 69 / 86 %).

#### 7.4 Ranking and the cheapest day over the next 6 days (measured here)

| | DK1, D+1..D+6 (D+1 known) | DK1, D+2..D+7 | DK2, D+1..D+6 | DK2, D+2..D+7 |
|---|---|---|---|---|
| Runs | 18 | 17 | 18 | 17 |
| Spearman, forecast vs actual daily means (mean / median) | 0.79 / 0.80 | 0.79 / 0.83 | 0.70 / 0.74 | 0.72 / 0.77 |
| Spearman, weekday-last-week baseline | −0.03 | 0.00 | 0.02 | 0.06 |
| Forecast picks the actual cheapest day | 67 % | 71 % | 50 % | 65 % |
| Weekday last week picks it | 17 % | 18 % | 17 % | 18 % |
| Picked day within 50 / 100 / 200 DKK/MWh of the cheapest | 67 / 83 / 94 % | 76 / 88 / 94 % | 61 / 67 / 83 % | 76 / 82 / 88 % |
| Mean regret of the forecast pick (median) | 68 (0) | 58 (0) | 110 (0) | 82 (0) |
| Mean regret of the weekday-last-week pick | 566 | 536 | 570 | 541 |

Chance of picking the cheapest at random is 17 %.

#### 7.5 Literature on directional accuracy
- The elpriser.org v3 backtest reports a "Min-hour hit-rate (cheapest hour in predicted top-3)" of 69.0 % (DK1) and 70.0 % (DK2) — [model card](https://huggingface.co/Elpriser/denmark-price-forecast). This is the only published Danish ranking-type accuracy found.
- The Volvo/Lund SE3 study: "the broader price pattern remains clear over the first two to four days". Ranking days by the median forecast (λ = 0) was near-optimal in 3 of 4 setups — [Kjellergren & Lindqvist Sabel 2026](https://lup.lub.lu.se/student-papers/record/9244798/file/9244801.pdf).
- **Kath & Ziel (German quarter-hourly markets).** They use Directional Accuracy (share of correct up/down calls) and the Pesaran-Timmermann test: "the tests suggest a promising rate of correctness but do not allow us to reject the null hypothesis of autonomous directional errors". They note that a hit rate above 50 % yields economic benefit only "if the losses of an incorrect prediction and the gains of a correct one are equally distributed". Directional accuracy declined in peak quarter-hours — [Kath & Ziel, arXiv:1811.08604](https://arxiv.org/abs/1811.08604) (PDF read). Their directions are between two intraday markets, not across days.
- **Australian NEM, 24 h and 48 h horizons.** They report mean directional accuracy (MDA, step-to-step sign of change). Examples in QLD: CNN-LSTM 66.2 % (24 h) and 65.6 % (48 h); DLinear 54.6 % and 54.0 %. "directional accuracy deteriorates sharply during abrupt shifts in price direction" — [Gani et al., arXiv:2602.01157](https://arxiv.org/abs/2602.01157) (PDF read). This is intraday step direction, not day-level trend.
- **Not found:** a published study of *day-level* direction accuracy at 2–7 days for Nordic or any European day-ahead prices. None of the EPF papers read for sections 2–3 (Lago et al., Ghelasi & Ziel, Steinert & Ziel, Maciejowska et al.) reports directional accuracy (searched their text for "direction", "sign of", "turning point").

#### 7.6 Simulation of decision rules (measured here)

**Model.**
- Daily inventory: one car using 10 kWh per day, one charging opportunity per calendar day.
- Each opportunity is priced at the actual mean of that day's 2 cheapest hours (spot,
  DKK/MWh).
- Each day, after the auction, the decision sets how much to charge at tomorrow's (published)
  opportunity, from the forecasts for the 6 days after it.
- Battery: at least one day's energy after charging; capacity 50 kWh (5 days), or 30 kWh in a
  second run.
- 23 decisions, issued 2026-10-06 to 2026-10-28. The energy left at the end is valued at the
  period's mean opportunity price.

**Rules.**
- **Floor:** charge each day's need. This is within-day optimisation only.
- **Oracle:** perfect foresight. Charge enough to last until the next *actually* cheaper day.
- **Forecast next-cheaper + premium P:** the same rule, judged on forecast cheapest-hour
  prices plus an additive P for forecast days.
- **Trend switch:** if the forecast mean of D+2..D+6 exceeds the known D+1 mean by more than T,
  fill to capacity (or to 3 days' worth); otherwise charge the floor.

Average price paid, DKK/MWh, and the share of the oracle's saving over the floor:

| Rule | DK1, 50 kWh | DK2, 50 kWh | DK1, 30 kWh | DK2, 30 kWh |
|---|---|---|---|---|
| Floor (charge each day's need) | 718 | 730 | 718 | 730 |
| Oracle next-cheaper (actual prices) | 358 (100 %) | 372 (100 %) | 466 (100 %) | 475 (100 %) |
| Forecast next-cheaper, P = 0 | 372 (96 %) | 403 (91 %) | 499 (87 %) | 527 (80 %) |
| P = 50 | 369 (97 %) | 403 (91 %) | 496 (88 %) | 527 (80 %) |
| P = 100 | 386 (92 %) | 384 (97 %) | 505 (85 %) | 508 (87 %) |
| P = 150 / 200 | 386 (92 %) | 423 (86 %) | 505 (85 %) | 527 / 545 (80 / 73 %) |
| P = 300 | 462 (71 %) | 437 (82 %) | 565 (61 %) | 541 (74 %) |
| Trend switch, T = 0 → fill | 434 (79 %) | 444 (80 %) | 555 (65 %) | 550 (71 %) |
| Trend switch, T = 100–200 → fill | 456 (73 %) | 444–464 (74–80 %) | 550 (67 %) | 550–573 (62–71 %) |
| Trend switch, T = 100–200 → 3 days' worth | 550 (47 %) | 550–573 (44–50 %) | 550 (67 %) | 550–573 (62–71 %) |

### Inferences
- Reasoning: both views fit the same data.
  - The level of a single forecast day is off by about 230–400 DKK/MWh MAE (section 2).
  - In this window, though, days differed from one another by about 340 DKK/MWh on average.
  - Section 5 showed the day-level part of the error was the larger part of each day's error;
    even so, the *order* of days survives whenever the true differences between them are
    larger than that error. That is why direction and ranking are good while levels are not,
    and why direction is a coin flip for moves under ~100 DKK/MWh.
  - In a calm period with small daily differences, direction hit rates would be lower. This
    window cannot show it. Reasoning, not measured.
- Reasoning: the threshold below which direction is noise lies between 100 and 300 DKK/MWh
  in this sample (about 0.1–0.3 DKK/kWh on spot). It is of the same order as one forecast-day
  MAE. A rule of thumb follows: "trust a predicted move larger than about one MAE of that
  horizon." A dimensionless form keeps D3: a move larger than the provider's backtest MAE at
  that horizon, or larger than the spread of the call's known prices.
- Reasoning: the simulation says the useful content of the forecast is its **day ranking**,
  used through the engine's ordinary cheapest-first choice (D22). A separate trend switch is
  not needed:
  - "Wait for the next cheaper day, else charge now" on forecast prices beat the binary
    trend switch in all four cases. With P = 0 the margin was 9–21 points of oracle savings.
  - The trend switch is too coarse. It fills fully even when a cheaper day lies two days
    ahead, and it ignores dips inside a "rising" week.
  - Ranking by the forecast is what the engine already does when forecast hours are in its
    price list. The maintainer's signal is therefore best used by keeping forecasts in the
    ranking, with a small markup, rather than by a separate trend rule.
- Reasoning on the premium:
  - In the simulation, P between 0 and about 100–150 DKK/MWh moved results by only 5–11 points
    of oracle savings, best at 0–50 for DK1 and at 100 for DK2. That is noise-level for 23
    decisions.
  - P = 300 clearly cost money: 13–27 points below the best premium.
  - This agrees with Lund (λ = 0 near-optimal; a full P90 premium costs) and with the
    selection bias of about 120–160 DKK/MWh measured in section 5.
  - The earlier suggestion of a first step of about one first-day MAE (≈150 DKK/MWh) is at the
    upper edge of what this simulation tolerates. A first step of about half that is safer:
    roughly 50–100 DKK/MWh, i.e. ≈0.05–0.10 DKK/kWh on DK spot, or about 0.3–0.6× the
    first-forecast-day MAE.
  - 23 decisions cannot separate 50 from 150. Never above about one MAE.
- Reasoning on the maintainer's rule ("charge only the floor when falling by more than T;
  charge up when rising by more than T"):
  - Its *direction* is right; the simulated trend switch saved 62–80 % of the oracle saving
    against the floor, across both battery sizes.
  - It is dominated by the ranking rule.
  - If the integration wants it, it should apply only above a move of roughly 200–300 DKK/MWh,
    where direction hit rates were 79–95 % (DK1) and 59–87 % (DK2).
  - It should charge up only to cover the days until the forecast cheaper day, not to full.
- Reasoning for O1 (charge beyond the required floors when hours are cheap): the data favours
  a variant over a fixed price threshold or a percentile:
  - Charge beyond the floors only for days whose forecast price, plus the markup, is higher
    than the known price now. That is, buy now what the coming days would otherwise buy
    dearer, up to `default_target_soc`.
  - This is the "forecast next-cheaper" rule. It recovered 80–97 % of perfect-foresight savings
    in the simulation.
  - It needs an assumed daily consumption beyond the known targets, which the engine does not
    have. Today `min_idle_soc` and the targets carry that. So it is an argument to revisit O1
    option (a), not a settled answer.

### Gaps
- Sample: 23 runs and 22–24 actual days in one month, with two dominant low-price episodes and
  overlapping runs. The PT statistics assume independence they do not have. The threshold and
  premium figures are indications only. A year of the elpriser archive (kept from 2026-10-06,
  for 400 days) or of logged Carnot forecasts is needed.
- Carnot, the forecast most Danish HA users have: not tested (no key). The maintainer's
  experience may be with Carnot; whether it ranks days as well is unknown.
- No calm-period data: how direction accuracy behaves when day-to-day moves are small (summer
  plateaus, low wind variance) is not measured.
- The simulation ignores the car's real schedule (targets, absences, D8 buffer) and uses the
  2 cheapest hours as the day's price. The engine's own greedy plan over hours was not
  simulated.
- No published day-level directional accuracy for multi-day European price forecasts was found.
