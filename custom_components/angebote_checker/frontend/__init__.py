"""JavaScript module registration for Angebote Checker."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

from ..const import CARD_JS_FILENAME, INTEGRATION_VERSION, URL_BASE

_LOGGER = logging.getLogger(__name__)

_FRONTEND_DIR = Path(__file__).parent


class JSModuleRegistration:
    """Registers the Lovelace card JS as a HA frontend resource."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._lovelace = hass.data.get("lovelace")

    async def async_register(self) -> None:
        """Register static HTTP path and, if in storage mode, the Lovelace resource."""
        await self._async_register_static_path()
        if self._lovelace and self._lovelace.mode == "storage":
            await self._async_wait_and_register()
        else:
            _LOGGER.info(
                "Angebote Checker: Lovelace ist im YAML-Modus – "
                "Ressource muss manuell eingetragen werden: %s?v=%s",
                f"{URL_BASE}/{CARD_JS_FILENAME}",
                INTEGRATION_VERSION,
            )

    async def _async_register_static_path(self) -> None:
        """Serve the frontend directory under URL_BASE."""
        try:
            await self.hass.http.async_register_static_paths(
                [StaticPathConfig(URL_BASE, _FRONTEND_DIR, cache_headers=False)]
            )
            _LOGGER.debug("Angebote Checker: Statischer Pfad registriert: %s -> %s", URL_BASE, _FRONTEND_DIR)
        except RuntimeError:
            # Path already registered on a previous setup (e.g. reload)
            _LOGGER.debug("Angebote Checker: Statischer Pfad bereits vorhanden: %s", URL_BASE)

    async def _async_wait_and_register(self) -> None:
        """Wait until Lovelace resources are loaded before registering."""

        async def _check(_now: Any = None) -> None:
            resources = self._lovelace.resources
            if not resources.loaded:
                _LOGGER.debug("Angebote Checker: Lovelace-Ressourcen noch nicht geladen, Retry in 5 s …")
                async_call_later(self.hass, 5, _check)
                return
            await self._async_register_module(resources)

        await _check()

    async def _async_register_module(self, resources: Any) -> None:
        """Add or update the card JS entry in Lovelace resources."""
        url_path = f"{URL_BASE}/{CARD_JS_FILENAME}"
        versioned_url = f"{url_path}?v={INTEGRATION_VERSION}"

        existing = [r for r in resources.async_items() if r["url"].startswith(url_path)]

        if existing:
            resource = existing[0]
            if resource["url"] != versioned_url:
                _LOGGER.info("Angebote Checker: Ressource wird aktualisiert auf v%s", INTEGRATION_VERSION)
                await resources.async_update_item(
                    resource["id"],
                    {"res_type": "module", "url": versioned_url},
                )
            else:
                _LOGGER.debug("Angebote Checker: Ressource ist aktuell (v%s)", INTEGRATION_VERSION)
        else:
            _LOGGER.info("Angebote Checker: Registriere Lovelace-Ressource: %s", versioned_url)
            await resources.async_create_item({"res_type": "module", "url": versioned_url})

    async def async_unregister(self) -> None:
        """Remove the Lovelace resource entry (called on unload)."""
        if not (self._lovelace and self._lovelace.mode == "storage"):
            return
        resources = self._lovelace.resources
        if not resources.loaded:
            return
        url_path = f"{URL_BASE}/{CARD_JS_FILENAME}"
        for resource in list(resources.async_items()):
            if resource["url"].startswith(url_path):
                await resources.async_delete_item(resource["id"])
                _LOGGER.debug("Angebote Checker: Lovelace-Ressource entfernt: %s", resource["url"])
