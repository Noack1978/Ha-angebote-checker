"""Angebote Checker – Home Assistant custom integration."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CoreState, EVENT_HOMEASSISTANT_STARTED, HomeAssistant, ServiceCall
from homeassistant.helpers.event import async_call_later

from .const import CARD_JS_FILENAME, DOMAIN, INTEGRATION_VERSION, SERVICE_REFRESH, URL_BASE
from .coordinator import AngeboteCheckerCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

# ---------------------------------------------------------------------
# Frontend-Ressource (Lovelace-Karte): vormals in einer eigenen
# frontend/__init__.py, jetzt hier zusammengeführt, damit frontend/ ein
# reines Verzeichnis (nur die JS-Datei) ohne eigenes Python-Package ist.
#
# Nutzt das bestätigte Registrierungs-Muster ("Developer Guide: Embedded
# Lovelace Card in a Home Assistant Integration", Jan/Feb 2026):
# - Zugriff NUR über das echte, laufende hass.data["lovelace"]-Objekt.
# - Bestätigter Breaking Change seit HA 2026.2 (Übergangsfrist bis 2026.8
#   ist abgelaufen): Das Attribut heißt nicht mehr "mode", sondern
#   "resource_mode" - deshalb mit Fallback auf beide Namen geprüft.
# - URL mit ?v={version}-Parameter (Cache-Busting), Version kommt aus
#   const.INTEGRATION_VERSION (liest bereits selbst aus manifest.json).
# ---------------------------------------------------------------------

_FRONTEND_DIR = Path(__file__).parent / "frontend"


def _get_lovelace_resources(hass: HomeAssistant) -> Any | None:
    """Safely retrieve the Lovelace resources collection.

    The internal structure of hass.data['lovelace'] has changed across HA
    versions. We try several known attribute paths and return None if none
    work, so the rest of the code can fall back gracefully.
    """
    lovelace = hass.data.get("lovelace")
    if lovelace is None:
        return None

    # HA 2024+ stores resources directly on the lovelace data object
    resources = getattr(lovelace, "resources", None)
    if resources is not None:
        return resources

    # Older layout: lovelace.hass_config or similar nested objects
    for attr in ("hass_config", "config", "default_config"):
        sub = getattr(lovelace, attr, None)
        if sub is not None:
            resources = getattr(sub, "resources", None)
            if resources is not None:
                return resources

    return None


def _is_storage_mode(hass: HomeAssistant) -> bool:
    """Return True when Lovelace is in storage (UI) mode."""
    lovelace = hass.data.get("lovelace")
    if lovelace is None:
        return False

    # Try the direct attribute first, then nested objects. Bestätigter
    # Breaking Change seit HA 2026.2 (Übergangsfrist bis 2026.8 ist
    # abgelaufen): das Attribut heißt nicht mehr "mode", sondern
    # "resource_mode" - deshalb mit Fallback auf beide Namen geprüft.
    for obj in [lovelace] + [
        getattr(lovelace, a, None)
        for a in ("hass_config", "config", "default_config")
    ]:
        if obj is None:
            continue
        mode = getattr(obj, "resource_mode", None) or getattr(obj, "mode", None)
        if mode is not None:
            return mode == "storage"

    # If we cannot determine the mode assume storage (most common setup)
    return True


class JSModuleRegistration:
    """Registers the Lovelace card JS as a HA frontend resource."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def async_register(self) -> None:
        """Register static HTTP path and Lovelace resource."""
        await self._async_register_static_path()

        if _is_storage_mode(self.hass):
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
                [StaticPathConfig(URL_BASE, str(_FRONTEND_DIR), cache_headers=False)]
            )
            _LOGGER.debug(
                "Angebote Checker: Statischer Pfad registriert: %s -> %s",
                URL_BASE, _FRONTEND_DIR,
            )
        except RuntimeError:
            _LOGGER.debug("Angebote Checker: Statischer Pfad bereits vorhanden: %s", URL_BASE)

    async def _async_wait_and_register(self) -> None:
        """Wait until Lovelace resources are loaded, then register."""

        async def _check(_now: Any = None) -> None:
            resources = _get_lovelace_resources(self.hass)
            if resources is None:
                _LOGGER.debug("Angebote Checker: Lovelace-Ressourcen nicht verfügbar, Retry in 5 s …")
                async_call_later(self.hass, 5, _check)
                return
            if not getattr(resources, "loaded", True):
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
        """Remove the Lovelace resource entry."""
        resources = _get_lovelace_resources(self.hass)
        if resources is None or not getattr(resources, "loaded", True):
            return
        url_path = f"{URL_BASE}/{CARD_JS_FILENAME}"
        for resource in list(resources.async_items()):
            if resource["url"].startswith(url_path):
                await resources.async_delete_item(resource["id"])
                _LOGGER.debug("Angebote Checker: Lovelace-Ressource entfernt: %s", resource["url"])


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration (called once, not per config entry).

    Frontend resource registration must happen here so that it runs
    exactly once regardless of how many config entries exist.
    """

    async def _register_frontend(_event=None) -> None:
        registrar = JSModuleRegistration(hass)
        await registrar.async_register()

    if hass.state is CoreState.running:
        await _register_frontend()
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _register_frontend)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Angebote Checker from a config entry."""
    config = {**entry.data, **entry.options}
    coordinator = AngeboteCheckerCoordinator(hass, config)

    # Initial data fetch – raises ConfigEntryNotReady on failure
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload entry when options change
    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    # Register service (only once across all entries)
    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):

        async def _handle_refresh(call: ServiceCall) -> None:
            """Refresh all coordinator instances."""
            for cfg_entry in hass.config_entries.async_entries(DOMAIN):
                coordinator: AngeboteCheckerCoordinator | None = getattr(
                    cfg_entry, "runtime_data", None
                )
                if coordinator is not None:
                    await coordinator.async_refresh_now()

        hass.services.async_register(DOMAIN, SERVICE_REFRESH, _handle_refresh)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove service only when the last entry is gone
    remaining = hass.config_entries.async_entries(DOMAIN)
    if len(remaining) <= 1 and hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH)

    return unloaded


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)
