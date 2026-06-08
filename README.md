# Angebote Checker für Home Assistant

Eine HACS-kompatible Custom Integration, die deine HA-Einkaufslisten (Todo-Entitäten) mit dem **Marktguru-Angebotsdienst** verbindet und dir im Dashboard anzeigt, welche Artikel gerade wo im Angebot sind.

## Features

- 🛒 Liest Artikel aus einer oder mehreren HA-Einkaufslisten (Todo-Entitäten, z. B. Bring!, HomeAssistant Shopping List)
- 🏷️ Sucht automatisch nach aktuellen Angeboten per Marktguru-API
- 🏪 Konfigurierbarer Händler-Filter (Aldi, Lidl, Rewe, Edeka, Kaufland …)
- 📅 Zeigt Angebotszeitraum (von–bis) je Händler an
- 🔄 Automatische Aktualisierung (konfigurierbares Intervall, min. 5 Minuten)
- ▶️ Manuelle Suche per Service-Button im Dashboard
- 🖼️ Custom Lovelace-Karte mit Kachel- und Listenansicht, Händler-Filter-Chips und Produktbildern
- 🔍 Lightbox: Produktbild per Klick vergrößern
- ✏️ Artikel direkt aus der Karte mit Angebotsinformationen ergänzen (z. B. `Butter → Butter (Lidl 0,99 €)`)
- ➡️ Artikel aus der Lightbox heraus auf eine andere Einkaufsliste verschieben
- ✅ Vollständiger Config Flow – keine `configuration.yaml`-Änderungen nötig

## Installation

### HACS (empfohlen)

[![In HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Noack1978&repository=ha-angebote-checker&category=integration)

1. Auf den Button klicken – HACS öffnet sich direkt mit diesem Repository
2. **Herunterladen** klicken → Home Assistant neu starten

Oder manuell als benutzerdefiniertes Repository:

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

Die Integration bringt eine eigene Lovelace-Karte mit, die nach der Installation automatisch im Dashboard-Editor unter **„Angebote Checker"** auswählbar ist.

```yaml
type: custom:angebote-checker-card
entity: sensor.angebote_checker_angebote_checker
title: Angebote
max_height: 500
show_images: true
default_view: grid
```

### Karten-Funktionen

| Funktion | Beschreibung |
|---|---|
| Kachel-/Listenansicht | Umschalten über die Buttons oben rechts |
| Händler-Filter | Chips oberhalb der Angebote – Klick filtert nach Händler |
| Suchen-Button | Löst sofort eine neue API-Abfrage aus |
| Bild vergrößern | Klick auf ein Produktbild öffnet die Lightbox |
| Artikel ergänzen | In der Lightbox: benennt den Todo-Eintrag um (fügt Händler + Preis hinzu) |
| Liste verschieben | In der Lightbox: verschiebt den Artikel auf eine andere Todo-Liste |

## Service

```yaml
service: angebote_checker.refresh
```

Löst sofort eine neue Suche aus (z. B. per Dashboard-Button).

## Changelog

### v1.1.0
- 🔍 Lightbox: Produktbild per Klick vergrößerbar
- ✏️ Artikel aus der Lightbox heraus mit Angebotsinformationen ergänzen
- ➡️ Artikel direkt in der Karte auf eine andere Einkaufsliste verschieben
- 🐛 Fix: Datumsparser für `validityDates`-API-Struktur korrigiert
- 🐛 Fix: Syntaxfehler in JS-Karte behoben
- 🐛 Fix: `todo.get_items`-Service-Verfügbarkeit wird jetzt vor Aufruf geprüft

### v1.0.0
- Erstveröffentlichung
- Custom Lovelace-Karte mit Kachel- und Listenansicht
- Händler-Filter, automatische Lovelace-Ressourcen-Registrierung
- Marktguru-API-Anbindung mit regionaler PLZ-Suche

## Bekannte Einschränkungen

Die Marktguru-API ist eine inoffizielle API ohne garantierte Stabilität. Die API-Keys sind in der App öffentlich und werden von vielen HA-Nutzern geteilt.

## Lizenz

MIT License – © Noack1978
