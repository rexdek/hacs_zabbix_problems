"""Config flow for zabbix_problems integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_EVENT,
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from . import zapi_login
from .const import DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="zabbix"): str,
        vol.Required(CONF_USERNAME, default="Admin"): str,
        vol.Required(CONF_PASSWORD, default="zabbix"): str,
        vol.Required(CONF_SSL, default=True): bool,
    }
)

STEP_SENSOR_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default="network"): str,
        vol.Required(CONF_EVENT, default="component:network"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.
    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    if not await hass.async_add_executor_job(
        zapi_login,
        data[CONF_HOST],
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
        data[CONF_SSL],
    ):
        raise InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": DEFAULT_NAME}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for zabbix_problems."""

    VERSION = 1

    def __init__(self):
        super().__init__()
        self.data = {"sensors": []}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self.data.update(await validate_input(self.hass, user_input))
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                self.data["api"] = user_input
                return await self.async_step_sensor()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.data["sensors"].append(user_input)
            return self.async_show_menu(
                step_id="sensor",
                menu_options={"sensor": "Add Sensor", "exit_setup": "Exit Setup"},
            )

        return self.async_show_form(
            step_id="sensor", data_schema=STEP_SENSOR_DATA_SCHEMA, errors=errors
        )

    async def async_step_exit_setup(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        return self.async_create_entry(title=self.data["title"], data=self.data)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
