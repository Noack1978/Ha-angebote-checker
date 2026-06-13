"""DataUpdateCoordinator for Angebote Checker."""
from __future__ import annotations

import logging
import re
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


def _strip_offer_annotation(name: str) -> str:
    """Remove trailing offer annotation added by the card.

    e.g. "Butter (Lidl 0,99 €)"  →  "Butter"
         "Brötchen (Netto 2,29 €)" → "Brötchen"

    Only strips the last parenthesis block if it looks like a price annotation
    (contains a currency symbol or price pattern). This preserves parentheses
    that are part of the original item name, e.g. "Milch (3,5%)".
    """
    # Match trailing ( ... Händler Preis € ) pattern
    stripped = re.sub(r"\s*\([^()]*\d[.,]\d{2}\s*€[^()]*\)\s*$", "", name.strip())
    return stripped.strip() if stripped.strip() else name.strip()


async def _get_todo_items(hass: HomeAssistant, list_entity_id: str) -> list[str]:
    """Return summary strings of all incomplete items in a todo list."""

    # Primary: service call
    if hass.services.has_service("todo", "get_items"):
        _LOGGER.debug("AC: Lese Liste '%s' via Service", list_entity_id)
        try:
            result = await hass.services.async_call(
                "todo",
                "get_items",
                {"entity_id": list_entity_id, "status": "needs_action"},
                blocking=True,
                return_response=True,
            )
            _LOGGER.debug("AC: Service-Ergebnis für '%s': %s", list_entity_id, result)
            items = result.get(list_entity_id, {}).get("items", [])
            names = [_strip_offer_annotation(item.get("summary", "").strip()) for item in items if item.get("summary")]
            _LOGGER.info("AC: Liste '%s' → %d Artikel: %s", list_entity_id, len(names), names)
            return names
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("AC: Service fehlgeschlagen für '%s': %s", list_entity_id, err)

    # Fallback: state attributes
    _LOGGER.debug("AC: Fallback – lese Attribute von '%s'", list_entity_id)
    state = hass.states.get(list_entity_id)
    if state is None:
        _LOGGER.warning("AC: Entität '%s' nicht gefunden!", list_entity_id)
        return []

    _LOGGER.debug("AC: State von '%s': %s | Attribute-Keys: %s",
                  list_entity_id, state.state, list(state.attributes.keys()))

    items = state.attributes.get("items", state.attributes.get("todo_items", []))
    names = [
        _strip_offer_annotation(item.get("summary", item.get("name", "")).strip())
        for item in items
        if isinstance(item, dict)
        and item.get("status", "needs_action") == "needs_action"
        and (item.get("summary") or item.get("name"))
    ]
    _LOGGER.info("AC: Liste '%s' (Fallback) → %d Artikel: %s", list_entity_id, len(names), names)
    return names


class AngeboteCheckerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches Marktguru offer data for all items across the configured todo lists."""

    def __init__(self, hass: HomeAssistant, config_data: dict[str, Any]) -> None:
        self._zip_code: str = config_data[CONF_ZIP_CODE]
        self._todo_lists: list[str] = config_data.get(CONF_TODO_LISTS, [])
        self._retailers: list[str] = config_data.get(CONF_RETAILERS, [])
        interval_minutes: int = config_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        _LOGGER.info(
            "AC: Coordinator init – PLZ=%s, Listen=%s, Händler=%s, Intervall=%d min",
            self._zip_code, self._todo_lists, self._retailers, interval_minutes,
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval_minutes),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch fresh offer data."""
        _LOGGER.info("AC: Starte Aktualisierung – Listen: %s", self._todo_lists)

        all_items: list[str] = []
        for list_id in self._todo_lists:
            items = await _get_todo_items(self.hass, list_id)
            all_items.extend(items)

        seen: set[str] = set()
        unique_items = [x for x in all_items if not (x in seen or seen.add(x))]  # type: ignore[func-returns-value]

        now_iso = datetime.now(UTC).isoformat()
        _LOGGER.info("AC: Eindeutige Artikel gesamt: %d → %s", len(unique_items), unique_items)

        if not unique_items:
            _LOGGER.warning("AC: Keine Artikel in den Listen gefunden – API wird nicht abgefragt.")
            return {ATTR_OFFERS: [], ATTR_LAST_UPDATE: now_iso, "todo_lists": self._todo_lists}

        retailer_filter = self._retailers if self._retailers else None
        _LOGGER.info("AC: Händlerfilter: %s", retailer_filter)

        session = async_get_clientsession(self.hass)
        api = MarktguruAPI(session, self._zip_code)

        try:
            offers = await api.search_multiple(unique_items, retailer_filter)
        except Exception as err:
            raise UpdateFailed(f"Fehler beim Abruf der Angebote: {err}") from err

        _LOGGER.info("AC: Fertig – %d Angebote für %d Artikel gefunden.", len(offers), len(unique_items))
        return {ATTR_OFFERS: offers, ATTR_LAST_UPDATE: now_iso, "todo_lists": self._todo_lists}

    async def async_refresh_now(self) -> None:
        """Trigger an immediate data refresh."""
        await self.async_refresh()
