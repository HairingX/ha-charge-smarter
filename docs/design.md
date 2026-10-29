# Design

## What it is

ChargeSmarter decides when and how fast an electric car charges, from what other integrations
already report: the charger's state and controls, the electricity price, solar production and
the household's load. It talks to no hardware itself.

## How it is built

- A config entry with no options yet; one entry per Home Assistant.
- A `DataUpdateCoordinator` runs the orchestration loop once a minute. It makes no decision yet.
- `charge_smarter/` inside the integration holds the charging logic, which imports nothing from
  Home Assistant, so that it can be released as the library `charge-smarter` and pinned like the
  owner's other integrations pin theirs.
- Adapters translate other integrations' entities into what the logic needs, one per kind of
  charger, price or solar source.
- The charging logic is not built yet. What it must do, the decisions behind it and the research
  they rest on are in `design/`.

## How it is released

As every integration of the owner: the workflows, the release tools and the shared conventions
come from `HairingX/ha_integration_workflows`. The manifest says `0.0.0`; a release sets the
version in the zip HACS installs.
