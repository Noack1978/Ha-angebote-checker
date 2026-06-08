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

# Defaults
DEFAULT_SCAN_INTERVAL = 60  # minutes
DEFAULT_NAME = "Angebote Checker"

# Marktguru API
MARKTGURU_BASE_URL = "https://api.marktguru.de/api/v1/offers/search"
MARKTGURU_HEADERS = {
    "x-clientkey": "WU/RH+PMGDi+gkZer3WbMelt6zcYHSTytNB7VpTia90=",
    "x-apikey": "8Kk+pmbf7TgJ9nVj2cXeA7P5zBGv8iuutVVMRfOfvNE=",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0",
}
MARKTGURU_LIMIT = 20

# Known retailers for filter selection
RETAILER_OPTIONS = [
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
]

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
