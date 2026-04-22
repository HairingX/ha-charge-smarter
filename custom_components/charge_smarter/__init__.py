"""ChargeSmarter integration for Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN, STARTUP

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = []


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ChargeSmarter from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    integration = await async_get_integration(hass, DOMAIN)
    _LOGGER.info(STARTUP, integration.version)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
