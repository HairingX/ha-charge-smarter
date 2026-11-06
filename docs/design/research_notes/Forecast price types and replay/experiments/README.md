# Forecast bias and price-type experiments

Behind `../forecast_bias_and_price_types.md`. Python 3.13 with numpy and scipy (`pip install
numpy scipy`). Each script takes a data folder as its first argument; the data is public and is
not kept here.

| File | What it does |
|---|---|
| `fetch.sh <folder> [end]` | Downloads every elpriser.org forecast run (DK1, DK2; the archive starts 2026-10-06) and Energi Data Service `DayAheadPrices` from 2026-09-01 into an empty folder |
| `common.py` | Loading: hourly prices as the mean of the four quarters (hourly billing), forecast runs, and the total price with the household grid tariff (N1 for DK1, Radius for DK2), Energinet's tariffs, elafgift and VAT, from the `DatahubPricelist` rows valid 2026-10-01 to 2027-01-01 (copied into the code) |
| `bias.py` | Level bias of the forecast median against settled prices: by days ahead, hour of day, price level, target day and run; P10/P90 coverage; Mincer-Zarnowitz fits; how well one day's error predicts the next |
| `methods.py` | Defines the ways to use a biased forecast (markup, bias correction, anchored shift and scale, shape only, rank only, persistence) and compares them: level error, ranking inside the forecast days, the charge-now-or-wait choice, and a rolling daily replanning simulation solved as a linear program |
| `robustness.py` | The replanning simulation on the first and second half of the decision days separately, with variants of the anchored shift's weights |
| `quarters.py` | How far quarter-hour prices stray from their hour's mean, and how much of that is a fixed pattern by hour and quarter |

Runs that were generated before the day-ahead auction published list the next day as a forecast
with no values (2026-10-29, 10-31 and 11-05 in both areas); the scripts skip those entries.

The `replay/` and `report_review/` folders beside these files are separate work and are not described here.
