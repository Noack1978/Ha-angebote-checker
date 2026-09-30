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
    COUNTRY_OPTIONS,
    CONF_COUNTRY,
    CONF_NAME,
    CONF_RETAILERS,
    CONF_SCAN_INTERVAL,
    CONF_TODO_LISTS,
    CONF_ZIP_CODE,
    DEFAULT_COUNTRY,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    get_country,
)


def _zip_valid(value: str, country: str = DEFAULT_COUNTRY) -> bool:
    """Validate the postal code against the country's pattern (DE: 5, AT: 4 digits)."""
    pattern = get_country(country)["zip_pattern"]
    return bool(re.fullmatch(pattern, value.strip()))


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


def _build_country_schema(
    defaults: dict[str, Any] | None = None,
    include_name: bool = True,
) -> vol.Schema:
    """Step 1: instance name (initial setup only) and country."""
    d = defaults or {}
    fields: dict[vol.Marker, Any] = {}

    if include_name:
        fields[vol.Required(CONF_NAME, default=d.get(CONF_NAME, DEFAULT_NAME))] = TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        )

    fields[vol.Required(CONF_COUNTRY, default=d.get(CONF_COUNTRY, DEFAULT_COUNTRY))] = SelectSelector(
        SelectSelectorConfig(
            options=COUNTRY_OPTIONS,
            multiple=False,
            mode=SelectSelectorMode.DROPDOWN,
        )
    )
    return vol.Schema(fields)


def _build_details_schema(
    country: str,
    todo_options: dict[str, str],
    defaults: dict[str, Any] | None = None,
) -> vol.Schema:
    """Step 2: zip code, todo lists, retailers (country-specific) and interval."""
    d = defaults or {}
    retailer_options: list[str] = get_country(country)["retailers"]
    # Händler eines anderen Landes aus den Vorgaben entfernen
    retailer_default = [r for r in d.get(CONF_RETAILERS, []) if r in retailer_options]
    # PLZ-Vorgabe nur übernehmen, wenn sie zum Land passt
    zip_default = d.get(CONF_ZIP_CODE, "")
    if zip_default and not _zip_valid(zip_default, country):
        zip_default = ""

    fields: dict[vol.Marker, Any] = {}
    fields[vol.Required(CONF_ZIP_CODE, default=zip_default)] = TextSelector(
        TextSelectorConfig(type=TextSelectorType.TEXT)
    )
    fields[vol.Required(CONF_TODO_LISTS, default=d.get(CONF_TODO_LISTS, []))] = SelectSelector(
        SelectSelectorConfig(
            options=[{"value": eid, "label": name} for eid, name in todo_options.items()],
            multiple=True,
            mode=SelectSelectorMode.LIST,
        )
    )
    fields[vol.Optional(CONF_RETAILERS, default=retailer_default)] = SelectSelector(
        SelectSelectorConfig(
            options=retailer_options,
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
    """Handle the initial config flow (step 1: country, step 2: details)."""

    VERSION = 1

    def __init__(self) -> None:
        self._base: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        todo_options = await _get_todo_lists(self.hass)
        if not todo_options:
            return self.async_abort(reason="no_lists")

        if user_input is not None:
            self._base = dict(user_input)
            return await self.async_step_details()

        return self.async_show_form(
            step_id="user",
            data_schema=_build_country_schema(include_name=True),
        )

    async def async_step_details(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        country = self._base.get(CONF_COUNTRY, DEFAULT_COUNTRY)
        todo_options = await _get_todo_lists(self.hass)

        if user_input is not None:
            data = {**self._base, **_normalize_input(user_input)}
            if not _zip_valid(data[CONF_ZIP_CODE], country):
                errors[CONF_ZIP_CODE] = f"invalid_zip_{country}"
            else:
                return self.async_create_entry(
                    title=data.get(CONF_NAME, DEFAULT_NAME),
                    data=data,
                )

        schema = _build_details_schema(country, todo_options, user_input)
        return self.async_show_form(step_id="details", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return AngeboteCheckerOptionsFlow()


class AngeboteCheckerOptionsFlow(OptionsFlow):
    """Handle options (reconfigure) flow: step 1 country, step 2 details.

    Note: No __init__ accepting config_entry – that pattern is broken in HA 2025.12+.
    Use self.config_entry (provided by OptionsFlow base class) instead.
    """

    def __init__(self) -> None:
        self._country: str = DEFAULT_COUNTRY

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            self._country = user_input[CONF_COUNTRY]
            return await self.async_step_details()

        return self.async_show_form(
            step_id="init",
            data_schema=_build_country_schema(current, include_name=False),
        )

    async def async_step_details(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        todo_options = await _get_todo_lists(self.hass)
        current = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            data = _normalize_input(user_input)
            if not _zip_valid(data[CONF_ZIP_CODE], self._country):
                errors[CONF_ZIP_CODE] = f"invalid_zip_{self._country}"
            else:
                data[CONF_COUNTRY] = self._country
                return self.async_create_entry(title="", data=data)

        defaults = user_input if user_input is not None else current
        schema = _build_details_schema(self._country, todo_options, defaults)
        return self.async_show_form(step_id="details", data_schema=schema, errors=errors)
