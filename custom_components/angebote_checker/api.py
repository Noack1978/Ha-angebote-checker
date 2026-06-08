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
    # Real image URL pattern: https://images.marktguru.de/offers/{id}/{size}.jpg
    image_url = ""
    offer_id = entry.get("id")
    if offer_id:
        image_url = f"https://cdn.marktguru.de/api/v1/offers/{offer_id}/images/default/0/medium.webp"

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

        raw_results = data.get("results", [])
        _LOGGER.debug("AC: '%s' → %d Rohtreffer", query, len(raw_results))

        results: list[dict[str, Any]] = []
        for entry in raw_results:
            try:
                offer = _parse_entry(entry, query, retailer_filter)
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
