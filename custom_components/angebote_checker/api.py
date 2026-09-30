"""Marktguru API wrapper for Angebote Checker."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import date
from typing import Any

import aiohttp

from .const import (
    ATTR_DESCRIPTION,
    ATTR_IMAGE_URL,
    ATTR_ITEM_NAME,
    ATTR_PRICE,
    ATTR_RETAILER,
    ATTR_VALID_FROM,
    ATTR_VALID_TO,
    COUNTRIES,
    DEFAULT_COUNTRY,
    MARKTGURU_LIMIT,
    MARKTGURU_USER_AGENT,
    get_country,
)

_LOGGER = logging.getLogger(__name__)

# In-Memory-Cache der API-Keys pro Land: {"at": {"api_key": ..., "client_key": ...}}
_KEY_CACHE: dict[str, dict[str, str]] = {}
_KEY_LOCK = asyncio.Lock()

_API_KEY_RE = re.compile(r'"apiKey"\s*:\s*"([^"]+)"')
_CLIENT_KEY_RE = re.compile(r'"clientKey"\s*:\s*"([^"]+)"')


def _parse_date(value: str | None) -> str:
    """Convert ISO datetime string to German DD.MM.YYYY format."""
    if not value:
        return ""
    try:
        d = date.fromisoformat(value[:10])
        return d.strftime("%d.%m.%Y")
    except ValueError:
        return value


def _parse_entry(
    entry: dict[str, Any],
    query: str,
    retailer_filter: list[str] | None,
    image_url_template: str,
) -> dict[str, Any] | None:
    """Parse a single Marktguru API result entry."""

    # ── Retailer ──────────────────────────────────────────────────────────
    advertisers = entry.get("advertisers") or []
    if advertisers and isinstance(advertisers, list):
        first = advertisers[0]
        retailer_name: str = (
            first.get("name", "Unbekannt") if isinstance(first, dict) else str(first)
        )
    else:
        retailer_name = (
            entry.get("retailerName")
            or entry.get("advertiserName")
            or "Unbekannt"
        )

    if retailer_filter and not any(
        r.lower() in retailer_name.lower() for r in retailer_filter
    ):
        return None

    # ── Price ─────────────────────────────────────────────────────────────
    price_raw = entry.get("price")
    try:
        price_str = f"{float(price_raw):.2f} €".replace(".", ",") if price_raw is not None else "—"
    except (TypeError, ValueError):
        price_str = str(price_raw) if price_raw else "—"

    # ── Validity dates ─────────────────────────────────────────────────────
    # API returns: "validityDates": [{"from": "2026-06-07T22:00:00Z", "to": "..."}]
    valid_from = ""
    valid_to = ""
    validity_dates = entry.get("validityDates") or []
    if validity_dates and isinstance(validity_dates, list):
        first_date = validity_dates[0]
        if isinstance(first_date, dict):
            valid_from = _parse_date(first_date.get("from"))
            valid_to = _parse_date(first_date.get("to"))
    else:
        # Fallback: flat fields
        valid_from = _parse_date(entry.get("validFrom") or entry.get("valid_from"))
        valid_to = _parse_date(entry.get("validTo") or entry.get("valid_to"))

    # ── Image URL ──────────────────────────────────────────────────────────
    # API returns: "images": {"count": 1, "metadata": [...]}
    # Länderspezifisches CDN-Muster (siehe const.COUNTRIES)
    image_url = ""
    offer_id = entry.get("id")
    if offer_id:
        image_url = image_url_template.format(offer_id=offer_id)

    # ── Description ───────────────────────────────────────────────────────
    description = (
        entry.get("description")
        or (entry.get("product") or {}).get("name")
        or entry.get("name")
        or ""
    )

    return {
        ATTR_ITEM_NAME: query,
        ATTR_PRICE: price_str,
        ATTR_RETAILER: retailer_name,
        ATTR_DESCRIPTION: description,
        ATTR_VALID_FROM: valid_from,
        ATTR_VALID_TO: valid_to,
        ATTR_IMAGE_URL: image_url,
    }


class MarktguruAPI:
    """Async wrapper around the Marktguru offers search endpoint."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        zip_code: str,
        country: str = DEFAULT_COUNTRY,
    ) -> None:
        self._session = session
        self._zip_code = zip_code
        self._country_code = country if country in COUNTRIES else DEFAULT_COUNTRY
        self._country = get_country(country)

    # ── API keys ──────────────────────────────────────────────────────────
    def _keys(self) -> dict[str, str] | None:
        """Return cached/configured keys for the country, or None if unknown."""
        cached = _KEY_CACHE.get(self._country_code)
        if cached:
            return cached
        api_key = self._country.get("api_key")
        client_key = self._country.get("client_key")
        if api_key and client_key:
            return {"api_key": api_key, "client_key": client_key}
        return None

    async def _scrape_keys(self) -> dict[str, str] | None:
        """Read apiKey/clientKey from the country's marktguru homepage."""
        async with _KEY_LOCK:
            # Parallele Suchen: ein anderer Task hat evtl. schon neu ausgelesen
            cached = _KEY_CACHE.get(self._country_code)
            if cached:
                return cached
            return await self._scrape_keys_locked()

    async def _scrape_keys_locked(self) -> dict[str, str] | None:
        url = self._country["site_url"]
        try:
            async with self._session.get(
                url,
                headers={"User-Agent": MARKTGURU_USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    _LOGGER.warning("Marktguru: Startseite %s → HTTP %s", url, resp.status)
                    return None
                html = await resp.text()
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.error("Marktguru: Keys von %s nicht abrufbar: %s", url, err)
            return None

        api_match = _API_KEY_RE.search(html)
        client_match = _CLIENT_KEY_RE.search(html)
        if not (api_match and client_match):
            _LOGGER.error(
                "Marktguru: API-Keys auf %s nicht gefunden (Seitenaufbau geändert?)", url
            )
            return None

        keys = {"api_key": api_match.group(1), "client_key": client_match.group(1)}
        _KEY_CACHE[self._country_code] = keys
        _LOGGER.debug("Marktguru: API-Keys für '%s' ausgelesen", self._country_code)
        return keys

    @staticmethod
    def _headers(keys: dict[str, str]) -> dict[str, str]:
        return {
            "x-clientkey": keys["client_key"],
            "x-apikey": keys["api_key"],
            "Accept": "application/json",
            "User-Agent": MARKTGURU_USER_AGENT,
        }

    # ── Search ────────────────────────────────────────────────────────────
    async def search_offers(
        self,
        query: str,
        retailer_filter: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for offers matching *query* and return normalised offer dicts."""
        params = {
            "as": "web",
            "limit": str(MARKTGURU_LIMIT),
            "offset": "0",
            "q": query,
            "zipCode": self._zip_code,
        }

        keys = self._keys() or await self._scrape_keys()
        if keys is None:
            return []

        data: dict[str, Any] | None = None
        for attempt in (1, 2):
            try:
                async with self._session.get(
                    self._country["api_url"],
                    headers=self._headers(keys),
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status in (401, 403) and attempt == 1:
                        # Keys evtl. rotiert → einmalig neu auslesen
                        _KEY_CACHE.pop(self._country_code, None)
                        new_keys = await self._scrape_keys()
                        if new_keys is None:
                            return []
                        keys = new_keys
                        continue
                    if resp.status != 200:
                        _LOGGER.warning(
                            "Marktguru API: HTTP %s für Suche '%s'", resp.status, query
                        )
                        return []
                    data = await resp.json(content_type=None)
                    break
            except asyncio.TimeoutError:
                _LOGGER.error("Marktguru API: Timeout für Suche '%s'", query)
                return []
            except aiohttp.ClientError as err:
                _LOGGER.error("Marktguru API: Verbindungsfehler für '%s': %s", query, err)
                return []

        if data is None:
            return []

        raw_results = data.get("results", [])
        _LOGGER.debug("AC: '%s' → %d Rohtreffer", query, len(raw_results))

        results: list[dict[str, Any]] = []
        for entry in raw_results:
            try:
                offer = _parse_entry(
                    entry, query, retailer_filter, self._country["image_url"]
                )
                if offer is not None:
                    results.append(offer)
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("AC: Parse-Fehler übersprungen: %s", err)

        _LOGGER.debug("AC: '%s' → %d verwertbare Angebote", query, len(results))
        return results

    async def search_multiple(
        self,
        queries: list[str],
        retailer_filter: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Run multiple searches concurrently and merge results."""
        tasks = [self.search_offers(q, retailer_filter) for q in queries]
        nested = await asyncio.gather(*tasks, return_exceptions=True)
        combined: list[dict[str, Any]] = []
        for res in nested:
            if isinstance(res, list):
                combined.extend(res)
            else:
                _LOGGER.error("Unerwarteter Fehler bei paralleler Suche: %s", res)
        return combined
