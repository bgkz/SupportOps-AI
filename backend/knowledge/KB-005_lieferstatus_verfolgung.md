---
id: KB-005
title: Lieferstatus und Sendungsverfolgung
version: 1.2
category: lieferstatus
tags: [tracking, lieferzeit, versand, dhl, hermes, sendungsnummer]
---

# Lieferstatus & Sendungsverfolgung

## Standard-Lieferzeiten
* **Deutschland**: 1–3 Werktage
* **Österreich / Schweiz**: 2–5 Werktage
* **EU-Ausland**: 3–7 Werktage

## Statusabfrage im System (`get_shipment_status`)
Wenn der Kunde fragt "Wo ist meine Bestellung?", führt der Bot das Tool `get_shipment_status(order_id)` aus:
* **OFFEN / IN_BEARBEITUNG**: Bestellung ist im Lager, noch nicht übergeben.
* **VERSENDET**: Die Tracking-ID ist verfügbar. Link zur DHL/Hermes-Verfolgung an den Kunden ausgeben.
* **ZUGESTELLT**: Das Paket wurde laut Dienstleister abgegeben.

## Wichtiger Hinweis bei Verzögerung
Erst wenn sich der Tracking-Status seit mehr als 4 Werktagen nicht verändert hat, kann ein Nachforschungsauftrag eingeleitet werden.
