"""The zabbix_problems integration."""
from __future__ import annotations

import logging

from pyzabbix import ZabbixAPI

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


def zapi_login(host, user, password, ssl):
    protocol = "https" if ssl else "http"
    return ZabbixAPI(f"{protocol}://{host}", user=user, password=password)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = await hass.async_add_executor_job(
        zapi_login,
        entry.data["api"][CONF_HOST],
        entry.data["api"][CONF_USERNAME],
        entry.data["api"][CONF_PASSWORD],
        entry.data["api"][CONF_SSL],
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
