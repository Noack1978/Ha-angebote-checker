# Angebote Checker für Home Assistant

Eine HACS-kompatible Custom Integration, die deine HA-Einkaufslisten (Todo-Entitäten) mit dem **Marktguru-Angebotsdienst** verbindet und dir im Dashboard anzeigt, welche Artikel gerade wo im Angebot sind.

## Features

- 🛒 Liest Artikel aus einer oder mehreren HA-Einkaufslisten (Todo-Entitäten, z. B. Bring!, HomeAssistant Shopping List)
- 🏷️ Sucht automatisch nach aktuellen Angeboten per Marktguru-API
- 🏪 Konfigurierbarer Händler-Filter (Aldi, Lidl, Rewe, Edeka, Kaufland …)
- 📅 Zeigt Angebotszeitraum (von–bis) je Händler an
- 🔄 Automatische Aktualisierung (konfigurierbares Intervall, min. 5 Minuten)
- ▶️ Manuelle Suche per Service-Button im Dashboard
- ✅ Vollständiger Config Flow – keine `configuration.yaml`-Änderungen nötig

## Installation

### HACS (empfohlen)

1. HACS öffnen → Integrationen → ⋮ → Benutzerdefiniertes Repository hinzufügen
2. URL: `https://github.com/Noack1978/ha-angebote-checker` · Typ: Integration
3. „Angebote Checker" installieren → Home Assistant neu starten

### Manuell

Den Ordner `custom_components/angebote_checker/` in dein HA-Konfigurationsverzeichnis kopieren und HA neu starten.

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → „Angebote Checker"**
2. Konfigurieren:
   - **Name** der Instanz
   - **Postleitzahl** (5-stellig) – bestimmt die regionale Suche
   - **Einkaufslisten** – alle Todo-Entitäten, die geprüft werden sollen
   - **Händler** – optional einschränken; leer = alle Händler
   - **Aktualisierungsintervall** in Minuten (5–1440)

## Dashboard-Karte

```yaml
type: markdown
title: 🏷️ Angebote meiner Einkaufsliste
content: >
  {% set sensor = states.sensor | selectattr('entity_id', 'match', 'sensor.angebote_checker.*') | list %}
  {% if sensor | length == 0 %}
  _Kein Angebote-Checker-Sensor gefunden._
  {% else %}
  {% set offers = sensor[0].attributes.offers | default([]) %}
  {% set last = sensor[0].attributes.last_update | default('') %}
  {% if offers | length == 0 %}
  **Keine passenden Angebote gefunden.**
  Stand: {{ last[:10] if last else '–' }}
  {% else %}
  Stand: {{ last[:10] if last else '–' }} · {{ offers | length }} Treffer

  | Artikel | Preis | Händler | Angebot |
  |---------|-------|---------|---------|
  {% for o in offers %}
  | {{ o.item }} | **{{ o.price }}** | {{ o.retailer }} | {{ o.valid_from }}–{{ o.valid_to }} |
  {% endfor %}
  {% endif %}
  {% endif %}
```

## Service

```yaml
service: angebote_checker.refresh
```

Löst sofort eine neue Suche aus (z. B. per Dashboard-Button).

## Bekannte Einschränkungen

Die Marktguru-API ist eine inoffizielle API ohne garantierte Stabilität. Die API-Keys sind in der App öffentlich und werden von vielen HA-Nutzern geteilt.

## Lizenz

MIT License – © Noack1978
