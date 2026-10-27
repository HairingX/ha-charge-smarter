"""Tests of setting the integration up from the user interface."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import SOURCE_USER, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.charge_smarter.const import DOMAIN


async def start(hass: HomeAssistant) -> dict[str, Any]:
    """A user's flow, at its first step."""
    return dict(await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER}))


async def configure(hass: HomeAssistant, flow_id: str, user_input: dict[str, str]) -> dict[str, Any]:
    # HA declares the flow manager's user input as a bare `dict`.
    flow: Any = hass.config_entries.flow
    result: ConfigFlowResult = await flow.async_configure(flow_id, user_input)
    return dict(result)


async def test_the_user_step_shows_an_empty_form_then_creates_the_entry(hass: HomeAssistant) -> None:
    result = await start(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await configure(hass, result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "ChargeSmarter"
    assert result["data"] == {}


async def test_a_second_entry_is_refused(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    config_entry.add_to_hass(hass)
    result = await start(hass)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
