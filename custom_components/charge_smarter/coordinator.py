"""Data update coordinator for ChargeSmarter."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ChargeSmarterCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator that drives the charging orchestration loop."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict:
        """Compute the current charging decision. Placeholder."""
        return {}
