"""Tests of loading and unloading a config entry, and of the orchestration loop."""

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.charge_smarter import charge_smarter
from custom_components.charge_smarter.coordinator import ChargeSmarterCoordinator


async def test_an_entry_loads_and_unloads(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_the_startup_log_names_the_version(
    hass: HomeAssistant, config_entry: MockConfigEntry, caplog: pytest.LogCaptureFixture
) -> None:
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    assert "ChargeSmarter integration, version: 0.0.0" in caplog.text


async def test_the_loop_makes_no_decision_yet(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    config_entry.add_to_hass(hass)
    coordinator = ChargeSmarterCoordinator(hass, config_entry)
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.data == {}
    assert coordinator.update_interval is not None
    assert coordinator.update_interval.total_seconds() == 60


def test_the_charging_logic_does_not_import_home_assistant() -> None:
    """It is to become a library of its own."""
    assert charge_smarter.__name__.endswith("charge_smarter.charge_smarter")
    assert not [name for name in vars(charge_smarter) if name.startswith("homeassistant")]
