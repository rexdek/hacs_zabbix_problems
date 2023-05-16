"""Support for Zabbix sensors."""
from __future__ import annotations

from collections.abc import Callable
import datetime
import logging
import re
from typing import Dict, List

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EVENT, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the config entry for zabbix sensor."""
    zapi_events = await hass.async_add_executor_job(
        ZabbixEvents, hass.data[DOMAIN][entry.entry_id]
    )
    _LOGGER.debug("Instantiating DataUpdateCoordinator")
    coordinator = ZabbixUpdateCoordinator(
        hass,
        _LOGGER,
        zapi_events,
        name="Zabbix Data Coordinator",
        update_interval=datetime.timedelta(seconds=3),
    )
    await coordinator.async_config_entry_first_refresh()
    for sensor in entry.data["sensors"]:
        tags = re.split(" *, *", sensor[CONF_EVENT])
        sensor["tags"] = tags
        async_add_entities(
            [ZabbixProblemSensorEntity(coordinator, sensor[CONF_NAME], tags)]
        )


class ZabbixProblemSensorEntity(CoordinatorEntity, SensorEntity):
    """Zabbix Problem Sensor."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:alpha-z-box"
    _attr_name = None

    def __init__(self, coordinator, name, tags):
        super().__init__(coordinator)
        self._name = name
        self._tags = set(tags)
        self._attr_unique_id = f"{tags}"
        self._attr_native_value = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "ZABBIX")}, name=coordinator.name
        )
        _LOGGER.debug(f"Created Zabbix sensor entity {self._tags}")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug(f"Updating entity {self._name} state")
        self._attr_extra_state_attributes = {"monitor": self._tags}
        states = []
        problem_tags = set(self.coordinator.data.keys())
        for tag in self._tags.intersection(problem_tags):
            tagvalues = [f"{e.host} ({e.severity})" for e in self.coordinator.data[tag]]
            states += [int(e.severity) for e in self.coordinator.data[tag]]
            self._attr_extra_state_attributes.update({tag: tagvalues})
        self._attr_native_value = max(states) if states else 0
        self.async_write_ha_state()

    @property
    def name(self):
        return self._name


class ZabbixUpdateCoordinator(DataUpdateCoordinator):
    """Zabbix DataUpdateCoordinator used to retrieve data for all sensors at once."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        zapi_events,
        name: str = None,
        update_interval: datetime.timedelta = 30,
    ):
        super().__init__(hass, logger, name=name, update_interval=update_interval)
        self._zapi_events = zapi_events

    async def _async_update_data(self):
        return await self.hass.async_add_executor_job(self._zapi_events.get)


class ZabbixEvent:
    def __init__(self, eid: int, host: str, name: str, severity: str, tags: list):
        self.eid = eid
        self.host = host
        self.name = name
        self.severity = severity
        self.tags = [f'{t["tag"]}:{t["value"]}' for t in tags]

    def __repr__(self):
        return f"{__class__}: {self.host}, {self.severity}"

    def __str__(self):
        return f"<{self.host}, {self.severity}>"


class ZabbixEvents:
    def __init__(self, zapi):
        self.zapi: Callable = zapi
        self._events: List
        self._tags: Dict

    def get(self):
        self._events = []
        problems = self.zapi.problem.get()
        for problem in problems:
            event = self.zapi.event.get(
                eventids=problem["eventid"], selectHosts=["name"], selectTags="extend"
            )[0]
            self._events.append(
                ZabbixEvent(
                    eid=problem["eventid"],
                    host=event["hosts"][0]["name"],
                    name=event["name"],
                    severity=event["severity"],
                    tags=event["tags"],
                )
            )
        self._tags = {}
        for event in self._events:
            for tag in event.tags:
                if tag not in self._tags:
                    self._tags[tag] = []
                self._tags[tag].append(event)
        _LOGGER.debug(f"Retrieved updated data from host {self.zapi.url}")
        return self._tags
