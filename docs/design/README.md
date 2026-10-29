# Charging design

What the charging logic must do, and what the decisions about it rest on. Nothing here is
implemented yet; this folder is the basis for designing and building it.

| Document | What it holds |
|---|---|
| [motor.md](motor.md) | The planning engine as currently decided: principles, layers, contract, algorithm |
| [decisions.md](decisions.md) | Every decision taken, with its reason, and the questions still open |
| [feature-candidates.md](feature-candidates.md) | Features considered, with their status: accepted, deferred, rejected or adapter-side |
| [research.md](research.md) | What has been investigated, how far each finding can be trusted, and what remains to research |
| [reports/](reports/) | Research reports: findings, a verdict on each decision, and proposed changes |
| [research_notes/](research_notes/) | The notes, panel papers and experiments behind each report |
| [sources/](sources/) | The earlier working documents and the first prototype, kept as reference |

## Which document wins

`decisions.md` is the record. `motor.md` follows it. A report proposes changes; they count once
they are taken into `decisions.md`. Where an earlier document in `sources/`
disagrees with either, the earlier document is out of date; it is kept for the detail it holds
(edge cases, the feature catalogue, the prototype's window search), not for its decisions.

## Working names

Names in the contract are working names. A naming pass is due before the contract is built;
see open question O3 in `decisions.md`.
