# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ChargeSmarter is a Home Assistant custom integration for advanced EV charging orchestration. It is charger-agnostic — it coordinates with existing Home Assistant charger integrations (Easee, Zaptec, Wallbox, OCPP, go-e, etc.) rather than talking to hardware directly. Planned scope: solar surplus charging, spot price optimization, dynamic load balancing, and calendar-aware scheduling.

A companion standalone Python library will be extracted to [HairingX/charge-smarter](https://github.com/HairingX/charge-smarter) once the logic stabilizes. During initial development, library code lives nested inside this integration at `custom_components/charge_smarter/charge_smarter/`.

## Development Commands

**Run Home Assistant locally (dev container):**
```bash
scripts/develop.sh
```
HA runs on port 8123 (mapped to 1337 in devcontainer).

**Run tests:**
```bash
python -m unittest discover -v -s ./custom_components/charge_smarter/charge_smarter -p "test_*.py"
```

**Run a single test:**
```bash
python -m unittest custom_components.charge_smarter.charge_smarter.test_example.TestExample.test_method
```

**Formatting:** Black with isort (`--profile black`), configured for format-on-save in VSCode.

**CI validation:** HACS validation and hassfest run on push/PR via GitHub Actions.

## Architecture

The integration is a scaffold. Planned architecture (will evolve as features land):

```
Config Flow (charger selection + price/solar sources)
    → ChargeSmarterClient (client.py)
        → Source adapters (custom_components/charge_smarter/charge_smarter/)
            ├─ Price sources (Nord Pool, Entso-e, Tibber, ...)
            ├─ Solar / PV sources
            ├─ Charger adapters (Easee, Zaptec, OCPP, ...)
            └─ Load / mains monitoring
    → Coordinators
        └─ ChargeSmarterCoordinator — orchestration loop, charge schedule computation
    → Entities
        ├─ Sensors: current schedule, target SOC, estimated cost
        ├─ Binary Sensors: charging active, solar surplus available
        └─ Switches / Number helpers: enable/disable, override power
```

**Key files (as they are created):**
- `custom_components/charge_smarter/__init__.py` — Platform setup and entry point
- `custom_components/charge_smarter/config_flow.py` — Configuration UI (charger source, price source, solar source)
- `custom_components/charge_smarter/coordinator.py` — Orchestration loop
- `custom_components/charge_smarter/const.py` — Integration constants
- `custom_components/charge_smarter/charge_smarter/` — Pure-logic library (no HA imports) — future standalone package

## Key Patterns

- **Adapter pattern:** Charger/price/solar integrations are accessed through thin adapters, not reimplemented. The goal is to compose existing HA integrations, not replace them.
- **Library separation:** Pure logic (scheduling algorithms, optimization) lives under `custom_components/charge_smarter/charge_smarter/` and must not import from `homeassistant`. This allows extraction to a standalone PyPI package later.
- **Entity base classes:** `ChargeSmarterEntityBase` for sensors/binary sensors — extends HA's `CoordinatorEntity`.
- **Blocking HTTP in async:** Uses `async_add_executor_job()` to run synchronous HTTP calls from async HA context.
- **Localization:** `strings.json` with translations in `translations/en.json` and `translations/da.json`.

## Agent Workflow (MANDATORY)

**All code changes MUST follow the agent workflow process defined in `docs/AGENT_WORKFLOW.md`.** This process requires every task to pass through 9 stages: Project Management → Design Document → Design Review (multi-team) → Implementation → QA Review → Performance Review → Network & Data Review → HASS Compliance → Final Verification. **NO code may be written until the design document is reviewed and approved by all specialist agent teams (Stage 3).** No stage may be skipped. Read the full process document before starting any task.

## Conventions

- All documentation, comments, and commit messages must be written in English unless explicitly told otherwise
- Python 3.14, minimum Home Assistant 2026.4.0
- 4-space indentation, LF line endings
- unittest framework (not pytest) for tests; test fixtures are JSON files colocated under `charge_smarter/`
- Version tracked in `custom_components/charge_smarter/manifest.json`
