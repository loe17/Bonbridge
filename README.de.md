# BonBridge

**Macht aus einem Raspberry Pi oder einem kleinen Linux-Rechner einen Netzwerk-Bondrucker.**

Viele Kassensysteme – darunter OrderAssist – können einen Bondrucker
ausschließlich über **IP-Adresse auf Port 9100** ansprechen. USB- und serielle
Drucker werden gar nicht unterstützt. Genau diese Lücke schließt BonBridge: Es
hängt sich an einen USB- oder seriellen ESC/POS-Drucker und stellt ihn im
Netzwerk so dar, als hätte er eine eingebaute Ethernet-Schnittstelle – dazu
eine Weboberfläche für Status, Diagnose und Einrichtung.

> 🇬🇧 **[English version → README.md](README.md)** ·
> Vollständige Doku: [`docs/de/`](docs/de/)

---

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/loe17/Bonbridge/main/install.sh | sudo bash
```

Das ist die komplette Installation. Sie läuft auf

| Plattform | Hinweise |
|---|---|
| Raspberry Pi Zero 2 W | empfohlen, benötigt einen USB-OTG-Adapter |
| Raspberry Pi 3 / 4 / 5 | Drucker an eine USB-A-Buchse (Pi 4: bevorzugt die schwarzen USB-2.0-Ports) |
| x86-64 Mini-PC / Thin Client | Debian 11–13, Ubuntu 22.04+ |
| Raspberry Pi 1 / 2 / Zero (ARMv6, ARMv7) | läuft – dort das **32-Bit**-Lite-Image nehmen, siehe [Hardware](docs/de/01-hardware.md#raspberry-pi-1-und-andere-alte-boards) |

Kein Compiler, kein `pip`, kein Klonen fremder Repositories zur
Installationszeit – alles, was BonBridge braucht, ist entweder ein
Debian-Paket oder liegt in `vendor/` im Repo.

Danach:

```
Weboberfläche :  http://<ip>:8080/
Dokumentation :  http://<ip>:8080/docs
Kassendruck   :  <ip>  Port 9100  (RAW / ESC-POS)
```

Die IP-Adresse musst du nicht suchen: **BonBridge druckt bei jedem Start einen
Bon mit der eigenen Adresse, dem Port und den Werten fürs Kassensystem.**

## Was es tut

* **RAW/JetDirect-Listener auf Port 9100** – genau das, was Kassensysteme erwarten.
* **Bidirektionale** Kommunikation mit dem Drucker: Papierende, offener Deckel
  und Cutter-Fehler werden sichtbar, statt dass Aufträge stillschweigend
  verschwinden.
* **Ein Besitzer pro Drucker.** Nur ein Worker-Thread schreibt auf das Gerät,
  Druckaufträge können sich also nicht vermischen. Fehlgeschlagene Aufträge
  werden zwischengespeichert und wiederholt statt verworfen.
* **Automatische Druckererkennung** aus USB-Deskriptoren, IEEE-1284-Geräte-ID
  und der ESC/POS-Drucker-ID (`GS I`), abgeglichen mit einer mitgelieferten
  Datenbank von rund 50 Druckermodellen.
* **Es sagt dir, was du im Kassensystem eintragen musst.** Schriftart,
  Zeichensatz und Zeilenbreite kommen aus dem Druckerprofil statt aus
  Ausprobieren.
* **Mehrere Ausdruckgruppen auf einem Gerät.** Kassensysteme adressieren
  Drucker nur über die IP – BonBridge kann deshalb jeden Drucker an eine
  eigene IP-Adresse binden, alle auf Port 9100.
* **Funktionsschalter.** Cutter, Kassenlade, Signalton, Barcode, QR, Grafik –
  jeweils automatisch erkannt und in der Weboberfläche überschreibbar.
* **Mehrere Anschlussarten:** libusb (auch für Drucker, die nie ein
  `/dev/usb/lp0` erzeugen, z. B. die Epson-TM-m30-Familie), Kernel-`usblp`,
  seriell/RS-232 und Netzwerk.
* **CUPS ist optional**, nicht Voraussetzung. Wenn es aktiviert wird, druckt
  dessen Warteschlange *durch* BonBridge hindurch, statt sich mit ihm um das
  Gerät zu streiten.
* **Druckt beim Start die eigene Adresse** – ein Gerät ohne Bildschirm sagt dir
  trotzdem, wohin die App zeigen muss.
* **Begründet jede Warnung.** Jede Statusampel klappt zu den Einzelprüfungen
  auf – Unterspannung, Temperatur, Speicher, Listener, Papier – samt Hinweis,
  was zu tun ist.
* **Bons direkt aus dem Browser drucken**, mit Live-Vorschau in der echten
  Papierbreite.
* **Dokumentation auf dem Gerät**, als HTML unter `/docs`, ohne Internet.

## Schnellprüfung

```bash
bonbridge scan                 # welche Drucker sind nutzbar?
bonbridge report > bericht.txt # vollständiger Support-Bericht
systemctl status bonbridge
journalctl -u bonbridge -f
```

## OrderAssist anbinden

1. `Drucker` → `+ Hinzufügen` → die **IP-Adresse** eintragen, die die
   BonBridge-Weboberfläche anzeigt. Der Port ist in der App fest 9100.
2. In der Weboberfläche den Reiter **Anbindung** öffnen und Schriftart,
   Zeichensatz und Zeilenbreite in die App übernehmen.
3. Testseite drucken und den Drucker einer Ausdruckgruppe zuweisen.

Details: [`docs/de/04-orderassist.md`](docs/de/04-orderassist.md)

## Dokumentation

| | Deutsch | English |
|---|---|---|
| Hardware & Optionen | [01-hardware.md](docs/de/01-hardware.md) | [01-hardware.md](docs/en/01-hardware.md) |
| Anschlusspläne | [02-anschlussplan.md](docs/de/02-anschlussplan.md) | [02-wiring.md](docs/en/02-wiring.md) |
| Druckerkonfiguration | [03-drucker-konfiguration.md](docs/de/03-drucker-konfiguration.md) | [03-printer-setup.md](docs/en/03-printer-setup.md) |
| Kassensystem-Anbindung | [04-orderassist.md](docs/de/04-orderassist.md) | [04-pos-integration.md](docs/en/04-pos-integration.md) |
| Weboberfläche | [05-weboberflaeche.md](docs/de/05-weboberflaeche.md) | [05-web-interface.md](docs/en/05-web-interface.md) |
| Diagnose & FAQ | [06-diagnose.md](docs/de/06-diagnose.md) | [06-diagnostics.md](docs/en/06-diagnostics.md) |
| Mehrere Ausdruckgruppen | [07-ausdruckgruppen.md](docs/de/07-ausdruckgruppen.md) | [07-print-groups.md](docs/en/07-print-groups.md) |
| Architektur | [08-architektur.md](docs/de/08-architektur.md) | [08-architecture.md](docs/en/08-architecture.md) |
| **Fremdcode & Quellen** | [09-referenzen.md](docs/de/09-referenzen.md) | [09-references.md](docs/en/09-references.md) |
| **Updates, Netzwerküberwachung, Wartung** | [10-updates.md](docs/de/10-updates.md) | [10-updates.md](docs/en/10-updates.md) |

## Lizenz

MIT für BonBridge selbst. Mitgelieferte Komponenten behalten ihre eigenen
Lizenzen – siehe [`NOTICE`](NOTICE) und die kommentierte Liste in
[`docs/de/09-referenzen.md`](docs/de/09-referenzen.md). Dort steht jeder
verwendete Fremdcode mit Lizenz und Fundstelle:
[zj-58](https://github.com/klirichek/zj-58) (BSD-2-Clause, CUPS-Filter) und
[escpos-printer-db](https://github.com/receipt-print-hq/escpos-printer-db)
(CC BY 4.0, Druckermodell-Datenbank). BonBridge steht in keiner Verbindung zu
Seiko Epson oder zu OrderAssist.
