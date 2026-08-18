# Weboberfläche

Erreichbar unter `http://<ip>:8080/` und – wenn Avahi läuft – unter
`http://<hostname>.local:8080/`.

Die Oberfläche ist **bewusst ohne Passwort** und für das lokale Netz gedacht.
Port 8080 darf nicht ins Internet weitergeleitet werden. Sprache oben rechts
umschaltbar (DE/EN).

## Übersicht

Zeigt pro Drucker eine Statusampel:

| Farbe | Bedeutung |
|---|---|
| 🟢 grün | Betriebsbereit |
| 🟡 gelb | Warnung, z. B. Papier fast leer |
| 🔴 rot | Fehler: Papierende, Deckel offen, Cutter-Fehler, oder nicht verbunden |
| ⚪ grau | Status unbekannt (Transport ohne Rückkanal) |

Dazu: die Adresse fürs Kassensystem (anklickbar zum Kopieren), Verbindung,
erkanntes Modell, Auftragszähler, letzter Auftrag, letzter Fehler und der
Zustand des Netzwerk-Listeners.

Die Seite aktualisiert sich alle fünf Sekunden selbst.

## Drucker

Verwaltung der Drucker-Einträge.

* **Geräte suchen** – listet alle USB-, `usblp`- und seriellen Geräte, die als
  Bondrucker in Frage kommen. Mit *Übernehmen* wird ein Gerät einem Drucker
  zugeordnet.
* **Name** – frei wählbar, taucht in Testdrucken und im Support-Bericht auf.
* **IP-Adresse für Port 9100** (`bind`) – `0.0.0.0` bedeutet „alle Adressen des
  Geräts". Für mehrere Ausdruckgruppen bekommt jeder Drucker hier seine eigene
  IP, siehe [07-ausdruckgruppen.md](07-ausdruckgruppen.md).
* **Anschluss** – `auto`, `usb`, `usblp`, `serial` oder `network`. `auto` sucht
  bei jedem Start das plausibelste lokale Gerät.
* **Druckerprofil** – `automatisch` oder ein konkretes Modell aus der
  mitgelieferten Datenbank.
* **Optionen** – Schnitt nach jedem Auftrag, Kassenlade nach jedem Auftrag,
  `ESC @` vor jedem Auftrag, Statusabfrage-Intervall, Papiervorschub.

Änderungen werden sofort übernommen; die betroffenen Listener starten neu.

## Funktionen

Die Funktionsmatrix je Drucker. Jede Zeile zeigt:

* **erkannt** – was aus Profil und Live-Abfrage ermittelt wurde
* **Einstellung** – `automatisch` / `ein (erzwungen)` / `aus (erzwungen)`
* **wirksam** – was BonBridge tatsächlich benutzt

Erkannte Funktionen sind: Papierschneider, Kassenlade, Signalton, Barcodes,
QR-Codes, PDF417, Bilddruck, NV-Logo und Statusabfrage.

**Warum überschreiben?** Die Modell-Datenbank ist eine Sammlung von
Erfahrungswerten. Wenn dein Gerät zwar als „hat Cutter" geführt wird, aber
keinen hat (Baureihenvariante, ausgebauter Cutter), schaltest du die Funktion
hier ab – dann sendet BonBridge keinen Schnittbefehl mehr.

Darunter stehen die **empfohlenen Werte fürs Kassensystem** und die
**aktiven Tests**:

| Test | Wirkung |
|---|---|
| Schneiden testen | Papiervorschub + Teilschnitt |
| Kassenlade öffnen | `ESC p` – Schublade muss aufspringen |
| Signalton | `ESC ( A` – nur bei Geräten mit Buzzer |
| Papiervorschub | vier Zeilen |
| Funktionstestseite | Fett, doppelte Größe, Barcode, QR |

Diese Tests verbrauchen Papier und laufen deshalb nie automatisch.

## Diagnose

* **Letzte Druckaufträge** – Nummer, Quelle (IP des Kassensystems), Größe,
  Zeitpunkt und eine lesbare Vorschau der Daten. Damit lässt sich beantworten:
  *Ist der Auftrag überhaupt angekommen?*
* **Rohdaten senden** – Text oder Hex-Bytes direkt an den Drucker,
  z. B. `1B 40` für `ESC @` (Reset). Für Fehlersuche und Memory-Switches.
* **Zwischenspeicher leeren** – verwirft gespoolte Aufträge, die nicht mehr
  gedruckt werden sollen.
* **Status / Identity** – die rohen Antworten von `DLE EOT` und `GS I`.
* **Systemausgaben** – `lsusb`, `/dev/usb/`, `ss -tlnp`, `ip addr`,
  `dmesg | tail`, Kernelmodule, Dienststatus.
* **Support-Bericht herunterladen** – eine Textdatei mit allem oben Genannten.
  Das ist die Datei, die man an eine Support-Anfrage anhängt.

## Anbindung

Fertige, kopierbare Einrichtungsanleitung – siehe
[04-orderassist.md](04-orderassist.md). Enthält die IP zum Anklicken, die
empfohlenen Druckeinstellungen, eine nummerierte Schrittliste und
Beispielbefehle für CUPS, Windows, macOS und die Kommandozeile.

## System

* Gerätebezeichnung, Port der Weboberfläche, RAW-Port
* mDNS/Bonjour-Ankündigung an/aus
* Epson-Suchprotokoll (ENPC) beantworten – **experimentell**, siehe
  [06-diagnose.md](06-diagnose.md)
* Systeminformationen: Modell, Betriebssystem, Kernel, Architektur, Python,
  Laufzeit, freier Speicher
* Links auf die Dokumentation in der eingestellten Sprache

## REST-API

Die Oberfläche benutzt ausschließlich diese API – man kann sie also auch von
einem Skript oder einem Monitoring-System ansprechen.

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/api/overview` | Gesamtstatus |
| GET | `/healthz` | Lebenszeichen für Monitoring |
| GET/PUT | `/api/config` | Konfiguration lesen/ändern |
| GET/POST | `/api/printers` | Drucker auflisten/anlegen |
| GET/PATCH/DELETE | `/api/printers/<id>` | Drucker lesen/ändern/löschen |
| POST | `/api/printers/<id>/test` | Testdruck (`kind`: `standard`, `features`, `minimal`) |
| POST | `/api/printers/<id>/probe` | `what`: `cut`, `drawer`, `buzzer`, `feed` |
| POST | `/api/printers/<id>/raw` | `{"hex": "1B40"}` oder `{"text": "..."}` |
| POST | `/api/printers/<id>/refresh` | Status neu abfragen |
| POST | `/api/printers/<id>/redetect` | Verbindung + Erkennung neu aufbauen |
| GET | `/api/printers/<id>/integration` | Werte fürs Kassensystem |
| GET | `/api/scan` | Geräte suchen |
| GET | `/api/profiles` | verfügbare Druckerprofile |
| GET | `/api/diagnostics` | Systeminfos + Kommandoausgaben |
| GET | `/api/report` | Support-Bericht als Text |
| POST | `/api/restart` | Drucker und Listener neu starten |

Beispiel:

```bash
curl -s http://192.168.1.50:8080/api/overview | python3 -m json.tool
curl -s -X POST http://192.168.1.50:8080/api/printers/printer1/test \
     -H 'Content-Type: application/json' -d '{"kind":"standard"}'
```
