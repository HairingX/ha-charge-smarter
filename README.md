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

Not yet available. HACS installation instructions will be added once the integration reaches a usable state.

## Development

Open the repository in a VS Code dev container. Home Assistant runs on port 8123 (mapped to 1337 in the dev container).

```bash
scripts/develop.sh
```

Run tests:

```bash
python -m unittest discover -v -s ./custom_components/charge_smarter/charge_smarter -p "test_*.py"
```

## License

MIT — see [LICENSE](LICENSE).
