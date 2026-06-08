"""Angebote Checker – Home Assistant custom integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CoreState, EVENT_HOMEASSISTANT_STARTED, HomeAssistant, ServiceCall

from .const import DOMAIN, SERVICE_REFRESH
from .coordinator import AngeboteCheckerCoordinator
from .frontend import JSModuleRegistration

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


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
