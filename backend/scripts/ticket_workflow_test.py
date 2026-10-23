import uuid

import requests

from backend.config import BACKEND_API_KEY, BASE_BACKEND_URL

"""Manuelle API-Testdaten; dieses Modul sendet keine Requests.

USER_ID durch die UUID eines bestehenden Testnutzers ersetzen.
OWN_ORDER_NUMBER muss diesem Nutzer gehoeren, FOREIGN_ORDER_NUMBER einem
anderen Nutzer. UNKNOWN_ORDER_NUMBER darf nicht in der Datenbank existieren.
Pro neuem Ticket einen neuen Idempotency-Key als Request-Header verwenden.
Die Werte unter TEST_TICKETS sind jeweils die JSON-Bodys fuer POST /tickets/.
"""

USER_ID = "22b61f45-6d3a-4a7a-8681-464b1c8e1926"  # Platzhalter, ersetzen!
OWN_ORDER_NUMBER = "AB-0042"
FOREIGN_ORDER_NUMBER = "CD-0043"
UNKNOWN_ORDER_NUMBER = "ZZ-9999"

TEST_TICKETS = {
    # KB-001 und KB-002: Nachweise und Ersatzbedingungen, keine Zusage
    # ueber Lagerbestand oder bereits ausgefuehrte Ersatzlieferungen.
    "damaged_goods_own_order": {
        "user_id": USER_ID,
        "text": f"Meine Bestellung {OWN_ORDER_NUMBER} ist heute angekommen. Das Gehaeuse ist gebrochen und die Verpackung beschaedigt. Welche Fotos braucht ihr und kann ich Ersatz bekommen?",
    },
    # Muss vor der Wissenssuche mit order_not_found zur Pruefung gehen.
    "damaged_goods_foreign_order": {
        "user_id": USER_ID,
        "text": f"Der Artikel aus Bestellung {FOREIGN_ORDER_NUMBER} ist zerbrochen angekommen. Ich moechte eine Ersatzlieferung erhalten.",
    },
    "damaged_goods_unknown_order": {
        "user_id": USER_ID,
        "text": f"Meine Bestellung {UNKNOWN_ORDER_NUMBER} ist beschaedigt angekommen. Wie bekomme ich Ersatz?",
    },
    # Erwarteter Pruefgrund: missing_order_number bei sicherer Klassifikation.
    "damaged_goods_missing_order_number": {
        "user_id": USER_ID,
        "text": "Mein Paket ist heute angekommen, aber der Artikel darin ist zerbrochen. Ich brauche eine Ersatzlieferung, habe die Bestellnummer gerade nicht zur Hand.",
    },
    # KB-003: 30-Tage-Shop-Garantie fuer ungeoeffnete, unbenutzte Ware.
    "return_unopened_after_twenty_days": {
        "user_id": USER_ID,
        "text": f"Ich habe Bestellung {OWN_ORDER_NUMBER} vor 20 Tagen erhalten. Der Artikel ist ungeoeffnet und unbenutzt. Kann ich ihn wegen Nichtgefallen noch zurueckgeben?",
    },
    # KB-004: Ruecksendegebuehr laut Beispieldokument; Preis ist hier
    # eine Kundenaussage und kein verifizierter Datenbankwert.
    "return_shipping_cost": {
        "user_id": USER_ID,
        "text": f"Ich moechte Bestellung {OWN_ORDER_NUMBER} wegen Nichtgefallen zuruecksenden. Laut meiner Rechnung hat der Artikel 25 Euro gekostet. Was kostet die Retoure und wo bekomme ich das Label?",
    },
    # KB-005: Lieferzeiten und Tracking; keine Tracking-ID erfinden.
    "shipping_tracking": {
        "user_id": USER_ID,
        "text": f"Wo bleibt Bestellung {OWN_ORDER_NUMBER}? Wie lange dauert die Lieferung nach Deutschland und wo finde ich die Sendungsverfolgung?",
    },
    # KB-006: Verlustmeldung; ohne Trackingdaten keine Nachforschung behaupten.
    "shipment_reported_missing": {
        "user_id": USER_ID,
        "text": f"Das Paket zu Bestellung {OWN_ORDER_NUMBER} ist nicht angekommen. Laut meiner Sendungsverfolgung gab es seit sechs Werktagen keinen Scan. Was soll ich jetzt pruefen?",
    },
    # KB-007: Rechnungsdownload.
    "invoice_download": {
        "user_id": USER_ID,
        "text": f"Ich finde die Rechnung fuer Bestellung {OWN_ORDER_NUMBER} nicht mehr. Wo kann ich das PDF herunterladen?",
    },
    # KB-008: Technische FAQ soll ohne Bestellung weiterlaufen.
    "faq_password_reset": {
        "user_id": USER_ID,
        "text": "Ich habe mein Passwort fuer das Kundenkonto vergessen. Wie kann ich es zuruecksetzen und wie lange ist der Link gueltig?",
    },
    "faq_reset_email_missing": {
        "user_id": USER_ID,
        "text": "Ich habe Passwort vergessen angeklickt, aber die E-Mail zum Zuruecksetzen kommt nicht an. Was kann ich tun?",
    },
    # Fachlich nicht durch KB-001 bis KB-008 abgedeckt. Qdrant kann trotzdem
    # Treffer liefern: Der Entwurf soll fehlendes Wissen offen benennen.
    "faq_not_in_knowledge": {
        "user_id": USER_ID,
        "text": "Wie richte ich in eurer App eine Zwei-Faktor-Anmeldung mit einem FIDO2-Sicherheitsschluessel ein? Welche Schluesselmodelle unterstuetzt ihr?",
    },
    # Zwei Nummern: Regex-Extraktion liefert aktuell keine eindeutige Nummer.
    "ambiguous_order_numbers": {
        "user_id": USER_ID,
        "text": f"Ich habe die Bestellungen {OWN_ORDER_NUMBER} und {FOREIGN_ORDER_NUMBER}. Einer der gelieferten Artikel ist zerbrochen. Ich weiss nicht, zu welcher Bestellung er gehoert.",
    },
}


def main() -> None:

    for ticket_header, payload in TEST_TICKETS.items():
        payload = TEST_TICKETS[ticket_header]

        response = requests.post(
            f"{BASE_BACKEND_URL.rstrip('/')}/tickets/",
            json=payload,
            headers={
                "X-API-Key": BACKEND_API_KEY,
                "Idempotency-Key": str(uuid.uuid4()),
            },
            timeout=30,
        )

        response.raise_for_status()
        print(response.json())

        print("\n")
        print("\n")
        print("\n")


if __name__ == "__main__":
    main()
