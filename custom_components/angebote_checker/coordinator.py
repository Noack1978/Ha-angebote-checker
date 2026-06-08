"""DataUpdateCoordinator for Angebote Checker."""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MarktguruAPI
from .const import (
    ATTR_LAST_UPDATE,
    ATTR_OFFERS,
    CONF_RETAILERS,
    CONF_SCAN_INTERVAL,
    CONF_TODO_LISTS,
    CONF_ZIP_CODE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def _get_todo_items(hass: HomeAssistant, list_entity_id: str) -> list[str]:
    """Return the summary strings of all incomplete items in a todo list."""
    try:
        result = await hass.services.async_call(
            "todo",
            "get_items",
            {"entity_id": list_entity_id, "status": "needs_action"},
            blocking=True,
            return_response=True,
        )
        items = result.get(list_entity_id, {}).get("items", [])
        return [item.get("summary", "").strip() for item in items if item.get("summary")]
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Einkaufsliste '%s' konnte nicht gelesen werden: %s", list_entity_id, err)
        return []


class AngeboteCheckerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches Marktguru offer data for all items across the configured todo lists."""

    def __init__(self, hass: HomeAssistant, config_data: dict[str, Any]) -> None:
        self._zip_code: str = config_data[CONF_ZIP_CODE]
        self._todo_lists: list[str] = config_data.get(CONF_TODO_LISTS, [])
        self._retailers: list[str] = config_data.get(CONF_RETAILERS, [])
        interval_minutes: int = config_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval_minutes),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch fresh offer data. Called automatically by the coordinator."""
        session = async_get_clientsession(self.hass)
        api = MarktguruAPI(session, self._zip_code)

        # Collect all item names from every configured todo list
        all_items: list[str] = []
        for list_id in self._todo_lists:
            all_items.extend(await _get_todo_items(self.hass, list_id))

        # Deduplicate while preserving insertion order
        seen: set[str] = set()
        unique_items = [x for x in all_items if not (x in seen or seen.add(x))]  # type: ignore[func-returns-value]

        now_iso = datetime.now(UTC).isoformat()

        if not unique_items:
            return {ATTR_OFFERS: [], ATTR_LAST_UPDATE: now_iso}

        retailer_filter = self._retailers if self._retailers else None

        try:
            offers = await api.search_multiple(unique_items, retailer_filter)
        except Exception as err:
            raise UpdateFailed(f"Fehler beim Abruf der Angebote: {err}") from err

        return {ATTR_OFFERS: offers, ATTR_LAST_UPDATE: now_iso}

    async def async_refresh_now(self) -> None:
        """Trigger an immediate data refresh."""
        await self.async_refresh()
