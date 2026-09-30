"""Constants for the Angebote Checker integration."""
from __future__ import annotations

import json
from pathlib import Path

DOMAIN = "angebote_checker"

# Read version from manifest so there is a single source of truth
_manifest = json.loads((Path(__file__).parent / "manifest.json").read_text())
INTEGRATION_VERSION: str = _manifest.get("version", "1.0.0")

# Config keys
CONF_ZIP_CODE = "zip_code"
CONF_TODO_LISTS = "todo_lists"
CONF_RETAILERS = "retailers"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_NAME = "name"
CONF_COUNTRY = "country"

# Defaults
DEFAULT_SCAN_INTERVAL = 60  # minutes
DEFAULT_NAME = "Angebote Checker"
DEFAULT_COUNTRY = "de"

# Marktguru API – länderspezifische Konfiguration
# api_key/client_key: None = beim ersten Zugriff automatisch von der Startseite
# (boot config) auslesen und im Speicher cachen; bei HTTP 401/403 erneut auslesen.
MARKTGURU_LIMIT = 20
MARKTGURU_USER_AGENT = "Mozilla/5.0"

COUNTRIES: dict[str, dict] = {
    "de": {
        "label": "Deutschland",
        "api_url": "https://api.marktguru.de/api/v1/offers/search",
        "site_url": "https://www.marktguru.de/",
        "image_url": "https://cdn.marktguru.de/api/v1/offers/{offer_id}/images/default/0/medium.webp",
        "zip_pattern": r"\d{5}",
        "api_key": "8Kk+pmbf7TgJ9nVj2cXeA7P5zBGv8iuutVVMRfOfvNE=",
        "client_key": "WU/RH+PMGDi+gkZer3WbMelt6zcYHSTytNB7VpTia90=",
        "retailers": [
            "Aldi",
            "Lidl",
            "Rewe",
            "Edeka",
            "Kaufland",
            "Netto",
            "Penny",
            "dm",
            "Rossmann",
            "Müller",
            "Real",
            "Norma",
            "Globus",
            "tegut",
            "V-Markt",
            "Hit",
            "Combi",
            "Marktkauf",
            "Famila",
            "diska",
        ],
    },
    "at": {
        "label": "Österreich",
        "api_url": "https://api.marktguru.at/api/v1/offers/search",
        "site_url": "https://www.marktguru.at/",
        "image_url": "https://cdn.marktguru.at/api/v1/offers/{offer_id}/images/default/0/medium.webp",
        "zip_pattern": r"\d{4}",
        "api_key": None,
        "client_key": None,
        "retailers": [
            "Billa",
            "Billa Plus",
            "Spar",
            "Eurospar",
            "Interspar",
            "Hofer",
            "Lidl",
            "Penny",
            "MPreis",
            "Unimarkt",
            "Norma",
            "dm",
            "Bipa",
            "Müller",
            "Adeg",
        ],
    },
}

COUNTRY_OPTIONS = [
    {"value": code, "label": cfg["label"]} for code, cfg in COUNTRIES.items()
]


def get_country(code: str | None) -> dict:
    """Return the country config; unknown/missing code falls back to the default."""
    return COUNTRIES.get(code or DEFAULT_COUNTRY, COUNTRIES[DEFAULT_COUNTRY])


# Service
SERVICE_REFRESH = "refresh"

# Frontend resource
URL_BASE = "/angebote-checker"
CARD_JS_FILENAME = "angebote-checker-card.js"

# Attribute names used in sensor state attributes
ATTR_OFFERS = "offers"
ATTR_LAST_UPDATE = "last_update"
ATTR_ITEM_NAME = "item"
ATTR_PRICE = "price"
ATTR_RETAILER = "retailer"
ATTR_DESCRIPTION = "description"
ATTR_VALID_FROM = "valid_from"
ATTR_VALID_TO = "valid_to"
ATTR_IMAGE_URL = "image_url"
ATTR_SOURCE_LIST = "source_list"
