# Price analyses

The analyses behind `../../price_composition_denmark.md` (`analyse.py`, `arr.py`) and
`../../price_forecast_uncertainty.md` (`analyse2.py`, `trend.py`, `pt.py`, `sim.py`): spreads and
savings of the total Danish price, forecast error by horizon, direction hit rates, and simulated
decision rules.

Each script takes a data folder as its first argument. The folder holds `dap.json`, the
DayAheadPrices records from Energi Data Service's API, and the downloaded tariff rows or
elpriser.org forecast files the script reads; the script's `open` and `glob` calls name them.
The data itself is not kept here, as it is public and can be fetched again.

`arbitrage.py` is behind `../../panel_market_economist.md`: the value of charging beyond each
night's need with perfect foresight, and of a percentile fill rule, on a year of total prices.
