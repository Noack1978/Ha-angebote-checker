"""Sensor platform for Angebote Checker."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_LAST_UPDATE,
    ATTR_OFFERS,
    CONF_NAME,
    DEFAULT_NAME,
    DOMAIN,
)
from .coordinator import AngeboteCheckerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AngeboteCheckerCoordinator = entry.runtime_data
    friendly_name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    async_add_entities([AngeboteCheckerSensor(coordinator, entry, friendly_name)], True)


class AngeboteCheckerSensor(CoordinatorEntity[AngeboteCheckerCoordinator], SensorEntity):
    """Sensor holding the current list of found offers as state attributes."""

    _attr_icon = "mdi:tag-search"
    _attr_force_update = True  # always push updates even if native_value unchanged

    def __init__(
        self,
        coordinator: AngeboteCheckerCoordinator,
        entry: ConfigEntry,
        friendly_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_name = friendly_name
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_offers"

    @property
    def native_value(self) -> int:
        """Return the number of offers currently found."""
        if self.coordinator.data is None:
            return 0
        return len(self.coordinator.data.get(ATTR_OFFERS, []))

    @property
    def native_unit_of_measurement(self) -> str:
        return "Angebote"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self.coordinator.data is None:
            return {}
        return {
            ATTR_OFFERS: self.coordinator.data.get(ATTR_OFFERS, []),
            ATTR_LAST_UPDATE: self.coordinator.data.get(ATTR_LAST_UPDATE, ""),
            "todo_lists": self.coordinator.data.get("todo_lists", []),
        }
