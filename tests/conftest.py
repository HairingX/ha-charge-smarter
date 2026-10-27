"""Home Assistant with this integration loadable, and a check that it uses nothing deprecated."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.charge_smarter.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> Iterator[None]:
    """Let Home Assistant load the integration from custom_components/."""
    yield


@pytest.fixture(autouse=True)
def no_deprecated_usage(caplog: pytest.LogCaptureFixture) -> Iterator[None]:
    """Fail a test in which Home Assistant reports this integration using something deprecated."""
    yield
    reports = [
        record.getMessage()
        for phase in ("setup", "call")
        for record in caplog.get_records(phase)
        if "Detected that custom integration 'charge_smarter'" in record.getMessage()
        or " was used from charge_smarter" in record.getMessage()
    ]
    assert reports == []


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """A config entry for the integration, not yet added to Home Assistant."""
    return MockConfigEntry(domain=DOMAIN, title="ChargeSmarter", data={})
