# Report review re-runs

Behind `../../report_review.md`. Each script takes a data folder holding `dk1.json` (Energi Data
Service `DayAheadPrices`, DK1, 2025-10-01 to 2026-11-07, columns TimeUTC, TimeDK,
DayAheadPriceDKK, DayAheadPriceEUR) and `n1_CD.json` (`DatahubPricelist` rows for GLN
5790001089030, charge type code `CD`). The data is public and not kept here.

- `n1_quarter_billing.py`: reproduces the 2026 sensitivity table of
  `price_composition_denmark.md` §5 (quarter-hour billing), once with the notes' hardcoded N1
  tariff and once with N1's DataHub rows by date.
- `n1_hourly_billing.py`: the same strategies on hourly billing (simple mean of the quarters),
  as the maintainer is billed, plus a crude test of planning at 11 kW while the car takes less.

Run with `python3 -I <script> <data folder>`.
