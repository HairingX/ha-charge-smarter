# ChargeSmarter

Advanced EV charging orchestration for Home Assistant.

## Status

**Early development — not yet functional.** This repository is currently a scaffold. Features listed below describe the planned scope, not what is implemented today.

## Planned features

- **Solar surplus charging** — charge from PV excess production
- **Spot price optimization** — charge during the cheapest hours (Nord Pool, Energi Data Service, Entso-e, Tibber, etc.)
- **Dynamic load balancing** — respect household mains limits and prioritize other loads (heat pump, home battery)
- **Calendar-aware scheduling** — ensure target SOC by a departure time
- **Charger-agnostic** — integrates with existing HA charger integrations (Easee, Zaptec, Wallbox, OCPP, go-e, and more) rather than replacing them

## Installation

Through HACS, as a custom repository:

1. In HACS, add `https://github.com/HairingX/ha-charge-smarter` as a custom repository of the
   type Integration.
2. Install ChargeSmarter, and restart Home Assistant.
3. Add the integration under Settings -> Devices & services.

It is a scaffold: it sets up, but does nothing yet.

To remove it, delete the integration under Settings -> Devices & services, then remove it in
HACS and restart Home Assistant.

## Development

Open the repository in a VS Code dev container, which installs what `requirements-test.txt`
pins. Home Assistant runs with the integration on port 8123 (1338 in the dev container):

```bash
scripts/develop.sh
```

The tests, the type check and the shared checks:

```bash
pyright
python -m pytest --cov=custom_components.charge_smarter --cov-fail-under=100
```

Releases are made by the Release workflow; see `CLAUDE.md`.

## License

MIT — see [LICENSE](LICENSE).
