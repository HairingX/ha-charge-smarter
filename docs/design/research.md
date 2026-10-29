# Research

What has been investigated for the design, how far each finding can be trusted, and what is
still to be researched.

**Rule for all research:** a finding needs a source that was actually read: a fetched page, a
file, a command's output. Whoever cannot reach a source, or cannot find the answer, says so and
stops; nothing is filled in from memory. Reasoning, such as an argument about an algorithm, is
marked as reasoning.

## Where the research is

| Document | What it holds |
|---|---|
| [reports/Cheapest home EV charging.md](reports/Cheapest%20home%20EV%20charging.md) | The synthesis: how to charge cheapest in Denmark, a verdict on every decision and open question, proposed new decisions, and what remains to be measured |
| [research_notes/Cheapest home EV charging/](research_notes/Cheapest%20home%20EV%20charging/) | Seven specialist notes (prices, forecasts, charging physics, the algorithm, existing software, Home Assistant, driver behaviour) and five panel papers that weigh them against each other, one of them an audit that re-checked 28 claims at their sources |
| `research_notes/Cheapest home EV charging/experiments/` | The scripts behind the measured numbers. The price data they read is public and not kept |

The report proposes; `decisions.md` records what is decided. Until a proposal is taken into
`decisions.md`, the decision there stands.

## Corrections to earlier findings

- A web search once reported hourly forecast errors of 8–11 % MAPE for Nord Pool prices. The
  figure could not be found again, and MAPE is unsuitable for prices near or below zero. Errors for
  Danish forecasts are far larger: about a quarter to a third of the mean price from the first
  forecast day in the provider's own backtest, and more in the live runs measured.
- "A greedy choice runs well inside the 10 ms budget" was reasoning. Measured in pure Python, an
  exact dynamic programme takes about 6 ms for 168 hourly slots and 22–37 ms for 672 quarter-hour
  slots, more with every term the panels want in the objective.
- The earlier review that cited an optimality gap of 2–5 % for greedy selection wrote it from
  memory. Measured on real Danish prices, a correctly implemented greedy matches the optimum at
  constant power; the gap comes from the taper, and is small in a typical week.

## Research items

| ID | Question | Status |
|---|---|---|
| S1 | Forecast error by horizon | Measured for one provider (elpriser.org) over one October; Carnot not tested. Error is additive in price units and flattens after the first forecast day. Direction of the coming days is right far more often than chance |
| S2 | What existing software does | Answered from source code: evcc, emhass, openWB, OpenEMS, EV Smart Charging, Predbat, and commercial documentation |
| S3 | What Home Assistant integrations expose | Answered. From Home Assistant 2026.11 the core Škoda integration is read-only, with no wake, refresh or charge limit; control goes through the charger |
| S4 | How far greedy falls from the optimum | Measured on DK1 prices; see the report's section on exact optimisation |

What remains to be measured, mostly from the maintainer's own Home Assistant data, is listed at
the end of the report.
