# Optimisation panel experiments

The experiments behind `../../panel_optimisation_engineer.md`. They reuse `../scheduling/model.py`
(copy it here before running) and add `fulldp.py`, a standard-library DP over (slot, SoC grid,
on-state) with backtracking. `prices.py` builds the DK1 Danish total price from Energi Data
Service `DayAheadPrices` (path in `DK1_JSON`); `e5.py` also reads the elpriser.org forecast archive
files `arch_DK1_*.json` (folder in `ARCH_DIR`). Run with Python 3.13 or later from this folder:

- `e1.py` / `e1b.py`: corrected greedy against the exact DP; spot against total price, hourly against 15 minutes.
- `e2.py`: `fulldp` checked against the exact DP, and timed with every objective term on.
- `e3.py`: what coarser grids, hourly-then-quarter refinement and mixed resolution cost.
- `e4.py`: plan churn under re-planning every 15 minutes, with and without a start cost.
- `e5.py [kWh per day]`: charging beyond the floors (O1), daily re-planning with real forecasts.
