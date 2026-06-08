"""Marktguru API wrapper for Angebote Checker."""
from __future__ import annotations

import asyncio
import logging
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
    MARKTGURU_BASE_URL,
    MARKTGURU_HEADERS,
    MARKTGURU_LIMIT,
)

_LOGGER = logging.getLogger(__name__)


def _parse_date(value: str | None) -> str:
    """Convert an ISO date string to German DD.MM.YYYY format."""
    if not value:
        return ""
    try:
        d = date.fromisoformat(value[:10])
        return d.strftime("%d.%m.%Y")
    except ValueError:
        return value


class MarktguruAPI:
    """Async wrapper around the Marktguru offers search endpoint."""

    def __init__(self, session: aiohttp.ClientSession, zip_code: str) -> None:
        self._session = session
        self._zip_code = zip_code

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
        try:
            async with self._session.get(
                MARKTGURU_BASE_URL,
                headers=MARKTGURU_HEADERS,
                params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    _LOGGER.warning(
                        "Marktguru API: HTTP %s für Suche '%s'", resp.status, query
                    )
                    return []
                data = await resp.json(content_type=None)
        except asyncio.TimeoutError:
            _LOGGER.error("Marktguru API: Timeout für Suche '%s'", query)
            return []
        except aiohttp.ClientError as err:
            _LOGGER.error("Marktguru API: Verbindungsfehler für '%s': %s", query, err)
            return []

        results: list[dict[str, Any]] = []
        for entry in data.get("results", []):
            try:
                advertisers = entry.get("advertisers", [])
                retailer_name: str = advertisers[0].get("name", "Unbekannt") if advertisers else "Unbekannt"

                if retailer_filter and not any(
                    r.lower() in retailer_name.lower() for r in retailer_filter
                ):
                    continue

                price_raw = entry.get("price")
                price_str = (
                    f"{price_raw:.2f} €".replace(".", ",")
                    if price_raw is not None
                    else "—"
                )

                images = entry.get("images", [])
                image_url = ""
                if images:
                    img = images[0]
                    image_url = (
                        img.get("medium") or img.get("large") or img.get("small") or ""
                    )

                results.append(
                    {
                        ATTR_ITEM_NAME: query,
                        ATTR_PRICE: price_str,
                        ATTR_RETAILER: retailer_name,
                        ATTR_DESCRIPTION: entry.get("description") or entry.get("name", ""),
                        ATTR_VALID_FROM: _parse_date(entry.get("validFrom")),
                        ATTR_VALID_TO: _parse_date(entry.get("validTo")),
                        ATTR_IMAGE_URL: image_url,
                    }
                )
            except (IndexError, KeyError, TypeError) as err:
                _LOGGER.debug("Ungültiger API-Eintrag übersprungen: %s", err)

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
