---
id: KB-002
title: Richtlinie für Ersatzlieferungen
version: 1.1
category: beschaedigte_ware
tags: [ersatzlieferung, umtausch, lagerbestand, freigabe]
---

# Bedingungen für Ersatzlieferungen

Eine Ersatzlieferung ist der bevorzugte Prozess bei beschädigter Ware oder Falschlieferungen.

## Voraussetzungen
1. **Verfügbarkeit**: Der Artikel muss im Warenwirtschaftssystem als "auf Lager" markiert sein.
2. **Identifikation**: Die ursprüngliche Bestellnummer (z. B. `AB-0042`) muss validiert sein.
3. **Rücksendung des Altartikels**:
   * Bei Werten > 30 € muss der beschädigte Artikel zuerst mit einem kostenlosen Retourenschein zurückgesendet werden, es sei denn, ein Supervisor erteilt eine Ausnahme.
   * Bei Werten ≤ 30 € reicht ein eindeutiges Fotobeweisdokument aus.

## System-Aktion: `propose_replacement`
* Der Bot schlägt die Aktion `propose_replacement(order_id, item_sku, quantity)` vor.
* Die Aktion wird erst ausgeführt, nachdem der Agent auf "Genehmigen" klickt.
