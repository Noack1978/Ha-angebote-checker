"""Config flow for Angebote Checker."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_NAME,
    CONF_RETAILERS,
    CONF_SCAN_INTERVAL,
    CONF_TODO_LISTS,
    CONF_ZIP_CODE,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    RETAILER_OPTIONS,
)


def _zip_valid(value: str) -> bool:
    return bool(re.fullmatch(r"\d{5}", value.strip()))


async def _get_todo_lists(hass) -> dict[str, str]:
    """Return {entity_id: friendly_name} for all enabled todo entities."""
    ent_reg = er.async_get(hass)
    lists: dict[str, str] = {}
    for entry in ent_reg.entities.values():
        if entry.domain == "todo" and not entry.disabled:
            state = hass.states.get(entry.entity_id)
            name = (
                state.attributes.get("friendly_name", entry.entity_id)
                if state
                else entry.entity_id
            )
            lists[entry.entity_id] = name
    return lists


def _normalize_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Normalize types that selectors may return differently (e.g. float from NumberSelector)."""
    result = dict(user_input)
    result[CONF_ZIP_CODE] = result.get(CONF_ZIP_CODE, "").strip()
    if CONF_SCAN_INTERVAL in result:
        result[CONF_SCAN_INTERVAL] = int(result[CONF_SCAN_INTERVAL])
    return result


def _build_user_schema(
    todo_options: dict[str, str],
    defaults: dict[str, Any] | None = None,
    include_name: bool = True,
) -> vol.Schema:
    d = defaults or {}
    fields: dict[vol.Marker, Any] = {}

    if include_name:
        fields[vol.Required(CONF_NAME, default=d.get(CONF_NAME, DEFAULT_NAME))] = TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        )

    fields[vol.Required(CONF_ZIP_CODE, default=d.get(CONF_ZIP_CODE, ""))] = TextSelector(
        TextSelectorConfig(type=TextSelectorType.TEXT)
    )
    fields[vol.Required(CONF_TODO_LISTS, default=d.get(CONF_TODO_LISTS, []))] = SelectSelector(
        SelectSelectorConfig(
            options=[{"value": eid, "label": name} for eid, name in todo_options.items()],
            multiple=True,
            mode=SelectSelectorMode.LIST,
        )
    )
    fields[vol.Optional(CONF_RETAILERS, default=d.get(CONF_RETAILERS, []))] = SelectSelector(
        SelectSelectorConfig(
            options=RETAILER_OPTIONS,
            multiple=True,
            mode=SelectSelectorMode.LIST,
        )
    )
    fields[
        vol.Optional(CONF_SCAN_INTERVAL, default=d.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    ] = NumberSelector(
        NumberSelectorConfig(min=5, max=1440, step=5, mode=NumberSelectorMode.BOX)
    )

    return vol.Schema(fields)


class AngeboteCheckerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        todo_options = await _get_todo_lists(self.hass)

        if not todo_options:
            return self.async_abort(reason="no_lists")

        if user_input is not None:
            data = _normalize_input(user_input)
            if not _zip_valid(data[CONF_ZIP_CODE]):
                errors[CONF_ZIP_CODE] = "invalid_zip"
            else:
                return self.async_create_entry(
                    title=data.get(CONF_NAME, DEFAULT_NAME),
                    data=data,
                )

        schema = _build_user_schema(todo_options, user_input, include_name=True)
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return AngeboteCheckerOptionsFlow()


class AngeboteCheckerOptionsFlow(OptionsFlow):
    """Handle options (reconfigure) flow.

    Note: No __init__ accepting config_entry – that pattern is broken in HA 2025.12+.
    Use self.config_entry (provided by OptionsFlow base class) instead.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        todo_options = await _get_todo_lists(self.hass)
        current = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            data = _normalize_input(user_input)
            if not _zip_valid(data[CONF_ZIP_CODE]):
                errors[CONF_ZIP_CODE] = "invalid_zip"
            else:
                return self.async_create_entry(title="", data=data)

        schema = _build_user_schema(todo_options, current, include_name=False)
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
